import json

from src.web.api import _num, _date, _tick


def test_helpers_make_valid_json():
    assert _num(float("nan")) is None and _num(None) is None and _num("x") is None and _num(0.123456) == 0.1235
    assert _date(float("nan")) is None and _date("2026-11-24 00:00:00") == "2026-11-24"
    assert _tick("AAPL | APPL2") == "AAPL" and _tick(float("nan")) is None
    json.dumps({"a": _num(float("nan"))}, allow_nan=False)
