import os

SOFT_ASSERTS = os.getenv("SOFT_ASSERTS", "1") != "0"


def soft_assert(condition, message=None):
    if condition:
        return
    if SOFT_ASSERTS:
        msg = message if message else "assertion failed"
        print(f"MOCK: soft assert failed: {msg}")
        return
    assert condition, message
