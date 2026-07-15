import pytest

from src.config import _get_float_env, _get_int_env


def test_get_int_env_returns_default_when_unset(monkeypatch):
    monkeypatch.delenv("SOME_TEST_VAR", raising=False)
    assert _get_int_env("SOME_TEST_VAR", 42) == 42


def test_get_int_env_parses_valid_value(monkeypatch):
    monkeypatch.setenv("SOME_TEST_VAR", "7")
    assert _get_int_env("SOME_TEST_VAR", 42) == 7


def test_get_int_env_raises_for_invalid_value(monkeypatch):
    monkeypatch.setenv("SOME_TEST_VAR", "not-a-number")
    with pytest.raises(ValueError, match="must be an integer"):
        _get_int_env("SOME_TEST_VAR", 42)


def test_get_float_env_returns_default_when_unset(monkeypatch):
    monkeypatch.delenv("SOME_TEST_VAR", raising=False)
    assert _get_float_env("SOME_TEST_VAR", 1.5) == 1.5


def test_get_float_env_parses_valid_value(monkeypatch):
    monkeypatch.setenv("SOME_TEST_VAR", "2.5")
    assert _get_float_env("SOME_TEST_VAR", 1.5) == 2.5


def test_get_float_env_raises_for_invalid_value(monkeypatch):
    monkeypatch.setenv("SOME_TEST_VAR", "not-a-number")
    with pytest.raises(ValueError, match="must be a number"):
        _get_float_env("SOME_TEST_VAR", 1.5)
