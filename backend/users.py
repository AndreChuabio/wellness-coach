"""
users.py - Single source of truth for the allowlist of users.

Two users only — Andre and Nikki. Anything beyond that is a 400.
"""

USERS = ("andre", "nikki")

DISPLAY_NAMES = {
    "andre": "Andre",
    "nikki": "Nikki",
}


def is_valid(user: str) -> bool:
    return user in USERS


def display_name(user: str) -> str:
    return DISPLAY_NAMES.get(user, user.capitalize())
