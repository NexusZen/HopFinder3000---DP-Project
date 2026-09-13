"""Load the user's trained classifier. No fitting occurs in this application."""
from pathlib import Path
import hashlib
import warnings

import joblib
import numpy as np
from sklearn.exceptions import InconsistentVersionWarning

from .errors import InspectorError


def build_prefix(question, context, hops, upto_hop):
    # Byte-for-byte template from the H1 notebook (prompt_version=1).
    if not 1 <= upto_hop <= len(hops):
        raise InspectorError("The hop prefix index is out of range.")
    text = f"Use the context to reason about the question.\n\nCONTEXT:\n{context}\n\nQUESTION:\n{question}\n"
    for i in range(upto_hop):
        text += f"\nHOP {i + 1}: {hops[i]}"
    return text


class ProbeService:
    def __init__(self, path: Path):
        if not path.is_file():
            raise InspectorError(f"Probe file missing: {path}. Place your trusted hop_error_probe.joblib in backend/models/.", "probe_missing", 503)
        # Administrator-provided artifact only. There is intentionally no joblib upload API.
        with warnings.catch_warnings():
            warnings.simplefilter("error", InconsistentVersionWarning)
            try:
                bundle = joblib.load(path)
            except Exception as exc:
                raise InspectorError(f"Cannot load the probe: {exc}. Install the artifact's scikit-learn version.", "probe_load_failed", 503) from exc
        if not isinstance(bundle, dict):
            raise InspectorError("The probe must be the notebook bundle, not a bare classifier.", "probe_metadata", 503)
        required = {"probe", "best_layer", "threshold", "feature_spec"}
        if not required.issubset(bundle):
            raise InspectorError(f"Probe bundle is missing: {', '.join(sorted(required-set(bundle)))}.", "probe_metadata", 503)
        self.bundle = bundle
        self.probe = bundle["probe"]
        self.spec = bundle["feature_spec"]
        self.layer = bundle["best_layer"]
        self.threshold = float(bundle["threshold"])
        if not isinstance(self.spec, dict) or self.spec.get("prompt_version") != 1 or self.spec.get("pooling") != "last_input_token":
            raise InspectorError("Unsupported training prompt or pooling configuration.", "probe_metadata", 503)
        if type(self.layer) is not int or self.layer < 1 or not np.isfinite(self.threshold) or not 0 <= self.threshold <= 1:
            raise InspectorError("Invalid saved layer or threshold.", "probe_metadata", 503)
        self.model_name = bundle.get("model_name") or self.spec.get("model")
        if not self.model_name or self.model_name != self.spec.get("model"):
            raise InspectorError("Conflicting/missing model identity in probe metadata.", "probe_metadata", 503)
        self.revision = self.spec.get("commit") or self.spec.get("revision")
        if not self.revision or not self.spec.get("model_config") or not self.spec.get("tokenizer_hash"):
            raise InspectorError("Bundle lacks model revision, configuration, or tokenizer identity.", "probe_metadata", 503)
        if not hasattr(self.probe, "predict_proba") or list(self.probe.classes_) != [0, 1]:
            raise InspectorError("Expected a fitted binary 0/1 probability classifier.", "probe_metadata", 503)
        self.width = int(self.probe.n_features_in_)
        if self.width != self.spec["model_config"].get("hidden_size"):
            raise InspectorError("Probe feature width differs from saved model hidden size.", "probe_metadata", 503)
        self.sha256 = hashlib.sha256(path.read_bytes()).hexdigest()

    def score(self, hidden):
        vector = np.asarray(hidden, dtype=np.float32)
        if vector.shape != (self.width,) or not np.isfinite(vector).all():
            raise InspectorError("Model returned an incompatible hidden-state vector.", "feature_mismatch", 503)
        score = float(self.probe.predict_proba(vector.reshape(1, -1))[0, 1])
        if not np.isfinite(score) or not 0 <= score <= 1:
            raise InspectorError("Probe returned an invalid score.", "invalid_score", 503)
        return score

    def analyze_hops_with_probe(self, model, question, context, hops):
        if not hops:
            raise InspectorError("There are no reasoning hops to analyze.")
        rows = []
        for i, hop in enumerate(hops):
            hidden = model.get_hop_hidden_state(build_prefix(question, context, hops, i+1), self.layer)
            score = self.score(hidden)
            rows.append(dict(index=i+1, text=hop, error_score=score, flagged=score >= self.threshold))
        first = next((r["index"] for r in rows if r["flagged"]), None)
        return dict(hops=rows, first_flagged_hop=first,
                    most_suspicious_hop=max(rows, key=lambda r: r["error_score"])["index"], threshold=self.threshold)
