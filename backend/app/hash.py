from argon2 import PasswordHasher


# Initialize Argon2id hasher (you can adjust parameters for stronger hashing if needed)
ph = PasswordHasher()  # Defaults: time_cost=2, memory_cost=51200, parallelism=2

def hash_password(password: str) -> str:
    """
    Takes a plain text password and returns a secure Argon2id hash.
    """
    return ph.hash(password)

def verify_password(hashed_password: str, plain_password: str) -> bool:
    """
    Verifies if the plain password matches the stored hashed password.
    Returns True if valid, False otherwise.
    """
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except Exception:
        return False