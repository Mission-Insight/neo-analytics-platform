from src.parsing.utils import safe_float


def test_safe_float_converts_numeric_string():
    assert safe_float("12.34") == 12.34


def test_safe_float_converts_int_string():
    assert safe_float("100") == 100.0


def test_safe_float_handles_none():
    assert safe_float(None) is None


def test_safe_float_handles_empty_string():
    assert safe_float("") is None
