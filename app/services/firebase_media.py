"""Firebase Storage helper utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import firebase_admin
from firebase_admin import credentials, storage

from app.core.config import settings

_cred_path = Path(settings.firebase_credentials_path)
if not firebase_admin._apps:
    firebase_admin.initialize_app(
        credentials.Certificate(_cred_path),
        {"storageBucket": settings.firebase_storage_bucket},
    )


def upload_meme_asset(
    *,
    file_bytes: bytes,
    destination_path: str,
    content_type: str,
    metadata: dict[str, Any] | None = None,
    make_public: bool = True,
) -> str:
    """Upload meme media to Firebase Storage and return the public URL."""

    bucket = storage.bucket()
    blob = bucket.blob(destination_path)
    blob.upload_from_string(file_bytes, content_type=content_type)

    if metadata:
        blob.metadata = metadata
        blob.patch()

    if make_public:
        blob.make_public()
        return blob.public_url

    return blob.generate_signed_url(expiration=3600)


