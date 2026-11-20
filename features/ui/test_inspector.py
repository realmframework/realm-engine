"""Read-only redaction reports and area-specific graph metadata."""

from pathlib import Path

from fastapi.testclient import TestClient


def test_anonymize_preview_is_read_only(area_client: TestClient, tmp_path: Path) -> None:
    before = {p: p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    response = area_client.post('/api/anonymize/preview', json={'text': 'Contact Alice at alice@example.org', 'filename': 'CV_Alice.md'})
    assert response.status_code == 200 and response.headers['cache-control'] == 'no-store'
    assert response.json()['counts_by_type']['EMAIL'] == 1 and response.json()['counts_by_type']['NAME'] == 1
    assert len(response.json()['samples']) == 2 and 'alice@example.org' not in str(response.json()['samples'])
    upload = area_client.post('/api/anonymize/preview', files={'file': ('notes.txt', b'Contact learner@example.org', 'text/plain')})
    assert upload.status_code == 200 and upload.json()['total_redacted'] == 1
    assert {p: p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()} == before
    assert area_client.post('/api/anonymize/preview', json={'text': 42}).status_code == 422
    assert area_client.post('/api/anonymize/preview', files={'file': ('bad.exe', b'bad')}).status_code == 400


def test_graph_tags_distinct_area_nodes_and_links(area_client: TestClient) -> None:
    assert area_client.post('/api/workspace', json={'knowledge_dir': 'kitchen_recipes'}).status_code == 200
    assert area_client.post('/api/upload', json={'filename': 'shared.md', 'content': '# Shared Guide\nTags: base\n\n## Recipe\nKitchen universe marker.'}).status_code == 200
    response = area_client.get('/api/graph')
    assert response.status_code == 200
    graph = response.json()
    nodes = {n['id']: n for n in graph['nodes']}
    assert {"area", "hub", "doc", "section"} <= {n["type"] for n in nodes.values()}
    assert len({n['area_color'] for n in nodes.values()}) == 2
    assert {n['area'] for n in nodes.values()} == {'knowledge_base', 'kitchen_recipes'}
    assert all(nodes[e['source']]['area'] == nodes[e['target']]['area'] for e in graph['links'])
    active = area_client.get('/api/graph?all_areas=false').json()['nodes']
    assert active and all(n['area'] == 'kitchen_recipes' for n in active)
