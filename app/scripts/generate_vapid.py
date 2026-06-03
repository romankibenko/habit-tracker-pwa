"""Генерация VAPID-пары ключей для Web Push.

Запуск:
    python -m app.scripts.generate_vapid

Скопируй вывод в .env (VAPID_PUBLIC_KEY и VAPID_PRIVATE_KEY).
"""

from __future__ import annotations

import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def generate() -> tuple[str, str]:
    """Возвращает (public_key_b64url, private_key_b64url) формата VAPID."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_numbers = private_key.public_key().public_numbers()

    # Public — uncompressed point: 0x04 || X (32) || Y (32) = 65 байт
    x = public_numbers.x.to_bytes(32, "big")
    y = public_numbers.y.to_bytes(32, "big")
    public_bytes = b"\x04" + x + y

    # Private — 32 байта
    private_bytes = private_key.private_numbers().private_value.to_bytes(32, "big")

    return _b64url(public_bytes), _b64url(private_bytes)


if __name__ == "__main__":
    public_key, private_key = generate()
    print("Сгенерированы VAPID-ключи. Скопируй в .env:\n")
    print(f"VAPID_PUBLIC_KEY={public_key}")
    print(f"VAPID_PRIVATE_KEY={private_key}")
