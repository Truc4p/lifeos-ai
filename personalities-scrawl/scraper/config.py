PERSONALITY_TYPES = [
    "intj", "intp", "entj", "entp",
    "infj", "infp", "enfj", "enfp",
    "istj", "isfj", "estj", "esfj",
    "istp", "isfp", "estp", "esfp",
]

ROLE_MAP = {
    "INTJ": "analyst", "INTP": "analyst", "ENTJ": "analyst", "ENTP": "analyst",
    "INFJ": "diplomat", "INFP": "diplomat", "ENFJ": "diplomat", "ENFP": "diplomat",
    "ISTJ": "sentinel", "ISFJ": "sentinel", "ESTJ": "sentinel", "ESFJ": "sentinel",
    "ISTP": "explorer", "ISFP": "explorer", "ESTP": "explorer", "ESFP": "explorer",
}

BASE_URL = "https://www.16personalities.com"


def intro_url(type_code: str) -> str:
    return f"{BASE_URL}/{type_code}-personality"


def strengths_url(type_code: str) -> str:
    return f"{BASE_URL}/{type_code}-strengths-and-weaknesses"


MIN_DELAY = 4.0
MAX_DELAY = 8.0

PAGE_LOAD_TIMEOUT = 30_000
POST_LOAD_SLEEP = 3.0

OUTPUT_FILE = "personalities.json"
