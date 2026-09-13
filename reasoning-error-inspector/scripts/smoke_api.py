"""Opt-in live Qwen smoke test. Start the server first; no mock scores are used."""
import json
from pathlib import Path
import httpx

payload = {
    'question': 'Who founded the university where Mira taught?',
    'context': 'Mira taught at North University. North University was founded in 1902 by Ada Vale.',
}
output = Path('output/live'); output.mkdir(parents=True, exist_ok=True)
with httpx.Client(base_url='http://127.0.0.1:8000', timeout=600) as client:
    health = client.get('/api/health').json()
    assert health['status'] == 'ready', health
    manual = client.post('/api/score', json={**payload, 'hops': [
        'Mira taught at North University.', 'North University was founded in 1905 by Ada Vale.']})
    manual.raise_for_status()
    (output / 'manual.json').write_text(json.dumps(manual.json(), indent=2), encoding='utf-8')
    print('Manual scoring:', manual.json(), flush=True)
    for demo in (False, True):
        response = client.post('/api/analyze', json={**payload, 'inject_test_error': demo})
        print('Demo:', demo, 'Status:', response.status_code, json.dumps(response.json(), ensure_ascii=True), flush=True)
        response.raise_for_status()
        data = response.json()
        assert len(data['hops']) >= 2
        assert all(0 <= row['error_score'] <= 1 for row in data['hops'])
        tag = 'demo' if demo else 'analyze'
        (output / f'{tag}.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
        pdf = client.get(f"/api/reports/{data['report_id']}.pdf")
        pdf.raise_for_status()
        (output / f'{tag}.pdf').write_bytes(pdf.content)
