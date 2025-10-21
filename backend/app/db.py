from contextlib import contextmanager
from typing import Generator

from .models import SessionLocal, init_db


def initialize_database() -> None:
    init_db()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


