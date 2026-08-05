import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class ECDHEncryption:
    def __init__(self):
        self._private_key = X25519PrivateKey.generate()
        self._shared_key: bytes = None
        self._aesgcm: AESGCM = None

    @property
    def public_key_bytes(self) -> bytes:
        return self._private_key.public_key().public_bytes_raw()

    def compute_shared_key(self, peer_public_bytes: bytes) -> bytes:
        peer_key = X25519PublicKey.from_public_bytes(peer_public_bytes)
        self._shared_key = self._private_key.exchange(peer_key)
        self._aesgcm = AESGCM(
            HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=b'reverse-backdoor-ecdh',
            ).derive(self._shared_key)
        )
        return self._shared_key

    def encrypt(self, plaintext: bytes) -> bytes:
        if self._aesgcm is None:
            raise RuntimeError("Key exchange not completed")
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext

    def decrypt(self, encrypted: bytes) -> bytes:
        if self._aesgcm is None:
            raise RuntimeError("Key exchange not completed")
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]
        return self._aesgcm.decrypt(nonce, ciphertext, None)

    def is_ready(self) -> bool:
        return self._aesgcm is not None
