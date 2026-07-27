import sqlite3
from pathlib import Path

import pytest
import streamlit as st

from tests.fixtures.sample_data import seed_sample_data

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"


@pytest.fixture
def seeded_db_path(tmp_path):
    """
    File-backed (not :memory:) sqlite DB seeded with the sample dataset.
    data_service opens a fresh connection per call, and separate :memory:
    connections don't share state, so tests need a real file every one of
    those connections can see.
    """
    db_path = tmp_path / "dashboard_test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    seed_sample_data(conn)
    conn.close()
    return db_path


@pytest.fixture(autouse=True)
def _data_service_isolation(seeded_db_path, monkeypatch):
    """Point data_service at the seeded test DB and reset its st.cache_data cache per test."""
    monkeypatch.setattr(
        "src.dashboard.data_service.get_connection",
        lambda: sqlite3.connect(seeded_db_path),
    )
    st.cache_data.clear()
    yield
    st.cache_data.clear()
