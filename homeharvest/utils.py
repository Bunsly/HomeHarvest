import re


def parse_address_two(address_one: str):
    apt_match = re.search(r"(APT\s*.+|#[\s\S]+)$", address_one, re.I)
    return apt_match.group().strip() if apt_match else None
