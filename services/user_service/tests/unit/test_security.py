# unit/test_security.py
from core.security import get_hash_password, verify_password

def test_password_hash_and_verify():
    hashed = get_hash_password("mypassword")
    assert verify_password("mypassword", hashed)

def test_wrong_password_fails():
    hashed = get_hash_password("mypassword")
    assert not verify_password("wrongpassword", hashed)
