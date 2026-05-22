import re
from pathlib import Path
from langchain_core.documents import Document
from .config import RESEARCH_DIR, TOPIC_MAP


def filename_to_topic(path: Path) -> str:
    return TOPIC_MAP.get(path.stem, path.stem)


def split_into_sections(text: str) -> list[str]:
    """Split markdown text into sections, each starting at a **Bold Header** line."""
    sections: list[str] = []
    current: list[str] = []
    for line in text.splitlines(keepends=True):
        if re.match(r'^\*\*[^*]+\*\*', line) and current:
            sections.append("".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("".join(current))
    return [s for s in sections if s.strip()]


def load_and_chunk(research_dir: Path = RESEARCH_DIR) -> list[Document]:
    docs: list[Document] = []
    for md_file in sorted(research_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        topic = filename_to_topic(md_file)
        for i, section in enumerate(split_into_sections(text)):
            docs.append(Document(
                page_content=section,
                metadata={
                    "source_file": md_file.name,
                    "topic": topic,
                    "section_index": i,
                },
            ))
    return docs
