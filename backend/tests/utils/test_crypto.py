from app.utils import crypto


def test_encrypt_roundtrip_hides_the_value():
    stored = crypto.encrypt_secret("AIza-secret-1234")
    assert stored.startswith(crypto.ENCRYPTED_PREFIX)
    assert "AIza-secret-1234" not in stored
    assert crypto.decrypt_secret(stored) == "AIza-secret-1234"


def test_encryption_is_randomized():
    assert crypto.encrypt_secret("same") != crypto.encrypt_secret("same")


def test_plaintext_from_before_encryption_is_returned_as_is():
    assert crypto.decrypt_secret("AIza-legacy") == "AIza-legacy"


def test_missing_values():
    assert crypto.decrypt_secret(None) is None
    assert crypto.decrypt_secret("") is None


def test_value_encrypted_with_another_secret_key_is_unreadable(monkeypatch):
    stored = crypto.encrypt_secret("AIza-secret")
    monkeypatch.setattr(crypto.settings, "SECRET_KEY", "rotated-secret-key")
    assert crypto.decrypt_secret(stored) is None
