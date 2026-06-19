from __future__ import annotations

from pathlib import Path
from sqlmodel import SQLModel, Session, create_engine

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "toutiao.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    init_db()
    return Session(engine)
