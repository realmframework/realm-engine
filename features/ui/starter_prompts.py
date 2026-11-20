"""Natural starter ideas that never echo redaction placeholders or PDF page labels."""

import re

from core.contracts import KnowledgeChunk
from core.scope import NAVIGATION_TAG, is_navigation

REDACTION = re.compile(r"\[REDACTED_[^\]]*(?:\]|$)", re.IGNORECASE)
PAGE = re.compile(r"\bpage\s+\d+\b", re.IGNORECASE)
DEFAULT_IDEAS = (
    "Summarize the key points across my documents",
    "Extract key action items and important details",
    "What should I focus on next?",
)


def clean_label(text: str) -> str:
    return re.sub(r"\s+", " ", REDACTION.sub("", text)).strip(" _-—#\t\n")


def usable(text: str) -> bool:
    return bool(text.strip()) and "[redacted_" not in text.lower() and not PAGE.search(text)


def build_starter_prompts(chunks: list[KnowledgeChunk], topics: list[str]) -> list[str]:
    prompts: list[str] = []
    follow_ups: list[str] = []
    seen_guides: set[str] = set()
    seen_prompts: set[str] = set()
    for chunk in chunks:
        if is_navigation(chunk):
            continue
        if REDACTION.search(chunk.title) or "[redacted_" in chunk.title.lower():
            continue
        parts = chunk.title.split(" — ", 1)
        title = clean_label(parts[0])
        section = clean_label(re.sub(r"^\d+\.\s*", "", parts[1])) if len(parts) > 1 else "Overview"
        if not usable(title) or not usable(section):
            continue
        prompt = f"Summarize {title}" if section.lower() in {"overview", "body", "content"} else f"Explain {section} in {title}"
        if prompt in seen_prompts:
            continue
        seen_prompts.add(prompt)
        guide_id = chunk.doc_id or title
        if guide_id in seen_guides:
            if len(follow_ups) < 12:
                follow_ups.append(prompt)
            continue
        seen_guides.add(guide_id)
        prompts.append(prompt)
        if len(prompts) >= 12:
            return prompts
    prompts.extend(follow_ups[: 12 - len(prompts)])
    if len(prompts) < 3:
        topic_ideas: list[str] = []
        for topic in topics:
            if not usable(topic) or REDACTION.search(topic) or topic.casefold() == NAVIGATION_TAG:
                continue
            label = clean_label(topic).replace("-", " ").replace("_", " ")
            if usable(label):
                prompt = f"What are the main topics covered in {label}?"
                if prompt not in topic_ideas:
                    topic_ideas.append(prompt)
        fallback = [DEFAULT_IDEAS[0], *topic_ideas[:1], *DEFAULT_IDEAS[1:], *topic_ideas[1:]]
        prompts.extend(prompt for prompt in fallback if prompt not in prompts)
    return prompts[:12]
