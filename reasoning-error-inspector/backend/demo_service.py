import re

from .errors import InspectorError


def inject_controlled_error(hops, context):
    """One transparent numeric edit to a source-matching hop, never used in Analyze mode."""
    normalized_context = " ".join(context.split())
    for i, hop in enumerate(hops):
        if " ".join(hop.split()) not in normalized_context:
            continue
        for match in re.finditer(r"(?<![\w,./–-])\d{1,4}(?![\w,]|[./]\d)", hop):
            original = match.group()
            if original.startswith("0") or len(re.findall(r"(?<!\w)"+re.escape(original)+r"(?!\w)", hop)) != 1:
                continue
            replacement = str(int(original)+3)
            if replacement in hop:
                continue
            modified = hop[:match.start()] + replacement + hop[match.end():]
            if modified in context:
                continue
            result = hops.copy()
            result[i] = modified
            return result, dict(hop_index=i+1, original=hop, corrupted=modified,
                original_value=original, replacement_value=replacement, changed_value=f"{original} → {replacement}",
                note="Controlled numeric edit to a source-matching sentence. The edit is known; factual falsehood is not independently certified.")
    raise InspectorError("No safe controlled numeric edit was available in the generated, source-matching hops. Try evidence with a clear year or quantity, or turn off the test-error toggle.", "injection_unavailable")
