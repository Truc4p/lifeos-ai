from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StrengthWeakness:
    name: str
    description: str


@dataclass
class PersonalityType:
    type_code: str
    nickname: str
    role: str
    definition: str
    description_paragraphs: list[str]
    key_quotes: list[str]
    section_headings: list[str]
    strengths: list[StrengthWeakness]
    weaknesses: list[StrengthWeakness]
    source_url: str
    scraped_at: Optional[str] = None
