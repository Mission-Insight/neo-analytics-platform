def safe_float(value):
    if value in (None, ""):
        return None

    return float(value)
