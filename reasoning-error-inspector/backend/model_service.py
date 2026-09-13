"""One frozen checkpoint for generation, evidence checking, and prefix activations."""
import hashlib
import importlib.metadata
import json

from .errors import InspectorError


def canonical_rope(config):
    value = config.get("rope_parameters") or config.get("rope_scaling") or {}
    return {"rope_type": value.get("rope_type", value.get("type", "default")),
            "rope_theta": value.get("rope_theta", config.get("rope_theta", 10000.0)),
            **{k: v for k, v in value.items() if k not in {"type", "rope_type", "rope_theta"}}}


def verify_model_configuration(saved, loaded, width, layer):
    fields = ["model_type", "hidden_size", "intermediate_size", "num_hidden_layers", "num_attention_heads",
              "num_key_value_heads", "vocab_size", "hidden_act", "max_position_embeddings", "rms_norm_eps",
              "tie_word_embeddings", "use_sliding_window", "sliding_window", "max_window_layers", "layer_types"]
    differences = [name for name in fields if name in saved and saved[name] != loaded.get(name)]
    if canonical_rope(saved) != canonical_rope(loaded):
        differences.append("rotary-position configuration")
    if width != loaded.get("hidden_size") or not 1 <= layer <= loaded.get("num_hidden_layers", 0):
        differences.append("probe dimension/layer")
    if differences:
        raise InspectorError("Model/probe configuration mismatch: " + ", ".join(differences), "model_mismatch", 503)


class ModelService:
    def __init__(self, probe):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.warnings = []
        trained_transformers = probe.spec.get("versions", {}).get("transformers")
        if trained_transformers and importlib.metadata.version("transformers") != trained_transformers:
            raise InspectorError(f"This artifact used transformers=={trained_transformers}. Install that version before inference.", "runtime_mismatch", 503)
        self.tokenizer = AutoTokenizer.from_pretrained(probe.model_name, revision=probe.revision, trust_remote_code=False)
        token_hash = hashlib.sha256(self.tokenizer.backend_tokenizer.to_str().encode()).hexdigest()
        if token_hash != probe.spec["tokenizer_hash"]:
            raise InspectorError("Tokenizer fingerprint differs from training. Use the saved tokenizer/revision and Transformers version.", "tokenizer_mismatch", 503)
        trained_dtype = probe.spec.get("dtype", "torch.float32")
        dtype = {"torch.float16": torch.float16, "torch.bfloat16": torch.bfloat16,
                 "torch.float32": torch.float32}.get(trained_dtype)
        if dtype is None:
            raise InspectorError("Unsupported saved model precision.", "model_mismatch", 503)
        if self.device == "cpu":
            dtype = torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(probe.model_name, revision=probe.revision,
            dtype=dtype, trust_remote_code=False).to(self.device).eval()
        self.model.requires_grad_(False)
        if self.model.config.model_type != "qwen2" or self.model.config.is_encoder_decoder:
            raise InspectorError("This MVP expects the saved decoder-only Qwen2 checkpoint.", "model_mismatch", 503)
        verify_model_configuration(probe.spec["model_config"], self.model.config.to_dict(), probe.width, probe.layer)
        commit = getattr(self.model.config, "_commit_hash", None)
        if probe.spec.get("commit") and commit != probe.spec["commit"]:
            raise InspectorError("Loaded model commit differs from training.", "model_mismatch", 503)
        self.token_limit = min(int(probe.spec.get("token_limit", 2048)), self.model.config.max_position_embeddings)
        self.max_new_tokens = 384
        self.seed = int(probe.bundle.get("seed", 42))
        self.name, self.revision = probe.model_name, probe.revision
        # Base checkpoints may ship a chat template without being instruction-tuned.
        self.use_chat = bool(self.tokenizer.chat_template) and "instruct" in self.name.lower()

    def token_count(self, text):
        return len(self.tokenizer(text, truncation=False)["input_ids"])

    def render_prompt(self, instruction, payload):
        if self.use_chat:
            return self.tokenizer.apply_chat_template([
                {"role": "system", "content": instruction}, {"role": "user", "content": payload}],
                tokenize=False, add_generation_prompt=True)
        return instruction + "\n\n" + payload + "\n\nJSON:\n"

    def generate_text(self, instruction, payload, correction=False, json_prefix="{"):
        if correction:
            instruction += "\nYour previous attempt did not satisfy the format. Output one JSON object only, with the exact keys requested."
        # Prefill only JSON syntax/key names, never factual hop content.
        prompt = self.render_prompt(instruction, payload) + json_prefix
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=False,
                                add_special_tokens=not self.use_chat)
        if inputs["input_ids"].shape[1] + self.max_new_tokens > self.token_limit:
            raise InspectorError("The evidence plus generation instructions exceeds the model budget. Use a shorter question or context.", "context_too_long")
        torch = self.torch
        from transformers import StoppingCriteria, StoppingCriteriaList
        tokenizer = self.tokenizer
        input_length = inputs["input_ids"].shape[1]

        class CompleteJSONObject(StoppingCriteria):
            def __call__(self, input_ids, scores, **kwargs):
                text = json_prefix + tokenizer.decode(input_ids[0, input_length:], skip_special_tokens=True)
                try:
                    value, end = json.JSONDecoder().raw_decode(text.lstrip())
                    return isinstance(value, dict)
                except ValueError:
                    return False

        with torch.inference_mode():
            output = self.model.generate(**{k: v.to(self.device) for k, v in inputs.items()},
                max_new_tokens=self.max_new_tokens, do_sample=False, use_cache=True,
                stopping_criteria=StoppingCriteriaList([CompleteJSONObject()]),
                pad_token_id=self.tokenizer.eos_token_id)
        tail = output[0, inputs["input_ids"].shape[1]:]
        # A token may include a closing brace plus whitespace; parsing remains strict.
        return json_prefix + self.tokenizer.decode(tail, skip_special_tokens=True)

    def get_hop_hidden_state(self, prefix, layer):
        inputs = self.tokenizer(prefix, return_tensors="pt", truncation=False)
        if inputs["input_ids"].shape[1] > self.token_limit:
            raise InspectorError("A complete hop prefix exceeds the saved token limit. Evidence was not silently truncated.", "context_too_long")
        with self.torch.inference_mode():
            # The vocabulary head is unnecessary for probing. This is the SAME loaded model's base.
            outputs = self.model.base_model(**{k: v.to(self.device) for k, v in inputs.items()},
                output_hidden_states=True, use_cache=False, return_dict=True)
        return outputs.hidden_states[layer][0, -1, :].float().cpu().numpy().copy()
