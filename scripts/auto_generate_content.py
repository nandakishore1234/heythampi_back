"""
Automated seeding: create Sections with Units and Lessons,
generating Malayalam cinema dialogue/meme contexts using Gemini API.

Key Features:
- Creates 3 contexts per lesson (beginner, intermediate, advanced)
- Each context has 12 questions at the same level
- Uses Malayalam cinema dialogues and memes as contexts (in English translation)
- Implements difficulty progression based on Section + Unit + Lesson
- Generates complete, grammatically correct questions
- Formats context as Markdown for Flutter
"""

from __future__ import annotations

import os
import sys
import random
import time
import requests

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy.orm import sessionmaker
from app.db.session import sync_engine
from app.models.content import Section, Unit, Lesson
from app.models.enums import LearningLevel, QuestionType
from app.models.meme import MemeContext
from app.models.quiz import QuizQuestion, QuizAnswer

# ====== API CONFIG ======
GEMINI_API_KEY = "AIzaSyA3i2-CCWkjUdQ1xeX8Ze3EU3dRwP-wi5A"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent?key={GEMINI_API_KEY}"

SessionLocal = sessionmaker(bind=sync_engine, autoflush=False, expire_on_commit=False)

# ====== APP CONFIG ======
CONFIG = {
    "test_mode": os.getenv("TEST_MODE", "false").lower() == "true",
}

SECTION_TOPICS = [
    "daily life", "travel", "food", "school and friends", "health",
    "internet and slang", "shopping", "work and job", "family", "festivals and culture"
]

UNIT_TOPICS_PER_SECTION = [
    ["greetings", "introductions", "small talk", "farewell", "gratitude", "asking for help", "inviting"],
    ["bus and train", "directions", "booking tickets", "at the station", "checking in", "asking locals", "travel problems"],
    ["ordering food", "in a cafe", "at a restaurant", "complaints", "paying the bill", "recommendations", "special occasions"],
    ["classroom", "exams", "projects", "friendship", "teachers", "timetable", "after school plans"],
    ["feeling sick", "doctor visit", "pharmacy", "explaining symptoms", "getting advice", "emergencies", "weather talk"],
    ["memes", "texting", "Instagram", "WhatsApp", "slang and emojis", "online fights", "viral trends"],
    ["bargaining", "grocery", "mall shopping", "paying by UPI", "discounts", "returns", "shopping online"],
    ["meetings", "job interview", "work chat", "office parties", "emails", "deadlines", "boss-talk"],
    ["family gathering", "weddings", "siblings", "talking to parents", "household chores", "arguments", "support and comfort"],
    ["onam", "vishu", "going to temple", "local sports", "movie talk", "festive eating", "dressing for festivals"]
]

def build_cinema_dialogue_prompt(topic, level, lesson_number, context_number):
    """
    Build prompt to generate Malayalam cinema dialogue/meme contexts.
    Returns 2-3 lines of iconic dialogue or meme-worthy moments.
    """
    num_lines = random.choice([2, 3])  # 2-3 lines
    
    difficulty_desc = {
        LearningLevel.beginner: "simple, everyday language suitable for complete beginners with basic vocabulary",
        LearningLevel.intermediate: "moderately complex language with some idiomatic expressions and compound sentences",
        LearningLevel.advanced: "sophisticated language with complex idioms, cultural references, and nuanced expressions"
    }
    
    # Add more variety by including context number
    variety_prompts = [
        "iconic movie dialogue",
        "memorable film conversation",
        "famous cinema scene",
        "popular Malayalam movie quote",
        "well-known dialogue from movies"
    ]
    variety_type = variety_prompts[context_number % len(variety_prompts)]
    
    return (
        f"Create a SHORT, {variety_type} about '{topic}'.\n\n"
        f"REQUIREMENTS:\n"
        f"1. Write EXACTLY {num_lines} lines (short dialogue or monologue)\n"
        f"2. Use {difficulty_desc[level]}\n"
        f"3. Can be from a famous Malayalam movie scene, OR a meme-worthy moment\n"
        f"4. Can be a monologue, 2-person exchange, or group dialogue - variety is good\n"
        f"5. Make it culturally relevant and memorable\n"
        f"6. Keep each line concise (10-20 words per line)\n"
        f"7. Must be grammatically PERFECT English\n"
        f"8. Make it DIFFERENT from typical textbook conversations\n\n"
        f"FORMAT (IMPORTANT):\n"
        f"For each line, provide:\n"
        f"- English translation (clear, grammatically correct)\n"
        f"- Romanized Malayalam (using ONLY English letters)\n\n"
        f"Output format (no labels, just alternating EN/ML):\n"
        f"English line 1\n"
        f"Malayalam romanized line 1\n"
        f"English line 2\n"
        f"Malayalam romanized line 2\n\n"
        f"Level: {level.value}\n"
        f"Keep it SHORT ({num_lines} lines), ICONIC, and appropriate for {level.value} learners!"
    )

def parse_dialogue_context(raw_text):
    """Parse Gemini response into (EN, ML) pairs."""
    pairs = []
    lines = [l.strip() for l in raw_text.strip().splitlines() if l.strip()]
    for i in range(0, len(lines), 2):
        en = lines[i] if i < len(lines) else ""
        ml = lines[i+1] if i+1 < len(lines) else ""
        if en and ml:  # Only add if both exist
            pairs.append((en, ml))
    return pairs

def format_context_as_markdown(pairs, level):
    """
    Format context as Markdown for Flutter display.
    Includes proper spacing and line breaks.
    """
    md_lines = []
    md_lines.append(f"**Context** _(Level: {level.value.title()})_\n")
    
    for i, (en, ml) in enumerate(pairs, 1):
        md_lines.append(f"{i}. {en}")
        md_lines.append(f"   _{ml}_\n")
    
    return "\n".join(md_lines)

def build_questions_for_context(pairs, topic, context_level):
    """
    Generate 12 questions for a SINGLE context at a SPECIFIC level.
    All questions match the context difficulty level.
    
    Question distribution (12 questions):
    - 3 multiple_choice_single
    - 2 multiple_choice_multi
    - 2 true_false
    - 2 text_input
    - 3 ordering
    """
    questions = []
    
    # Define question type distribution
    question_plan = [
        QuestionType.multiple_choice_single,
        QuestionType.multiple_choice_single,
        QuestionType.multiple_choice_single,
        QuestionType.multiple_choice_multi,
        QuestionType.multiple_choice_multi,
        QuestionType.true_false,
        QuestionType.true_false,
        QuestionType.text_input,
        QuestionType.text_input,
        QuestionType.ordering,
        QuestionType.ordering,
        QuestionType.ordering,
    ]
    
    random.shuffle(question_plan)
    
    # Track used questions to avoid duplicates
    used_questions = set()
    
    for idx, qtype in enumerate(question_plan):
        # Try to get a unique question
        max_attempts = 5
        for attempt in range(max_attempts):
            en_ml_pair = random.choice(pairs) if pairs else ("", "")
            
            # Create a unique key for this question
            question_key = (qtype, en_ml_pair[0][:30], context_level)
            
            if question_key not in used_questions or attempt == max_attempts - 1:
                used_questions.add(question_key)
                break
        
        prompt_en = None
        prompt_ml = None
        answers = []
        
        # === Multiple Choice Single ===
        if qtype == QuestionType.multiple_choice_single:
            prompt_en = f"What does this mean: '{en_ml_pair[0]}'?"
            prompt_ml = f"Ithu enthaanu artham: '{en_ml_pair[0]}'?"
            corrects = [{"text_en": en_ml_pair[1], "text_ml": en_ml_pair[1], "is_correct": True}]
            
            # Generate distractors from context (no hardcoding)
            selected_distractors = []
            
            if len(pairs) > 1:
                # Use other Malayalam translations from the context as distractors
                available_distractors = [ml for (en, ml) in pairs if ml != en_ml_pair[1]]
                
                # Add unique distractors
                for dist in available_distractors:
                    if dist not in selected_distractors:
                        selected_distractors.append(dist)
                    if len(selected_distractors) >= 3:
                        break
            
            # If we still need more distractors, ask Gemini to generate them
            if len(selected_distractors) < 3:
                needed = 3 - len(selected_distractors)
                generated_wrong = generate_wrong_answers(en_ml_pair[1], context_level, needed)
                
                # Add generated answers ensuring no duplicates
                for wrong in generated_wrong:
                    if wrong not in selected_distractors and wrong != en_ml_pair[1]:
                        selected_distractors.append(wrong)
                    if len(selected_distractors) >= 3:
                        break
            
            distractors = [
                {"text_en": dist, "text_ml": "", "is_correct": False}
                for dist in selected_distractors[:3]  # Max 3 distractors
            ]
            
            all_opts = corrects + distractors
            random.shuffle(all_opts)
            answers = all_opts
            
        # === Multiple Choice Multi ===
        elif qtype == QuestionType.multiple_choice_multi:
            prompt_en = "Which of these phrases appear in the dialogue?"
            prompt_ml = "Ivayil ethokkeya samsaarathil ullathu?"
            
            # Use actual phrases from context as correct answers
            num_correct = min(2, len(pairs))
            corrects = [{"text_en": en, "text_ml": ml, "is_correct": True} for (en, ml) in pairs[:num_correct]]
            
            # Track used phrases to avoid duplicates
            used_phrases = set([en.lower().strip() for en, ml in pairs[:num_correct]])
            selected_wrong = []
            
            # First, try to use other phrases from context as wrong answers
            remaining_pairs = pairs[num_correct:]
            for (en, ml) in remaining_pairs:
                if en.lower().strip() not in used_phrases and en not in [w["text_en"] for w in selected_wrong]:
                    selected_wrong.append({"text_en": en, "text_ml": ml, "is_correct": False})
                    used_phrases.add(en.lower().strip())
                if len(selected_wrong) >= 2:
                    break
            
            # If we still need more wrong answers, ask Gemini to generate them
            if len(selected_wrong) < 2:
                # Generate a wrong phrase similar to the topic
                needed = 2 - len(selected_wrong)
                sample_en = corrects[0]["text_en"] if corrects else ""
                
                if sample_en:
                    try:
                        # Ask Gemini to generate similar but wrong phrases
                        wrong_prompt = (
                            f"Generate {needed} English phrases similar in style to '{sample_en}' "
                            f"but with different content. These are wrong answers for a quiz. "
                            f"Level: {context_level.value}. One phrase per line, no numbers or labels."
                        )
                        response = generate_conversation(wrong_prompt, max_retries=1, base_wait=600)
                        generated = [line.strip() for line in response.strip().splitlines() if line.strip()]
                        
                        for phrase in generated[:needed]:
                            if phrase.lower().strip() not in used_phrases:
                                selected_wrong.append({"text_en": phrase, "text_ml": "", "is_correct": False})
                                used_phrases.add(phrase.lower().strip())
                            if len(selected_wrong) >= 2:
                                break
                    except:
                        pass  # If generation fails, continue with what we have
            
            distractors = selected_wrong
            answers = corrects + distractors
            random.shuffle(answers)
            
        # === True/False ===
        elif qtype == QuestionType.true_false:
            en_choice = random.choice(pairs)[0] if pairs else ""
            is_greeting = any(word in en_choice.lower() for word in ["hello", "hi", "good morning", "good evening", "namaste", "namaskaram"])
            prompt_en = f"This phrase is a greeting: '{en_choice}'"
            prompt_ml = f"Ee vaakya oru abhivaadanamanu: '{en_choice}'"
            answers = [
                {"text_en": "True", "text_ml": "Sheriyaanu", "is_correct": is_greeting},
                {"text_en": "False", "text_ml": "Thettaanu", "is_correct": not is_greeting},
            ]
            
        # === Text Input (Fill in blank or translate) ===
        elif qtype == QuestionType.text_input:
            words = en_ml_pair[0].split()
            if len(words) >= 4:
                # Create fill-in-the-blank with complete sentence
                blank_idx = random.randint(1, len(words) - 2)
                blanked = ' '.join(words[:blank_idx] + ['____'] + words[blank_idx + 1:])
                prompt_en = f"Fill in the blank: {blanked}"
                prompt_ml = f"Ozhivaayi ullathu nirakkuka: {blanked}"
                answers = [{"text_en": words[blank_idx], "text_ml": "", "is_correct": True}]
            else:
                prompt_en = "Translate this to Malayalam (romanized): " + en_ml_pair[0]
                prompt_ml = "Ithu Malayalathil ezhuthuka (English akshrangalil): " + en_ml_pair[0]
                answers = [{"text_en": en_ml_pair[1], "text_ml": en_ml_pair[1], "is_correct": True}]
                
        # === Ordering (Complete Sentences from Context) ===
        elif qtype == QuestionType.ordering:
            # Generate ordering question from actual dialogue in the context
            # Pick a sentence from the context
            sentence_to_use = random.choice(pairs)[0] if pairs else en_ml_pair[0]
            words = sentence_to_use.split()
            
            # Determine chunk size based on difficulty
            if context_level == LearningLevel.beginner:
                # Beginner: 2-3 words per chunk
                chunk_size = random.choice([2, 3])
            elif context_level == LearningLevel.intermediate:
                # Intermediate: 3-4 words per chunk
                chunk_size = random.choice([3, 4])
            else:
                # Advanced: 4-5 words per chunk
                chunk_size = random.choice([4, 5])
            
            # Split sentence into chunks
            chunks = []
            if len(words) >= chunk_size * 2:  # Need at least 2 chunks
                for i in range(0, len(words), chunk_size):
                    chunk = ' '.join(words[i:i+chunk_size])
                    if chunk:  # Only add non-empty chunks
                        chunks.append(chunk)
            else:
                # Sentence too short, use word-by-word for very short sentences
                if len(words) >= 3:
                    chunks = words
                else:
                    # Fallback: use another sentence or skip
                    for pair in pairs:
                        alt_words = pair[0].split()
                        if len(alt_words) >= 3:
                            chunks = alt_words
                            sentence_to_use = pair[0]
                            break
                    
                    if not chunks:
                        # Last resort: create simple chunks from what we have
                        chunks = words if len(words) >= 2 else [sentence_to_use]
            
            # Need at least 2 chunks for ordering to make sense
            if len(chunks) < 2:
                # Skip this ordering question, fallback to text input
                prompt_en = "Translate this to Malayalam (romanized): " + en_ml_pair[0]
                prompt_ml = "Ithu Malayalathil ezhuthuka (English akshrangalil): " + en_ml_pair[0]
                answers = [{"text_en": en_ml_pair[1], "text_ml": en_ml_pair[1], "is_correct": True}]
            else:
                correct_order = chunks.copy()
                
                # Create shuffled version
                shuffled = correct_order.copy()
                attempts = 0
                while shuffled == correct_order and attempts < 10:
                    random.shuffle(shuffled)
                    attempts += 1
                
                prompt_en = f"Arrange these words to form the correct sentence:"
                prompt_ml = f"Ee vaakkangale sheriyaya kramathil aayi oru poornamaya vaakya undaakkuka:"
                
                # For Malayalam, we can use the Malayalam from the same sentence if available
                ml_sentence = None
                for en, ml in pairs:
                    if en == sentence_to_use:
                        ml_sentence = ml
                        break
                
                # Split Malayalam into same number of chunks if available
                ml_chunks = []
                if ml_sentence:
                    ml_words = ml_sentence.split()
                    if len(ml_words) >= len(chunks):
                        chunk_size_ml = len(ml_words) // len(chunks)
                        for i in range(len(chunks)):
                            start = i * chunk_size_ml
                            end = start + chunk_size_ml if i < len(chunks) - 1 else len(ml_words)
                            ml_chunk = ' '.join(ml_words[start:end])
                            ml_chunks.append(ml_chunk)
                
                # Ensure we have Malayalam chunks matching English chunks
                if len(ml_chunks) != len(chunks):
                    ml_chunks = [""] * len(chunks)  # Fallback to empty if mismatch
                
                # Store each fragment with its correct position
                answers = [
                    {
                        "text_en": chunk,
                        "text_ml": ml_chunks[correct_order.index(chunk)] if ml_chunks else "",
                        "order_index": correct_order.index(chunk),
                        "is_correct": True
                    }
                    for chunk in shuffled
                ]
            
        if not prompt_en:
            prompt_en = f"About: {topic.capitalize()} (level {context_level.value})"
        if not prompt_ml:
            prompt_ml = f"Vishayam: {topic.capitalize()} (level {context_level.value})"
            
        # XP value based on level
        xp_values = {
            LearningLevel.beginner: 10,
            LearningLevel.intermediate: 20,
            LearningLevel.advanced: 30
        }
        
        q = QuizQuestion(
            question_type=qtype,
            prompt_en=prompt_en,
            prompt_ml=prompt_ml,
            difficulty_level=context_level,  # Match context level
            hint_en=None,
            hint_ml=None,
            explanation_en=None,
            explanation_ml=None,
            xp_value=xp_values.get(context_level, 10),
            order_index=idx,
            is_active=True,
        )
        questions.append({"qq": q, "answers": answers})
    
    return questions  # Return exactly 12 questions

def generate_wrong_answers(correct_answer: str, context_level: LearningLevel, count: int = 3) -> list[str]:
    """
    Ask Gemini to generate plausible wrong answers for multiple choice questions.
    Returns a list of wrong answers that are similar but incorrect.
    """
    prompt = (
        f"Generate {count} plausible but INCORRECT Malayalam romanized phrases that are similar to '{correct_answer}' "
        f"but have different meanings. These are for a {context_level.value} level language learning quiz.\n\n"
        f"Requirements:\n"
        f"1. Each phrase should be grammatically correct Malayalam (romanized in English letters)\n"
        f"2. They should be similar in length to the correct answer\n"
        f"3. They should be DIFFERENT in meaning\n"
        f"4. Appropriate for {context_level.value} learners\n"
        f"5. Each phrase on a separate line\n\n"
        f"Output format (one per line, no numbers or labels):\n"
        f"Wrong phrase 1\n"
        f"Wrong phrase 2\n"
        f"Wrong phrase 3\n"
    )
    
    try:
        response = generate_conversation(prompt, max_retries=1, base_wait=600)
        wrong_answers = [line.strip() for line in response.strip().splitlines() if line.strip()]
        # Return only the requested count
        return wrong_answers[:count]
    except:
        # If generation fails, return empty list
        return []

def generate_conversation(prompt: str, max_retries=3, base_wait=1800) -> str:
    """
    Call Gemini API with automatic retry and exponential backoff for 429 errors.
    """
    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"text": prompt}]
        }]
    }
    
    for attempt in range(max_retries):
        try:
            r = requests.post(API_URL, json=payload, timeout=60)
            
            if r.status_code == 429:
                wait = base_wait * (2 ** attempt)
                print(f"⏳ [WARNING] Gemini 429 - sleeping for {wait//60} minutes (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
                
            r.raise_for_status()
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
            
        except requests.HTTPError as e:
            if r.status_code == 429 and attempt < max_retries - 1:
                wait = base_wait * (2 ** attempt)
                print(f"🔄 [RETRY] Gemini quota exceeded; pausing for {wait//60} minutes")
                time.sleep(wait)
            else:
                print(f"❌ [ERROR] Gemini API failed: {e}")
                raise
                
    raise RuntimeError(f'Gemini API failed after {max_retries} attempts')

def main():
    session = SessionLocal()
    used_contexts = set()
    
    try:
        num_sections = 1 if CONFIG["test_mode"] else len(SECTION_TOPICS)
        lessons_per_unit = 1 if CONFIG["test_mode"] else 5
        
        for section_idx in range(num_sections):
            section_topic = SECTION_TOPICS[section_idx]
            section_title = f"Section {section_idx+1}"
            section_slug = section_topic.replace(" ", "-")
            
            section = (
                session.query(Section)
                .filter(Section.slug == section_slug)
                .one_or_none()
            )
            if section is None:
                section = Section(
                    title=section_title,
                    slug=section_slug,
                    description=section_topic.title(),
                    order_index=section_idx,
                    is_active=True,
                )
                session.add(section)
                session.commit()
                session.refresh(section)

            unit_topics = UNIT_TOPICS_PER_SECTION[section_idx]
            num_units = 1 if CONFIG["test_mode"] else len(unit_topics)
            
            for unit_idx, unit_slug in enumerate(unit_topics[:num_units]):
                unit_title = f"Unit {unit_idx+1}"
                unit_slug_clean = unit_slug.replace(" ", "-")
                
                unit = (
                    session.query(Unit)
                    .filter(Unit.section_id == section.id, Unit.slug == unit_slug_clean)
                    .one_or_none()
                )
                if unit is None:
                    unit = Unit(
                        section_id=section.id,
                        title=unit_title,
                        slug=unit_slug_clean,
                        description=unit_slug,
                        order_index=unit_idx,
                        is_active=True
                    )
                    session.add(unit)
                    session.commit()
                    session.refresh(unit)
                
                print(f"\n{'='*80}")
                print(f"📚 Starting {unit.title} ({unit_slug}) - Generating {lessons_per_unit} lessons")
                print(f"{'='*80}\n")
                
                for lesson_idx in range(lessons_per_unit):
                    lesson_slug = f"{unit.slug}-lesson-{lesson_idx+1}"
                    
                    # Check if lesson already exists
                    existing_lesson = (
                        session.query(Lesson)
                        .filter(Lesson.unit_id == unit.id, Lesson.slug == lesson_slug)
                        .one_or_none()
                    )
                    
                    if existing_lesson is not None:
                        # Check if it has all contexts and questions
                        context_count = session.query(MemeContext).filter(
                            MemeContext.lesson_id == existing_lesson.id
                        ).count()
                        
                        question_count = session.query(QuizQuestion).filter(
                            QuizQuestion.lesson_id == existing_lesson.id
                        ).count()
                        
                        if context_count >= 3 and question_count >= 36:
                            print(f"   ⏭️  [SKIP] Lesson complete: {existing_lesson.title} ({context_count} contexts, {question_count} questions)")
                            continue
                        else:
                            print(f"   ⚠️  [INCOMPLETE] {existing_lesson.title} has {context_count}/3 contexts, {question_count}/36 questions")
                            print(f"   🔄 Completing lesson...")
                            lesson = existing_lesson
                    else:
                        # Create new lesson (use intermediate as default lesson level)
                        lesson = Lesson(
                            unit_id=unit.id,
                            title=f"Lesson {lesson_idx + 1}",
                            slug=lesson_slug,
                            summary=None,  # Will be updated with markdown
                            level=LearningLevel.intermediate,  # Default lesson level
                            order_index=lesson_idx,
                            is_active=True,
                        )
                        session.add(lesson)
                        session.commit()
                        session.refresh(lesson)
                    
                    topic = unit_slug
                    
                    # Generate 3 contexts (one for each level)
                    levels_to_generate = [LearningLevel.beginner, LearningLevel.intermediate, LearningLevel.advanced]
                    all_markdown_contexts = []
                    total_questions_generated = 0
                    
                    for context_idx, context_level in enumerate(levels_to_generate):
                        # Check if this level context already exists
                        existing_context = session.query(MemeContext).filter(
                            MemeContext.lesson_id == lesson.id,
                            MemeContext.level == context_level
                        ).first()
                        
                        if existing_context:
                            print(f"      ⏭️  Context {context_level.value} already exists")
                            continue
                        
                        # Generate unique context
                        max_context_attempts = 5
                        pairs = None
                        
                        for attempt in range(max_context_attempts):
                            prompt = build_cinema_dialogue_prompt(topic, context_level, lesson_idx, context_idx)
                            try:
                                gemini_output = generate_conversation(prompt)
                                pairs = parse_dialogue_context(gemini_output)
                                
                                if not pairs or len(pairs) < 2:
                                    raise ValueError("Context too short (need at least 2 lines)")
                                
                                # Check for uniqueness
                                current_lines = set([en.lower().strip() for en, ml in pairs])
                                is_duplicate = False
                                
                                for used_ctx in used_contexts:
                                    used_lines = set([en.lower().strip() for en, ml in used_ctx])
                                    overlap = len(current_lines & used_lines)
                                    if overlap > len(current_lines) * 0.3:
                                        is_duplicate = True
                                        break
                                
                                if not is_duplicate:
                                    used_contexts.add(tuple(pairs))
                                    break
                                else:
                                    if attempt == max_context_attempts - 1:
                                        used_contexts.add(tuple(pairs))
                                        break
                            except Exception as e:
                                print(f"      ❌ [ERROR] Context generation failed: {e}")
                                if attempt == max_context_attempts - 1:
                                    continue
                        
                        if not pairs or len(pairs) < 2:
                            print(f"      ⏭️  Skipping {context_level.value} context - generation failed")
                            continue
                        
                        # Format context
                        context_str_en = "\n".join(en for en, ml in pairs)
                        context_str_ml = "\n".join(ml for en, ml in pairs)
                        markdown_context = format_context_as_markdown(pairs, context_level)
                        all_markdown_contexts.append(markdown_context)
                        
                        # Create meme context
                        mctx = MemeContext(
                            lesson_id=lesson.id,
                            context_title=f"{context_level.value.title()} Context",
                            context_text_en=context_str_en,
                            context_text_ml=context_str_ml,
                            level=context_level,
                            explanation_notes=None,
                            source_url=None,
                            is_active=True,
                        )
                        session.add(mctx)
                        session.commit()
                        session.refresh(mctx)
                        
                        # Generate 12 questions for this context at this level
                        questions = build_questions_for_context(pairs, topic, context_level)
                        
                        for q_idx, qset in enumerate(questions):
                            qq = qset["qq"]
                            qq.lesson_id = lesson.id
                            qq.meme_context_id = mctx.id
                            qq.order_index = total_questions_generated + q_idx
                            session.add(qq)
                            session.commit()
                            session.refresh(qq)
                            
                            for a_idx, a in enumerate(qset["answers"]):
                                ans = QuizAnswer(
                                    question_id=qq.id,
                                    answer_text_en=a["text_en"],
                                    answer_text_ml=a["text_ml"],
                                    is_correct=a["is_correct"],
                                    order_index=a.get("order_index", a_idx),
                                )
                                session.add(ans)
                            session.commit()
                        
                        total_questions_generated += len(questions)
                        print(f"      ✅ {context_level.value.title()} context: {len(pairs)} lines, {len(questions)} questions")
                    
                    # Update lesson summary with all markdown contexts
                    if all_markdown_contexts:
                        lesson.summary = "\n\n---\n\n".join(all_markdown_contexts)
                        session.commit()
                    
                    print(f"   ✅ {lesson.title} complete - 3 contexts, {total_questions_generated} total questions")
                
                print(f"\n🎉 Completed {unit.title} - All {lessons_per_unit} lessons done!\n")
    finally:
        session.close()

if __name__ == "__main__":
    main()
