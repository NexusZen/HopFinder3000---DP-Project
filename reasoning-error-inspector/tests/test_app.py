import json
import time
from io import BytesIO
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from backend.errors import InspectorError
from backend.probe_service import ProbeService, build_prefix
from backend.model_service import verify_model_configuration
from backend.reasoning_service import generate_reasoning, validate_reasoning_output
from backend.evidence_service import analyze_against_evidence
from backend.demo_service import inject_controlled_error
from backend.document_service import extract_document, select_evidence
from backend.inspector_service import InspectorService
from backend.main import create_app

CONTEXT = 'Mira taught at North University. North University was founded in 1902 by Ada Vale.'
HOPS = ['Mira taught at North University.', 'North University was founded in 1902 by Ada Vale.']


@pytest.fixture
def probe():
    return ProbeService(Path(__file__).resolve().parents[1] / 'backend/models/hop_error_probe.joblib')


class TestModel:
    __test__ = False
    token_limit = 2048
    warnings = ['Test model: synthetic vectors, not real Qwen inference.']
    device = 'test'

    def __init__(self):
        self.prefixes = []
        self.calls = []

    def token_count(self, text):
        return len(text.split())

    def generate_text(self, instruction, payload, correction=False, json_prefix="{"):
        self.calls.append((instruction, payload, correction))
        return json.dumps(dict(hops=HOPS, answer='Ada Vale'))

    def get_hop_hidden_state(self, prefix, layer):
        self.prefixes.append(prefix)
        return np.zeros(896, dtype=np.float32)


def test_real_artifact_and_prefix(probe):
    assert probe.layer == 13 and probe.threshold == .27 and probe.width == 896
    assert 0 <= probe.score(np.zeros(896)) <= 1
    first = build_prefix('Who?', CONTEXT, HOPS, 1)
    assert first == f'Use the context to reason about the question.\n\nCONTEXT:\n{CONTEXT}\n\nQUESTION:\nWho?\n\nHOP 1: {HOPS[0]}'
    assert '\nHOP 2:' not in first
    with pytest.raises(InspectorError):
        probe.score(np.zeros(100))


def test_mismatch_rejected(probe):
    saved = probe.spec['model_config']
    with pytest.raises(InspectorError, match='mismatch'):
        verify_model_configuration(saved, {**saved, 'hidden_size': 10}, probe.width, probe.layer)


def test_highest_score_is_not_necessarily_flagged(probe):
    scores = iter([.10, .20])
    probe.score = lambda hidden: next(scores)
    result = probe.analyze_hops_with_probe(TestModel(), 'Who?', CONTEXT, HOPS)
    assert result['first_flagged_hop'] is None
    assert result['most_suspicious_hop'] == 2
    scores = iter([.30, .90])
    result = probe.analyze_hops_with_probe(TestModel(), 'Who?', CONTEXT, HOPS)
    assert result['first_flagged_hop'] == 1 and result['most_suspicious_hop'] == 2


@pytest.mark.parametrize('hops', [HOPS[:1], HOPS * 2, ['Find the university.', HOPS[1]], ['x', HOPS[1]]])
def test_invalid_reasoning(hops):
    with pytest.raises(InspectorError):
        validate_reasoning_output(dict(hops=hops, answer='Ada'))


def test_generation_retry():
    model = TestModel()
    replies = iter(['not JSON', json.dumps(dict(hops=HOPS, answer='Ada'))])
    model.generate_text = lambda *args, **kwargs: next(replies)
    assert generate_reasoning(model, 'Who?', CONTEXT)['hops'] == HOPS
    model.generate_text = lambda *args, **kwargs: 'invalid'
    with pytest.raises(InspectorError, match='two attempts'):
        generate_reasoning(model, 'Who?', CONTEXT)


def test_demo_is_single_edit_and_does_not_mutate():
    updated, edit = inject_controlled_error(HOPS, CONTEXT)
    assert HOPS[1].endswith('1902 by Ada Vale.')
    assert sum(a != b for a, b in zip(HOPS, updated)) == 1
    assert edit['hop_index'] == 2
    assert '1905' in updated[1]
    with pytest.raises(InspectorError):
        inject_controlled_error(HOPS[:1], CONTEXT)


def test_evidence_quotes_must_exist():
    model = TestModel()
    assert analyze_against_evidence(model, HOPS[0], CONTEXT)['status'] == 'SUPPORTED'
    model.generate_text = lambda *a, **k: json.dumps(dict(status='CONTRADICTED', evidence='Fabricated quote 1902.', claimed_value='1905', supported_value='1902', explanation='Wrong date.'))
    assert analyze_against_evidence(model, 'Founded in 1905.', CONTEXT)['status'] == 'NOT_ENOUGH_INFORMATION'


def test_numeric_comparison_uses_only_evidence():
    from backend.evidence_service import compare_numeric_fact
    result = compare_numeric_fact(HOPS[1].replace('1902', '1905'), CONTEXT)
    assert result['supported_value'] == '1902' and result['claimed_value'] == '1905'
    assert result['evidence'] == HOPS[1]
    assert compare_numeric_fact('Something else was founded in 1905.', CONTEXT) is None
    assert compare_numeric_fact(HOPS[1].replace('1902', '1905'), CONTEXT + ' North University was founded in 1903 by Ada Vale.') is None


def test_retrieval_and_bad_documents():
    model = TestModel()
    model.token_limit = 1200
    source = ('Ocean waves currents seawater. ' * 100) + ('North University founded Ada Vale. ' * 100)
    selected, metadata = select_evidence('Who founded North University?', source, model)
    assert metadata['used'] and model.token_count(selected) <= 244
    assert 'North University' in selected
    assert all(source[c['start']:c['end']] in selected for c in metadata['chunks'])
    assert extract_document('test.txt', b'hello') == 'hello'
    for name, data in [('bad.pdf', b'not pdf'), ('bad.exe', b'data'), ('empty.txt', b' '), ('bad.txt', b'\xff')]:
        with pytest.raises(InspectorError):
            extract_document(name, data)


def test_api_pipeline_and_pdf(probe):
    model = TestModel()
    service = InspectorService(model, probe)
    with TestClient(create_app(lambda: service)) as client:
        for _ in range(100):
            if client.get('/api/health').json()['status'] == 'ready':
                break
            time.sleep(.01)
        assert client.get('/').status_code == 200
        assert client.post('/api/analyze', json=dict(question=' ', context=CONTEXT)).status_code == 422
        result = client.post('/api/analyze', json=dict(question='Who founded the university where Mira taught?', context=CONTEXT))
        assert result.status_code == 200, result.text
        data = result.json()
        assert len(data['hops']) == 2 and data['controlled_error'] is None
        assert len(model.prefixes) == 2 and '\nHOP 2:' not in model.prefixes[0]
        pdf = client.get(f"/api/reports/{data['report_id']}.pdf")
        assert pdf.status_code == 200
        text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(pdf.content)).pages)
        assert 'Ada Vale' in text and 'not calibrated probabilities' in text
        output = Path('output/pdf'); output.mkdir(parents=True, exist_ok=True)
        (output / 'test-diagnostic.pdf').write_bytes(pdf.content)
        assert client.post('/api/documents', files={'file': ('sample.txt', b'New evidence', 'text/plain')}).json()['text'] == 'New evidence'
        assert client.post('/api/documents', files={'file': ('sample.pdf', pdf.content, 'application/pdf')}).status_code == 200
        demo = client.post('/api/analyze', json=dict(question='Who founded the university?', context=CONTEXT, inject_test_error=True))
        assert demo.status_code == 200 and demo.json()['controlled_error']['hop_index'] == 2
        manual = client.post('/api/score', json=dict(question='Who?', context=CONTEXT, hops=HOPS))
        assert manual.status_code == 200 and len(manual.json()['hops']) == 2


def test_startup_failure_readable():
    def fail():
        raise InspectorError('Probe file missing', 'probe_missing', 503)
    with TestClient(create_app(fail)) as client:
        for _ in range(100):
            if client.get('/api/health').json()['status'] == 'error':
                break
            time.sleep(.01)
        response = client.post('/api/analyze', json=dict(question='Who?', context=CONTEXT))
        assert response.status_code == 503
        assert 'missing' in response.json()['detail']['message']
