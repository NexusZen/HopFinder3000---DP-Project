from io import BytesIO
from pathlib import Path
import re

import numpy as np
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer

from .errors import InspectorError

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_CONTEXT_CHARS = 250_000


def extract_document(name, content):
    if not content or len(content) > MAX_UPLOAD_BYTES:
        raise InspectorError("Upload a nonempty file smaller than 10 MB.", "invalid_document")
    suffix = Path(name or "").suffix.lower()
    if suffix == ".txt":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise InspectorError("The text file must use UTF-8 encoding.", "invalid_document") from exc
    elif suffix == ".pdf":
        try:
            reader = PdfReader(BytesIO(content))
            if reader.is_encrypted:
                raise InspectorError("Encrypted PDFs are not supported. Upload an unlocked copy.", "invalid_document")
            if len(reader.pages) > 150:
                raise InspectorError("Use a PDF with 150 pages or fewer.", "invalid_document")
            pages, count = [], 0
            for page in reader.pages:
                page_text = page.extract_text() or ""
                count += len(page_text)
                if count > MAX_CONTEXT_CHARS:
                    raise InspectorError("Extracted text exceeds 250,000 characters. Upload a smaller section.", "invalid_document")
                pages.append(page_text)
            text = "\n\n".join(pages)
        except InspectorError:
            raise
        except Exception as exc:
            raise InspectorError("Unable to read this PDF. Use a valid text-based PDF or paste the text.", "invalid_document") from exc
    else:
        raise InspectorError("Only .txt and .pdf files are supported.", "invalid_document")
    if not text.strip() or "\x00" in text:
        raise InspectorError("The document has no usable text. Scanned PDFs need OCR before upload.", "empty_document")
    if len(text) > MAX_CONTEXT_CHARS:
        raise InspectorError("Document text exceeds 250,000 characters. Upload a smaller section.", "invalid_document")
    return text.strip()


def split_chunks(text, words_per_chunk=100):
    # Source character offsets make retrieval selections inspectable. No fabricated summaries.
    matches = list(re.finditer(r"\S+", text))
    return [dict(start=matches[i].start(), end=matches[min(i+words_per_chunk, len(matches))-1].end(),
                 text=text[matches[i].start():matches[min(i+words_per_chunk, len(matches))-1].end()])
            for i in range(0, len(matches), words_per_chunk)]


def select_evidence(question, context, model):
    budget = model.token_limit - model.token_count(question) - 950
    if budget < 128:
        raise InspectorError("The question leaves too little room for evidence. Shorten the question.", "context_too_long")
    count = model.token_count(context)
    if count <= budget:
        return context, dict(used=False, original_tokens=count, selected_tokens=count,
                             chunks=[dict(start=0, end=len(context))])
    chunks = split_chunks(context)
    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        features = vectorizer.fit_transform([c["text"] for c in chunks])
        relevance = (features @ vectorizer.transform([question]).T).toarray().ravel()
    except ValueError as exc:
        raise InspectorError("No usable terms were found for evidence retrieval. Paste a shorter relevant passage.", "retrieval_failed") from exc
    picked = []
    for i in np.argsort(-relevance, kind="stable"):
        if relevance[i] <= 0:
            continue
        candidate = sorted(picked + [int(i)])
        combined = "\n\n".join(chunks[j]["text"] for j in candidate)
        if model.token_count(combined) <= budget:
            picked = candidate
    if not picked:
        raise InspectorError("No relevant excerpt fits the context window. Paste a shorter passage focused on the question.", "retrieval_failed")
    selected = "\n\n".join(chunks[i]["text"] for i in picked)
    return selected, dict(used=True, original_tokens=count, selected_tokens=model.token_count(selected),
                         chunks=[dict(start=chunks[i]["start"], end=chunks[i]["end"]) for i in picked])
