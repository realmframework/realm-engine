"""Graph hierarchy derived from indexed guides, including small-vault section detail."""

from pathlib import Path

from core.contracts import KnowledgeArea, KnowledgeChunk
from core.scope import resolve_chunk_url


def area_graph(
    area: KnowledgeArea,
    chunks: list[KnowledgeChunk],
    url_template: str = "",
) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    guides: dict[str, list[KnowledgeChunk]] = {}
    for chunk in chunks:
        guides.setdefault(chunk.doc_id or Path(chunk.file_path).stem, []).append(chunk)
    area_id = f"{area.name}:area"
    common = {"area": area.name, "area_color": area.color}
    nodes: list[dict[str, object]] = [{**common, "id": area_id, "label": area.name, "type": "area"}]
    links: list[dict[str, str]] = []
    tags = sorted({tag for sections in guides.values() for tag in sections[0].tags})
    for tag in tags:
        topic_id = f"{area.name}:topic:{tag}"
        nodes.append({**common, "id": topic_id, "label": tag, "type": "hub"})
        links.append({"source": area_id, "target": topic_id})
    for doc_id, sections in guides.items():
        chunk = sections[0]
        tagged = chunk.model_copy(update={"area": chunk.area or area.name, "doc_id": chunk.doc_id or doc_id})
        node_id = f"{area.name}:doc:{doc_id}"
        doc_url = resolve_chunk_url(tagged.model_copy(update={"title": tagged.title.split(" — ", 1)[0], "url": tagged.url.split("#", 1)[0]}), url_template)
        doc_node: dict[str, object] = {**common, "id": node_id, "doc_id": doc_id, "label": chunk.title.split(" — ", 1)[0], "type": "doc", "tags": chunk.tags}
        if doc_url:
            doc_node["url"] = doc_url
        nodes.append(doc_node)
        links.extend({"source": f"{area.name}:topic:{tag}", "target": node_id} for tag in chunk.tags)
        if not chunk.tags:
            links.append({"source": area_id, "target": node_id})
        if len(guides) <= 5:
            for index, section in enumerate(sections):
                section_id = f"{node_id}:section:{index}"
                label = section.title.split(" — ", 1)[-1]
                sec_tagged = section.model_copy(update={"area": section.area or area.name, "doc_id": section.doc_id or doc_id})
                sec_url = resolve_chunk_url(sec_tagged, url_template)
                sec_node: dict[str, object] = {**common, "id": section_id, "doc_id": doc_id, "section_index": index, "label": label, "type": "section"}
                if sec_url:
                    sec_node["url"] = sec_url
                nodes.append(sec_node)
                links.append({"source": node_id, "target": section_id})
    return nodes, links
