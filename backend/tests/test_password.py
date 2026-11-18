import bcrypt

from user.service import hash_password, verify_password


class TestPasswordHashing:
    def test_hash_is_bcrypt_and_not_plaintext(self):
        hashed = hash_password("secret123")
        assert hashed != "secret123"
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_same_password_produces_different_salts(self):
        assert hash_password("secret123") != hash_password("secret123")

    def test_verify_accepts_the_original_password(self):
        hashed = hash_password("secret123")
        assert verify_password("secret123", hashed) is True
        assert bcrypt.checkpw(b"secret123", hashed.encode("utf-8")) is True

    def test_verify_rejects_wrong_password(self):
        hashed = hash_password("secret123")
        assert verify_password("wrongpass", hashed) is False
        assert verify_password("Secret123", hashed) is False

    def test_verify_rejects_corrupt_or_empty_hash(self):
        assert verify_password("secret123", "") is False
        assert verify_password("secret123", "not-a-bcrypt-hash") is False
        assert verify_password("", hash_password("secret123")) is False

    def test_verify_accepts_hash_stored_as_bytes(self):
        hashed = bcrypt.hashpw(b"secret123", bcrypt.gensalt())
        assert verify_password("secret123", hashed) is True
