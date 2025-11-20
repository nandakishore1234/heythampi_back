"""Upload a local meme image to Firebase Storage using the app's helper."""
from __future__ import annotations

import argparse
from pathlib import Path

from app.services.firebase_media import upload_meme_asset


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload meme media to Firebase Storage.")
    parser.add_argument("local_path", type=Path, help="Path to the local image file to upload.")
    parser.add_argument(
        "--remote-path",
        required=True,
        help="Destination path within the storage bucket, e.g. memes/campus_cafe/cafe_scene_001.jpg",
    )
    parser.add_argument(
        "--content-type",
        default="image/jpeg",
        help="MIME type of the file (default: image/jpeg).",
    )
    args = parser.parse_args()

    if not args.local_path.exists():
        raise FileNotFoundError(f"File not found: {args.local_path}")

    with args.local_path.open("rb") as file_obj:
        file_bytes = file_obj.read()

    url = upload_meme_asset(
        file_bytes=file_bytes,
        destination_path=args.remote_path,
        content_type=args.content_type,
        metadata={
            "source_filename": args.local_path.name,
        },
        make_public=True,
    )

    print("Upload complete.")
    print("Remote path:", args.remote_path)
    print("Public URL:", url)


if __name__ == "__main__":
    main()


