import hashlib

def generate_hash(input: str) -> str:
    # Generate a SHA-256 hash of the input string
    return hashlib.sha256(input.encode("utf-8")).hexdigest()