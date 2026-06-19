import json
from pathlib import Path
from datetime import datetime


ROOT_DIRS = [
    "data/samples",
    "data/style_profiles",
    "data/outputs",
    "data/covers",
]


def ensure_dirs():
    for d in ROOT_DIRS:
        Path(d).mkdir(parents=True, exist_ok=True)


def now_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_text(path: str, text: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8")


def read_json(path: str):
    return json.loads(read_text(path))


def write_json(path: str, data):
    write_text(
        path,
        json.dumps(data, ensure_ascii=False, indent=2),
    )