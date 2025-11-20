"""Import bilingual meme metadata and auto-create lessons, contexts, text-rendered images,
and questions.

Each meme folder under --meme-root must contain a `metadata.json` file with at least:
{
  "title": "Earbud Drama",
  "english_text": "btw when you go in the bus if your earbud bursts into flames what do you do",
  "malayalam_text": "btw busil povumbo earbud therich poya enth cheyyum?",
  "topic": "Bus commute panic"  # optional, helps with question flavour
}

The script now ignores any existing image assets. Instead it renders a text-only meme image
locally (English + Malayalam transliteration centered), uploads that JPEG to Firebase, and
creates lesson context + questions tied to the provided text.

Usage:
    python -m scripts.auto_import_memes \
        --meme-root /home/nandakishore/projects/memes \
        --section-slug section-imported-memes \
        --section-title "Section - Imported Memes" \
        --unit-title "Imported Meme Lessons"
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import requests
from sqlalchemy.orm import sessionmaker

from app.db.session import sync_engine
from app.models.content import Lesson, Section, Unit
from app.models.enums import LearningLevel, StorageProvider
from app.models.meme import MemeContext, MemeMedia
from app.models.quiz import QuizAnswer, QuizQuestion
from app.services.firebase_media import upload_meme_asset

from scripts.auto_generate_content import (
    GeneratedContent,
    build_questions_from_context_only,
    build_questions_from_meme,
    question_exists,
    render_meme_image,
)

SessionLocal = sessionmaker(bind=sync_engine, autoflush=False, expire_on_commit=False)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import existing bilingual memes into lessons.")
    parser.add_argument("--meme-root", required=True, help="Path containing meme folders.")
    parser.add_argument("--section-slug", default="section-imported-memes")
    parser.add_argument("--section-title", default="Imported Meme Section")
    parser.add_argument("--unit-title", default="Imported Meme Lessons")
    parser.add_argument(
        "--learning-level",
        default=LearningLevel.beginner.value,
        choices=[lvl.value for lvl in LearningLevel],
    )
    parser.add_argument(
        "--gemini-api-key",
        default=None,
        help="Optional API key for generating richer contexts (falls back to template if missing).",
    )
    return parser.parse_args()


def slugify(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "lesson"


def load_metadata(folder: Path) -> dict[str, Any] | None:
    metadata_path = folder / "metadata.json"
    if not metadata_path.exists():
        print(f"[WARN] Missing metadata.json in {folder}, skipping.")
        return None
    try:
        with metadata_path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
    except json.JSONDecodeError as exc:
        print(f"[WARN] Bad JSON in {metadata_path}: {exc}")
        return None

    required = ["english_text", "malayalam_text"]
    if any(key not in data or not data[key].strip() for key in required):
        print(f"[WARN] metadata.json missing fields in {folder}, needs {required}")
        return None
    data.setdefault("title", folder.name)
    return data


def generate_context_lines(
    *,
    english_text: str,
    malayalam_text: str,
    api_key: str | None,
) -> tuple[str, str]:
    if not api_key:
        context_en = f"This meme jokingly asks: \"{english_text}\""
        context_ml = malayalam_text
        return context_en, context_ml

    prompt = (
        "You help Malayali learners understand English memes.\n"
        "Given the meme text in English and Malayalam transliteration, "
        "write a 2-sentence English context plus a Malayalam transliteration context."
        "Output JSON with keys context_en and context_ml.\n"
        f"Meme English text: {english_text}\n"
        f"Meme Malayalam text: {malayalam_text}\n"
    )
    url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/gemini-2.5-flash-lite:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if data.get("candidates"):
            for part in data["candidates"][0]["content"].get("parts", []):
                if "text" in part:
                    try:
                        parsed = json.loads(part["text"])
                        return parsed["context_en"], parsed["context_ml"]
                    except (json.JSONDecodeError, KeyError):
                        continue
    except requests.RequestException as exc:
        print(f"[WARN] Gemini context API failed: {exc}")

    return f"This meme says: \"{english_text}\"", malayalam_text


def main() -> None:
    args = parse_args()
    level = LearningLevel(args.learning_level)
    session = SessionLocal()
    meme_root = Path(args.meme_root)
    if not meme_root.exists():
        raise FileNotFoundError(meme_root)

    try:
        section = (
            session.query(Section)
            .filter(Section.slug == args.section_slug)
            .one_or_none()
        )
        if section is None:
            section = Section(
                title=args.section_title,
                slug=args.section_slug,
                description="Lessons generated from existing meme folders.",
                order_index=0,
                is_active=True,
            )
            session.add(section)
            session.commit()
            session.refresh(section)

        unit_slug = slugify(args.unit_title)
        unit = (
            session.query(Unit)
            .filter(Unit.section_id == section.id, Unit.slug == unit_slug)
            .one_or_none()
        )
        if unit is None:
            unit = Unit(
                section_id=section.id,
                title=args.unit_title,
                slug=unit_slug,
                order_index=0,
                is_active=True,
            )
            session.add(unit)
            session.commit()
            session.refresh(unit)

        folders = sorted(p for p in meme_root.iterdir() if p.is_dir())
        if not folders:
            print(f"No folders found under {meme_root}")
            return

        for order_idx, folder in enumerate(folders):
            metadata = load_metadata(folder)
            if metadata is None:
                continue

            context_en, context_ml = generate_context_lines(
                english_text=metadata["english_text"],
                malayalam_text=metadata["malayalam_text"],
                api_key=args.gemini_api_key,
            )

            lesson_slug = slugify(folder.name)
            existing_lesson = (
                session.query(Lesson)
                .filter(Lesson.unit_id == unit.id, Lesson.slug == lesson_slug)
                .one_or_none()
            )
            if existing_lesson:
                print(f"[SKIP] Lesson already exists for {folder.name}")
                continue

            lesson = Lesson(
                unit_id=unit.id,
                title=metadata.get("title", folder.name),
                slug=lesson_slug,
                summary=metadata.get("topic"),
                level=level,
                order_index=order_idx,
                is_active=True,
            )
            session.add(lesson)
            session.commit()
            session.refresh(lesson)

            mctx = MemeContext(
                lesson_id=lesson.id,
                context_title=metadata.get("topic"),
                context_text_en=context_en,
                context_text_ml=context_ml,
                explanation_notes=None,
                source_url=None,
                is_active=True,
            )
            session.add(mctx)
            session.commit()
            session.refresh(mctx)

            english_text = metadata["english_text"].strip()
            malayalam_text = metadata["malayalam_text"].strip()
            generated = GeneratedContent(
                meme_top_en=english_text,
                meme_bottom_en="",
                meme_top_ml=malayalam_text,
                meme_bottom_ml="",
                context_en=context_en,
                context_ml=context_ml,
                questions=[],
            )

            meme_bytes = render_meme_image(
                generated.meme_top_en,
                generated.meme_top_ml,
                generated.meme_bottom_en,
                generated.meme_bottom_ml,
            )

            remote_path = f"imported_memes/{lesson.slug}.jpg"
            meme_url = upload_meme_asset(
                file_bytes=meme_bytes,
                destination_path=remote_path,
                content_type="image/jpeg",
                metadata={"source": "imported", "mode": "text_render"},
                make_public=True,
            )
            media = MemeMedia(
                meme_context_id=mctx.id,
                storage_provider=StorageProvider.firebase,
                remote_path=meme_url,
                metadata_json={"rendered": True},
                is_primary=True,
            )
            session.add(media)
            session.commit()

            theme_text = metadata.get("topic") or metadata["english_text"]
            questions = build_questions_from_meme(generated)
            if not questions:
                questions = build_questions_from_context_only(generated)

            order_counter = 0
            for q in questions:
                if question_exists(session, section.id, q["prompt_en"]):
                    continue
                qq = QuizQuestion(
                    lesson_id=lesson.id,
                    meme_context_id=mctx.id,
                    question_type=q["type"],
                    prompt_en=q["prompt_en"],
                    prompt_ml=q["prompt_ml"],
                    difficulty_level=level,
                    xp_value=10,
                    order_index=order_counter,
                    is_active=True,
                )
                session.add(qq)
                session.commit()
                session.refresh(qq)

                answers = q.get("answers", [])
                for answer_order, a in enumerate(answers):
                    ans = QuizAnswer(
                        question_id=qq.id,
                        answer_text_en=a.get("text_en", ""),
                        answer_text_ml=a.get("text_ml") or "",
                        is_correct=bool(a.get("is_correct", False)),
                        order_index=answer_order,
                    )
                    session.add(ans)
                session.commit()
                order_counter += 1

            print(f"[OK] Imported lesson '{lesson.title}' from {folder.name}")

    finally:
        session.close()


if __name__ == "__main__":
    main()


