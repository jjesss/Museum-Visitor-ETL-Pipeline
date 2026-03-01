"""Validations for consumer.py"""
import datetime


def validate_at(at: str) -> bool:
    """Validate the 'at' field is a valid datetime string and not in the future."""
    try:
        at = datetime.datetime.fromisoformat(at)
        if at > datetime.datetime.now(datetime.timezone.utc):
            raise ValueError("at cannot be in the future")
        return True
    except ValueError:
        raise ValueError("at must be a valid datetime string")


def validate_site(site: str) -> bool:
    """Validate the 'site' field is an integer in the range [0, 5]."""
    if site is None or str(site).strip() == "":
        raise ValueError("site cannot be empty")
    try:
        site_int = int(site)
    except (ValueError, TypeError):
        raise ValueError("site must be an integer")
    if site_int not in range(0, 6):
        raise ValueError("site must be in the range [0, 5]")
    return True


def validate_val(val: str) -> bool:
    """Validate the 'val' field is an integer in the range [-1,4]."""
    if val is None or str(val).strip() == "":
        raise ValueError("val cannot be empty")
    try:
        if isinstance(val, int):
            pass
        else:
            val = int(val)
        if val not in range(-1, 5):
            raise ValueError("val must be in the range [-1, 4]")
    except ValueError:
        raise ValueError("val must be an integer")
    return True


def validate_data(data: str) -> bool:
    # Check all 3 fields exist(at, site, val)
    required_fields = ["at", "site", "val"]
    if not all(field in data for field in required_fields):
        raise ValueError("Missing required fields: at, site, val")
    # validate at
    at = data["at"]
    validate_at(at)
    # validate site
    site = data["site"]
    validate_site(site)
    # validate val
    val = data["val"]
    validate_val(val)

    return True
