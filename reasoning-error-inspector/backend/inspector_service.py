from .probe_service import build_prefix
from .reasoning_service import generate_reasoning
from .errors import InspectorError


class InspectorService:
    def __init__(self, model, probe):
        self.model, self.probe = model, probe

    def analyze_request(self, question, context, inject_test_error=False, source_name=None):
        from .document_service import select_evidence
        from .evidence_service import analyze_against_evidence
        from .demo_service import inject_controlled_error

        selected, retrieval = select_evidence(question, context, self.model)
        reasoning = generate_reasoning(self.model, question, selected)
        hops = reasoning["hops"]
        controlled = None
        if inject_test_error:
            hops, controlled = inject_controlled_error(hops, selected)
        # Validate all complete prefixes before scoring any: do not silently drop later hops.
        for i in range(len(hops)):
            if self.model.token_count(build_prefix(question, selected, hops, i+1)) > self.model.token_limit:
                raise InspectorError("The generated chain exceeds the probe context limit. Use shorter evidence.", "context_too_long")
        probe_result = self.probe.analyze_hops_with_probe(self.model, question, selected, hops)
        most = probe_result["most_suspicious_hop"]
        evidence = analyze_against_evidence(self.model, hops[most-1], selected)
        if controlled:
            controlled["correct_localization"] = controlled["hop_index"] == most
        return dict(question=question, answer=reasoning["answer"], **probe_result,
                    evidence_analysis=evidence, controlled_error=controlled, reference_context=selected,
                    reference_source=source_name or "Pasted evidence", retrieval=retrieval,
                    answer_note="Answer generated before the controlled edit; it was not recomputed." if controlled else None,
                    warnings=self.model.warnings,
                    model=dict(name=self.probe.model_name, revision=self.probe.revision, layer=self.probe.layer,
                               device=self.model.device, artifact_sha256=self.probe.sha256))
