"""Tools to work with base36, for case-insensitive low-digit numbers."""

BASE_36_BASE = 36
BASE_36_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def base36_encode(positive_integer):
    """Convert from Base10 to Base36."""
    encoded_integer = ""
    while positive_integer > 0:
        positive_integer, remainder = divmod(positive_integer, BASE_36_BASE)
        encoded_integer = BASE_36_ALPHABET[remainder] + encoded_integer

    return encoded_integer


def base36_decode(string):
    """Convert from Base36 to Base10."""
    return int(string, BASE_36_BASE)
