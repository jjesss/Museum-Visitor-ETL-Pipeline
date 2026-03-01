from datetime import datetime, timedelta, timezone
import sys
import os
import pytest
from typing import Any, Dict

from etl import parse_JSON, get_button_id
from validations import validate_at, validate_site, validate_val, validate_data


def test_parse_JSON_valid_string_returns_dict() -> None:
    """parse_JSON should parse a valid JSON string into a dict."""
    json_str = '{"at":"2026-02-24T17:27:01.008973+00:00","site":"1","val":3}'
    expected = {"at": "2026-02-24T17:27:01.008973+00:00",
                "site": "1", "val": 3}
    assert parse_JSON(json_str) == expected


def test_parse_JSON_accepts_dict_and_returns_same_object() -> None:
    """If input is already a dict, parse_JSON should return it unchanged."""
    d = {"k": 1}
    assert parse_JSON(d) is d


def test_parse_JSON_invalid_raises_ValueError() -> None:
    """parse_JSON should raise ValueError for malformed JSON."""
    with pytest.raises(ValueError):
        parse_JSON('{"incomplete":')


# run test on multiple valid val/type combinations to ensure correct button_id mapping
@pytest.mark.parametrize("payload, expected", [
    ({"val": -1, "type": 0}, 0),
    ({"val": -1, "type": 1}, 1),
    ({"val": 0, "type": None}, 2),
    ({"val": 1, "type": None}, 3),
    ({"val": 4, "type": None}, 6),
])
def test_get_button_id_valid_mappings(payload: Dict[str, Any], expected: int) -> None:
    """get_button_id should return correct mapping for valid val/type combos."""
    assert get_button_id(payload) == expected


def test_get_button_id_invalid_combination_raises_ValueError() -> None:
    """Invalid val/type pairs must raise ValueError."""
    with pytest.raises(ValueError):
        get_button_id({"val": 999, "type": None})


def test_get_button_id_missing_keys_raises_KeyError() -> None:
    """Missing required keys should raise KeyError."""
    with pytest.raises(KeyError):
        get_button_id({"type": None})


# ===== Validation function tests =====
def test_validate_at_valid_past_returns_true() -> None:
    """Arrange/Act/Assert: a recent past ISO timestamp is valid."""
    ts = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    assert validate_at(ts) is True


def test_validate_at_future_raises_ValueError() -> None:
    """Future timestamps must raise ValueError."""
    future_ts = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    with pytest.raises(ValueError):
        validate_at(future_ts)


def test_validate_at_invalid_format_raises_ValueError() -> None:
    """Malformed timestamp strings must raise ValueError."""
    with pytest.raises(ValueError):
        validate_at("not-a-timestamp")


@pytest.mark.parametrize("site", ["0", "3", 5])
def test_validate_site_valid_inputs_return_true(site: int | str) -> None:
    """Valid site values (strings or ints in 0..5) return True."""
    assert validate_site(site) is True


def test_validate_site_empty_raises_ValueError() -> None:
    """Empty site values must raise ValueError."""
    with pytest.raises(ValueError):
        validate_site("")


def test_validate_site_non_integer_raises_ValueError() -> None:
    """Non-integer site values must raise ValueError."""
    with pytest.raises(ValueError):
        validate_site("A")


def test_validate_site_out_of_range_raises_ValueError() -> None:
    """Site values outside 0..5 must raise ValueError."""
    with pytest.raises(ValueError):
        validate_site("9")


@pytest.mark.parametrize("val", [-1, 0, 4, "2"])
def test_validate_val_valid_inputs_return_true(val: int | str) -> None:
    """Valid val inputs (ints or numeric strings within -1..4) return True."""
    assert validate_val(val) is True


def test_validate_val_empty_raises_ValueError() -> None:
    """Empty val must raise ValueError."""
    with pytest.raises(ValueError):
        validate_val("")


def test_validate_val_non_integer_raises_ValueError() -> None:
    """Non-numeric val must raise ValueError."""
    with pytest.raises(ValueError):
        validate_val("x")


def test_validate_val_out_of_range_raises_ValueError() -> None:
    """Vals outside -1..4 must raise ValueError."""
    with pytest.raises(ValueError):
        validate_val("-99")


def test_validate_data_valid_msg_returns_true() -> None:
    """A full, valid payload should validate successfully."""
    msg = {
        "at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
        "site": "1",
        "val": 3,
    }
    assert validate_data(msg) is True


def test_validate_data_missing_fields_raises_ValueError() -> None:
    """Payloads missing required fields must raise ValueError."""
    msg = {"at": (datetime.now(timezone.utc)).isoformat(), "val": 1}
    with pytest.raises(ValueError):
        validate_data(msg)


def test_validate_data_future_timestamp_raises_ValueError() -> None:
    """Arrange/Act/Assert: validate_data raises ValueError when 'at' is a
      future timestamp while other fields are valid."""
    # Arrange
    future_ts = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    payload: dict = {"at": future_ts, "site": "1", "val": 2}

    # Act / Assert
    with pytest.raises(ValueError):
        validate_data(payload)
