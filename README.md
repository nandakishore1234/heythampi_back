# HeyThambi Backend

FastAPI + PostgreSQL backend powering the HeyThambi English-learning MVP.

## Project Structure

- `app/` – FastAPI application code (configuration, models, routers).
- `alembic/` – Database migrations generated with Alembic.
- `requirements.txt` – Locked Python dependencies.
- `.env` – Local configuration (see `.env.example`).

## Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and update credentials. Default values target the `heythambi` PostgreSQL database with user `nandu`.

## Database Migrations

1. Ensure PostgreSQL has the `heythambi` database:
   ```bash
   createdb -U nandu heythambi
   ```
2. Apply migrations:
   ```bash
   alembic upgrade head
   ```

> Note: the generated schema relies on PostgreSQL-specific features (ENUM types, JSONB, ARRAY). Adjust `ALEMBIC_DATABASE_URL` in `.env` if you use a different environment.

## Schema Highlights

- **Content Hierarchy**
  - `sections` → `units` → `lessons`
  - `Lesson.level` uses the shared `learning_level` ENUM (`BEGINNER`, `BASIC`, `INTERMEDIATE`, `ADVANCED`, `FLUENT`).
- **Meme Context & Media**
  - `meme_contexts` store bilingual captions, cultural notes, and link to `lessons`.
  - `meme_media` references Firebase/S3 objects via `storage_provider`, `remote_path`, and optional metadata (`JSONB`).
  - `tags` + join tables (`lesson_tags`, `meme_context_tags`, `quiz_question_tags`) support categorisation (slang, idioms, etc.).
- **Quizzes**
  - `quiz_questions` map to lessons and optionally a meme context. Supports multiple question types (`question_type` ENUM) with bilingual prompts.
  - `quiz_answers` holds options, correctness flags, and per-answer feedback.
- **Gamification & Progress**
  - `users` track XP, streaks, and current level.
  - `user_lesson_progress`, `user_quiz_attempts`, `user_streaks`, and `user_badges` capture progress history.
  - `badges` catalog unlockable achievements.
- **Admin Auditing**
  - `content_audit_logs` record admin CRUD actions with before/after payloads.

## Firebase Media Workflow

1. Upload meme images to Firebase Storage (or AWS S3) under a predictable path (e.g., `memes/<category>/<filename>`).
2. Store the Firebase download URL or object path in `meme_media.remote_path` along with `storage_provider="FIREBASE"`.
3. Optionally include media metadata (dimensions, file size, blur hash) within `meme_media.metadata_json`.
4. Link the media to the appropriate `meme_context`. Quiz questions referencing the same meme simply point to the shared context, enabling multiple questions per meme.

## Running the API

```bash
uvicorn app.main:app --reload
```

Health check: `GET /health`

## Next Steps

- Build FastAPI routers/controllers for content, quizzes, and admin tooling.
- Implement authentication (JWT) and integrate with the `users` table.
- Connect Firebase admin SDK for media uploads within admin workflows.
