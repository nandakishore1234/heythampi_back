"""Seed the HeyThambi database with a meme lesson and quiz set based on a cafe scene.

Run with:
    uvicorn is not needed. Activate the venv and execute:
        python scripts/seed_cafe_scene.py
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import sync_engine
from app.models.content import Lesson, Section, Unit
from app.models.enums import LearningLevel, QuestionType, StorageProvider
from app.models.meme import MemeContext, MemeMedia
from app.models.quiz import QuizAnswer, QuizQuestion
from app.models.tag import Tag

PROJECT_MEDIA_PATH = "memes/campus_cafe/cafe_scene_001.webp"


def get_or_create(session: Session, model, defaults=None, **filters):
    instance = session.query(model).filter_by(**filters).one_or_none()
    if instance:
        return instance
    params = {**filters}
    if defaults:
        params.update(defaults)
    instance = model(**params)
    session.add(instance)
    return instance


def ensure_tag(session: Session, slug: str, name: str) -> Tag:
    tag = session.query(Tag).filter_by(slug=slug).one_or_none()
    if tag:
        return tag
    tag = Tag(slug=slug, name=name)
    session.add(tag)
    return tag


def add_unique_tags(target, tags):
    existing = {tag.slug for tag in getattr(target, "tags", [])}
    for tag in tags:
        if tag.slug not in existing:
            target.tags.append(tag)
            existing.add(tag.slug)


def seed_cafe_lesson() -> None:
    engine = sync_engine
    with Session(engine) as session:
        section = get_or_create(
            session,
            Section,
            slug="campus-life",
            defaults={
                "title": "Campus Life Stories",
                "description": "College-day conversations and culture-rich moments.",
                "order_index": 10,
            },
        )

        if section.id is None:
            session.flush([section])

        unit = get_or_create(
            session,
            Unit,
            section_id=section.id,
            slug="cafe-conversations",
            defaults={
                "title": "Cafe Conversations",
                "description": "Dialogues and slang from Kerala college hangouts.",
                "order_index": 1,
            },
        )

        if unit.id is None:
            session.flush([unit])

        lesson = (
            session.query(Lesson)
            .filter_by(unit_id=unit.id, slug="college-cafe-hustle")
            .one_or_none()
        )
        if not lesson:
            lesson = Lesson(
                unit_id=unit.id,
                slug="college-cafe-hustle",
                title="College Cafe Hustle",
                summary="Friends balancing assignments, chai, and Malayalam-English banter in a campus café.",
                level=LearningLevel.basic,
                order_index=1,
                xp_reward=50,
            )
            session.add(lesson)

        if lesson.id is None:
            session.flush([lesson])

        contexts_data = [
            {
                "slug": "study-huddle",
                "title": "Study Huddle",
                "ml": "സുഹൃത്തുക്കൾ ചേർന്ന് അസൈൻമെന്റിനെക്കുറിച്ച് ചര്‍ച്ച ചെയ്യുന്ന ക്യാംപസ് കഫേയുടെ ദൃശ്യം.",
                "en": "Friends in a campus cafe huddled over assignments, balancing fun and deadlines.",
                "notes": "Focus on collaborative study vibes and casual tone.",
            },
            {
                "slug": "chai-slang",
                "title": "Chai Slang",
                "ml": "ചായയുടെ ഇടവേളയിൽ മലയാളം-ഇംഗ്ലീഷ് മിശ്രിതത്തിലുള്ള സ്ലാങ്ങുകൾ പറയും.",
                "en": "During a chai break, they mix Malayalam-English slang while catching up.",
                "notes": "Highlights code-switching and Kerala student slang.",
            },
            {
                "slug": "future-plans",
                "title": "Future Plans",
                "ml": "വ്യക്തിഗത ലക്ഷ്യങ്ങളെക്കുറിച്ച് സംസാരിക്കുന്ന സമാധാന നിമിഷം.",
                "en": "A quieter moment where they talk about internships, dreams, and next steps.",
                "notes": "Encourages reflective vocabulary about ambitions.",
            },
        ]

        meme_contexts: dict[str, MemeContext] = {}
        for idx, ctx in enumerate(contexts_data, start=1):
            context = (
                session.query(MemeContext)
                .filter_by(lesson_id=lesson.id, context_title=ctx["title"])
                .one_or_none()
            )
            if not context:
                context = MemeContext(
                    lesson_id=lesson.id,
                    context_title=ctx["title"],
                    context_text_ml=ctx["ml"],
                    context_text_en=ctx["en"],
                    explanation_notes=ctx["notes"],
                    source_url=None,
                )
                session.add(context)
            meme_contexts[ctx["slug"]] = context

        session.flush()

        # Attach media to primary context
        primary_context = meme_contexts["study-huddle"]

        media = (
            session.query(MemeMedia)
            .filter_by(remote_path=PROJECT_MEDIA_PATH)
            .one_or_none()
        )
        if not media:
            media = MemeMedia(
                meme_context_id=primary_context.id,
                storage_provider=StorageProvider.firebase,
                remote_path=PROJECT_MEDIA_PATH,
                thumbnail_path="memes/campus_cafe/cafe_scene_001_thumb.webp",
                content_hash=None,
                metadata_json={
                    "alt": "Kerala college student working on laptop at outdoor cafe",
                    "source_image_credit": "HeyThambi MVP staging asset",
                },
                is_primary=True,
            )
            session.add(media)
        else:
            media.meme_context_id = primary_context.id

        # Tagging
        tags = [
            ensure_tag(session, "college", "College"),
            ensure_tag(session, "slang", "Slang"),
            ensure_tag(session, "motivation", "Motivation"),
        ]
        add_unique_tags(lesson, tags)
        add_unique_tags(primary_context, tags[:2])

        # Quiz questions per level
        questions_data = [
            {
                "slug": "beginner-greeting",
                "level": LearningLevel.beginner.value,
                "context": meme_contexts["study-huddle"],
                "prompt_ml": "സുഹൃത്തുക്കൾ അസൈൻമെന്റിനെക്കുറിച്ച് പറയുമ്പോൾ 'deadline' എന്ന ഇംഗ്ലീഷ് വാക്കിന് മലയാളത്തിൽ എന്താണ് അർത്ഥം?",
                "prompt_en": "When they talk about the assignment, what does the English word 'deadline' mean?",
                "answers": [
                    ("മൂടൽ മഞ്ഞ്", "fog", False),
                    ("സമയ പരിധി", "time limit", True),
                    ("വൈകി വരിക", "coming late", False),
                    ("താമസം", "a delay", False),
                ],
                "hint_en": "Think of the time by which you must submit work.",
            },
            {
                "slug": "basic-chai-slang",
                "level": LearningLevel.basic.value,
                "context": meme_contexts["chai-slang"],
                "prompt_ml": "'Chai adikkam' എന്നപ്പോൾ അവർ എന്താണ് ഉദ്ദേശിക്കുന്നത്?",
                "prompt_en": "When they say 'Chai adikkam', what are they planning to do?",
                "answers": [
                    ("ചായ കുടിക്കാൻ പോകുക", "Go have tea", True),
                    ("ധാരാളം പഠിക്കുക", "Study a lot", False),
                    ("കോഴ്‌സ് മാറ്റുക", "Switch their course", False),
                    ("വീട്ടിലേക്ക് തിരികെ പോവുക", "Head back home", False),
                ],
                "hint_en": "It's a Kerala slang phrase connected to a quick break.",
            },
            {
                "slug": "intermediate-focus",
                "level": LearningLevel.intermediate.value,
                "context": meme_contexts["study-huddle"],
                "prompt_ml": "അസൈൻമെന്റിനിടെ ഒരാൾ 'stay on track' എന്ന് പറയുമ്പോൾ, എന്താണ് അവൻ ഉദ്ദേശിക്കുന്നത്?",
                "prompt_en": "During the assignment chat, when someone says 'stay on track', what do they mean?",
                "answers": [
                    ("ട്രെയിനിൽ തുടരുക", "Stay on the train", False),
                    ("പദ്ധതിയിൽ ശ്രദ്ധ കേന്ദ്രീകരിക്കുക", "Keep focused on the plan", True),
                    ("റോഡ് മാറ്റുക", "Change the road", False),
                    ("വിരാമം എടുക്കുക", "Take a break", False),
                ],
                "hint_en": "It's encouragement to maintain focus and progress.",
            },
            {
                "slug": "advanced-future",
                "level": LearningLevel.advanced.value,
                "context": meme_contexts["future-plans"],
                "prompt_ml": "'Internship' നെ അവർ മലയാളത്തിൽ എങ്ങനെ വ്യാഖ്യാനിക്കുന്നു?",
                "prompt_en": "How do they explain the word 'Internship' in Malayalam conversation?",
                "answers": [
                    ("കോൾജ് ഒന്നാം വർഷം", "First year of college", False),
                    ("പ്രായോഗിക പരിശീലനം", "Hands-on training", True),
                    ("വ്യായാമം", "Exercise", False),
                    ("വീടുകൾ സന്ദർശിക്കൽ", "Visiting homes", False),
                ],
                "hint_en": "Relates to gaining practical experience before full-time work.",
            },
            {
                "slug": "fluent-tone",
                "level": LearningLevel.fluent.value,
                "context": meme_contexts["future-plans"],
                "prompt_ml": "ചിത്രത്തിലുള്ള സംഭാഷണത്തിന്റെ ആകെ ടോൺ എന്താണ്? ഏറ്റവും അനുയോജ്യമായ വിവരണം തിരഞ്ഞെടുക്കുക.",
                "prompt_en": "What best captures the overall tone of their conversation in the scene?",
                "answers": [
                    ("മാത്രം തമാശയും കളിയും", "Purely silly banter", False),
                    ("തീവ്രമായ തർക്കം", "An intense argument", False),
                    ("രസകരവും ലക്ഷ്യസൂക്ഷ്മവും", "Playful yet goal-focused", True),
                    ("തികച്ചും നിർജ്ജീവം", "Completely disinterested", False),
                ],
                "hint_en": "Notice they mix humor with ambition.",
            },
        ]

        for index, qdata in enumerate(questions_data, start=1):
            question = (
                session.query(QuizQuestion)
                .filter_by(lesson_id=lesson.id, prompt_en=qdata["prompt_en"])
                .one_or_none()
            )
            if question:
                continue

            question = QuizQuestion(
                lesson_id=lesson.id,
                meme_context_id=qdata["context"].id,
                question_type=QuestionType.multiple_choice_single,
                prompt_ml=qdata["prompt_ml"],
                prompt_en=qdata["prompt_en"],
                difficulty_level=qdata["level"],
                hint_ml=None,
                hint_en=qdata["hint_en"],
                explanation_ml=None,
                explanation_en=None,
                xp_value=20,
                order_index=index,
                is_active=True,
            )

            for answer_index, (ml_text, en_text, is_correct) in enumerate(
                qdata["answers"], start=1
            ):
                question.answers.append(
                    QuizAnswer(
                        answer_text_ml=ml_text,
                        answer_text_en=en_text,
                        is_correct=is_correct,
                        order_index=answer_index,
                    )
                )

            session.add(question)

        session.commit()


if __name__ == "__main__":
    if not Path(PROJECT_MEDIA_PATH).suffix:
        raise SystemExit("Please set PROJECT_MEDIA_PATH to your uploaded meme filename.")
    seed_cafe_lesson()
    print("Seed data for the cafe scene has been inserted.")

