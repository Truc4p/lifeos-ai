import re
import logging
from bs4 import BeautifulSoup, Tag
from .models import StrengthWeakness
from .config import ROLE_MAP

logger = logging.getLogger(__name__)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def _text(tag: Tag) -> str:
    """Extract clean text, collapsing whitespace and removing spaces before punctuation."""
    raw = " ".join(tag.get_text(separator=" ").split())
    return re.sub(r"\s+([,.:;!?'’])", r"\1", raw)


def parse_intro_page(html: str, type_code: str, url: str) -> dict:
    """Extract personality data from the {type}-personality page."""
    soup = _soup(html)

    # Nickname: .type-info__title span
    title_div = soup.find(class_="type-info__title")
    span = title_div.find("span") if title_div else None
    nickname = _text(span) if span else ""

    # Fallback: extract from definition text "TYPE (Nickname)is a..."
    if not nickname:
        for p in soup.find_all("p"):
            m = re.search(r"\([^)]+\)", p.get_text())
            if m and type_code.upper() in p.get_text():
                nickname = m.group(0).strip("()")
                break

    # Role: hardcoded mapping (not available as a CSS class in rendered HTML)
    role = ROLE_MAP.get(type_code.upper(), "unknown")

    # Definition: the paragraph inside .definition that names the type
    definition_div = soup.find(class_="definition")
    definition = ""
    if definition_div:
        for p in definition_div.find_all("p"):
            text = _text(p)
            if type_code.upper() in text and "personality type" in text.lower():
                definition = text
                break

    # The page is server-side rendered and may appear twice in the DOM.
    # Use only the first article to avoid duplicates.
    article: Tag = soup.find("article", class_="description")

    # Description paragraphs: inside div.description__content
    # Real structure: article > div.description__content > div (section) > div (paragraph)
    desc_paragraphs = []
    content_div = article.find(class_="description__content") if article else None
    if content_div:
        for section in content_div.children:
            if not isinstance(section, Tag):
                continue
            for elem in section.children:
                if not isinstance(elem, Tag):
                    continue
                if elem.name == "h2":
                    continue
                if "description-pullout" in elem.get("class", []):
                    continue
                text = _text(elem)
                if text:
                    desc_paragraphs.append(text)

    # Key quotes: scoped to first article only to avoid SSR duplicates
    pullouts = []
    if article:
        seen = set()
        for d in article.find_all(class_="description-pullout"):
            text = _text(d)
            if text and text not in seen:
                seen.add(text)
                pullouts.append(text)

    # Section headings: h2 tags inside the article
    section_headings = []
    if article:
        seen_h = set()
        for h2 in article.find_all("h2"):
            text = _text(h2)
            if text and text not in seen_h:
                seen_h.add(text)
                section_headings.append(text)

    return {
        "type_code": type_code.upper(),
        "nickname": nickname,
        "role": role,
        "definition": definition,
        "description_paragraphs": [p for p in desc_paragraphs if p],
        "key_quotes": pullouts,
        "section_headings": section_headings,
        "source_url": url,
    }


def _parse_sw_list(ul_tag: Tag) -> list[StrengthWeakness]:
    results = []
    if not ul_tag:
        return results
    for li in ul_tag.find_all("li", recursive=False):
        full_text = _text(li)
        strong = li.find("strong") or li.find("b")
        if strong:
            name = _text(strong)
        else:
            match = re.match(r"^([^–—\-]+)[–—\-]", full_text)
            name = match.group(1).strip() if match else full_text[:30]
        results.append(StrengthWeakness(name=name, description=full_text))
    return results


def parse_strengths_page(html: str, type_code: str) -> dict:
    """Extract strengths and weaknesses from the {type}-strengths-and-weaknesses page."""
    soup = _soup(html)
    article: Tag = soup.find("article", class_="description")

    strengths, weaknesses = [], []
    if article:
        for h2 in article.find_all("h2"):
            text = h2.get_text(strip=True)
            ul = h2.find_next_sibling("ul")
            if not ul:
                scene = h2.find_next_sibling("div", class_="scene")
                if scene:
                    ul = scene.find_next_sibling("ul")
            # Also try: next sibling of type ul anywhere nearby
            if not ul:
                ul = h2.find_next("ul")
            if "Strengths" in text and not strengths:
                strengths = _parse_sw_list(ul)
            elif "Weaknesses" in text and not weaknesses:
                weaknesses = _parse_sw_list(ul)

    return {"strengths": strengths, "weaknesses": weaknesses}
