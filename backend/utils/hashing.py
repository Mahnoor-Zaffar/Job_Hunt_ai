import hashlib


def generate_fingerprint(title: str, company: str, location: str, url: str) -> str:
    raw = f"{title.lower().strip()}|{company.lower().strip()}|{location.lower().strip()}|{url.strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()
