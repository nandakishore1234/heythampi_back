"""
Automated seeding: create 1 Section with 5 Units, each with 6 Lessons,
and generate dialogues using Gemini API.

Behavior:
- Stores English lines in context_text_en
- Stores Malayalam lines (including ML: prefix) in context_text_ml
- Prevents duplicate entries
"""

from __future__ import annotations

import os
import random
import time
import requests
from sqlalchemy.orm import sessionmaker
from app.db.session import sync_engine
from app.models.content import Section, Unit, Lesson
from app.models.enums import LearningLevel, QuestionType
from app.models.meme import MemeContext
from app.models.quiz import QuizQuestion, QuizAnswer

# ====== API CONFIG ======
GEMINI_API_KEY = "AIzaSyA3i2-CCWkjUdQ1xeX8Ze3EU3dRwP-wi5A"  # Your valid key
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent?key={GEMINI_API_KEY}"

SessionLocal = sessionmaker(bind=sync_engine, autoflush=False, expire_on_commit=False)

# ====== APP CONFIG ======
CONFIG = {
    "test_mode": os.getenv("TEST_MODE", "false").lower() == "true",
    "section": {
        "title": "Section 1 - Daily Life",
        "slug": "section-1-daily-life",
        "description": "Core daily-life themed lessons with dialogues only.",
    },
    "units": [
        {"title": "Unit 1 - Greetings", "slug": "unit-1-greetings"},
        {"title": "Unit 2 - Food & Cafes", "slug": "unit-2-food-cafes"},
        {"title": "Unit 3 - Travel & Directions", "slug": "unit-3-travel"},
        {"title": "Unit 4 - School & Friends", "slug": "unit-4-school-friends"},
        {"title": "Unit 5 - Internet & Slang", "slug": "unit-5-internet-slang"},
    ],
    "lessons_per_unit": 6,
    "levels": [
        LearningLevel.beginner,
        LearningLevel.intermediate,
        LearningLevel.advanced,
    ],
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

def turns_for_level(level):
    """
    Returns number of conversation turns (each turn = 1 EN + 1 ML line).
    Random 3-5 turns per conversation for variety.
    """
    return random.randint(3, 5)  # 3-5 turns = 6-10 lines total

def build_prompt(topic, level, lesson_number, unit_number):
    """
    Build a unique prompt that forces Gemini to generate different conversations.
    Uses lesson and unit numbers to create variety.
    """
    n_turns = turns_for_level(level)
    
    # Create specific scenarios to force different conversations
    scenarios = [
        f"two friends meeting at a {topic} place",
        f"a customer and shopkeeper discussing {topic}",
        f"two strangers starting a conversation about {topic}",
        f"a teacher and student talking about {topic}",
        f"two colleagues chatting about {topic}",
        f"family members discussing {topic}",
        f"someone asking for help with {topic}",
        f"people making plans related to {topic}",
        f"someone giving advice about {topic}",
        f"two people sharing experiences about {topic}"
    ]
    
    # Pick scenario based on lesson number to ensure variety
    scenario = scenarios[lesson_number % len(scenarios)]
    
    # Add time/place context for more variety
    contexts = [
        "in the morning",
        "in the evening", 
        "at a cafe",
        "on the street",
        "at home",
        "at work",
        "on the phone",
        "at a bus stop",
        "in a shop",
        "at school"
    ]
    context = contexts[unit_number % len(contexts)]
    
    return (
        f"Create a UNIQUE and ORIGINAL {n_turns}-turn conversation between {scenario} {context}. "
        f"Topic: {topic}. Level: {level.value}. "
        f"\n\n"
        f"CRITICAL REQUIREMENTS:\n"
        f"1. Write EXACTLY {n_turns} conversation turns ({n_turns*2} lines total)\n"
        f"2. DO NOT use common phrases like 'Namaskaram, ningalude peru enthanu?' or 'Ente peru [name]'\n"
        f"3. Create NEW and CREATIVE dialog - avoid greetings if possible\n"
        f"4. For each turn: First line in English, second line in Malayalam (using ONLY English letters)\n"
        f"5. Malayalam must be romanized like 'Sukhamano?' or 'Enthu vishesham?' - NO Malayalam script\n"
        f"\n"
        f"Format (no prefixes, no numbers):\n"
        f"English sentence here\n"
        f"Malayalam romanized here\n"
        f"Next English sentence\n"
        f"Next Malayalam romanized\n"
        f"\n"
        f"Make it natural, conversational, and DIFFERENT from typical textbook dialogs."
    )

def parse_gemini_conversation(raw_text):
    pairs = []
    lines = [l.strip() for l in raw_text.strip().splitlines() if l.strip()]
    for i in range(0, len(lines), 2):
        en = lines[i] if i < len(lines) else ""
        ml = lines[i+1] if i+1 < len(lines) else ""
        pairs.append((en, ml))
    return pairs

def build_questions_from_pairs(pairs, topic):
    """
    Generate questions with ALL 3 levels in EACH lesson:
    - 15-20 beginner questions
    - 15-20 intermediate questions  
    - 15-20 advanced questions
    Total: 50-60 questions per lesson covering all 6 question types.
    Ensures no duplicate questions by tracking used pairs.
    """
    questions = []
    levels = [LearningLevel.beginner, LearningLevel.intermediate, LearningLevel.advanced]
    qtypes = [
        QuestionType.multiple_choice_single,
        QuestionType.multiple_choice_multi,
        QuestionType.true_false,
        QuestionType.text_input,
        QuestionType.ordering,
        'matching_pairs'  # Will handle separately
    ]
    
    # Each lesson gets questions from ALL 3 levels
    level_quantity = {
        LearningLevel.beginner: 18,      # 18 beginner questions
        LearningLevel.intermediate: 18,   # 18 intermediate questions
        LearningLevel.advanced: 18        # 18 advanced questions
    }
    
    # Track used pairs to avoid duplicates
    used_questions = set()
    
    for lvl in levels:
        for idx in range(level_quantity[lvl]):
            # Try to get a unique question
            max_attempts = 10
            for attempt in range(max_attempts):
                qtype = random.choice(qtypes)
                en_ml_pair = random.choice(pairs) if pairs else ("", "")
                
                # Create a unique key for this question
                question_key = (qtype, en_ml_pair[0][:50], lvl)
                
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
                
                # Generate meaningful distractors from other pairs
                if len(pairs) > 1:
                    # Get unique distractors from actual conversation
                    available_distractors = [ml for (en, ml) in pairs if ml != en_ml_pair[1]]
                    num_needed = min(3, len(available_distractors))
                    selected_distractors = random.sample(available_distractors, num_needed)
                    
                    # If we need more, create plausible wrong answers based on topic
                    generic_distractors = [
                        "Shari", "Nanni", "Ente Peru", "Njan varunnudu", 
                        "Sukhamano?", "Enthanu?", "Shariyaanu", "Thettanu",
                        "Njan arinjilla", "Vishakkunnu", "Nalla divasam"
                    ]
                    while len(selected_distractors) < 3:
                        extra = random.choice([d for d in generic_distractors if d not in selected_distractors and d != en_ml_pair[1]])
                        selected_distractors.append(extra)
                    
                    distractors = [
                        {"text_en": dist, "text_ml": "", "is_correct": False}
                        for dist in selected_distractors[:3]
                    ]
                else:
                    # Use generic but meaningful wrong answers
                    distractors = [
                        {"text_en": random.choice(["Shari", "Nanni", "Sukhamano?"]), "text_ml": "", "is_correct": False},
                        {"text_en": random.choice(["Ente Peru", "Njan varunnudu", "Enthanu?"]), "text_ml": "", "is_correct": False},
                        {"text_en": random.choice(["Shariyaanu", "Njan arinjilla", "Vishakkunnu"]), "text_ml": "", "is_correct": False}
                    ]
                
                all_opts = corrects + distractors
                random.shuffle(all_opts)
                answers = all_opts
                
            # === Multiple Choice Multi ===
            elif qtype == QuestionType.multiple_choice_multi:
                prompt_en = "Which of these are responses in the conversation?"
                prompt_ml = "Ivayil ethokkeya samsaarathil ullathu?"
                
                # Use actual conversation lines as correct answers
                num_correct = min(2, len(pairs))
                corrects = [{"text_en": en, "text_ml": ml, "is_correct": True} for (en, ml) in pairs[:num_correct]]
                
                # Create plausible wrong answers
                generic_wrong_answers = [
                    "I don't understand", "See you later", "What's your name?",
                    "Where is the bus stop?", "How much does it cost?",
                    "Can you help me?", "I'm hungry", "What time is it?",
                    "Nice to meet you", "Have a good day"
                ]
                
                # Filter out any that might accidentally match real conversation
                used_phrases = [en.lower() for en, ml in pairs]
                available_wrong = [ans for ans in generic_wrong_answers if ans.lower() not in used_phrases]
                
                num_distractors = min(2, len(available_wrong))
                distractors = [
                    {"text_en": random.choice(available_wrong), "text_ml": "", "is_correct": False}
                    for _ in range(num_distractors)
                ]
                
                answers = corrects + distractors
                random.shuffle(answers)
                
            # === True/False ===
            elif qtype == QuestionType.true_false:
                en_choice = random.choice(pairs)[0] if pairs else ""
                is_greeting = any(word in en_choice.lower() for word in ["hello", "hi", "good morning", "good evening"])
                prompt_en = f"'{en_choice}' is a greeting."
                prompt_ml = f"'{en_choice}' oru abhivaadanamanu."
                answers = [
                    {"text_en": "True", "text_ml": "Sheriyaanu", "is_correct": is_greeting},
                    {"text_en": "False", "text_ml": "Thettaanu", "is_correct": not is_greeting},
                ]
                
            # === Fill in/Short answer ===
            elif qtype == QuestionType.text_input:
                words = en_ml_pair[0].split()
                if len(words) >= 3:
                    blank_idx = random.randint(1, len(words) - 2)
                    blanked = ' '.join(words[:blank_idx] + ['____'] + words[blank_idx + 1:])
                    prompt_en = f"Fill in the blank: {blanked}"
                    prompt_ml = f"Ozhivaayi ullathu nirakkuka: {blanked}"
                    answers = [{"text_en": words[blank_idx], "text_ml": "", "is_correct": True}]
                else:
                    prompt_en = "Translate this to Malayalam (English letters): " + en_ml_pair[0]
                    prompt_ml = "Ithu Malayalathil ezhuthuka (English akshrangalil): " + en_ml_pair[0]
                    answers = [{"text_en": en_ml_pair[1], "text_ml": en_ml_pair[1], "is_correct": True}]
                    
            # === Ordering ===
            elif qtype == QuestionType.ordering:
                # Create NEW ordering scenarios based on the context topic, NOT using actual conversation
                # This creates logical sequences that students need to arrange
                
                # Number of steps based on difficulty level
                if lvl == LearningLevel.beginner:
                    num_steps = 2  # Beginner: 2 steps
                elif lvl == LearningLevel.intermediate:
                    num_steps = 3  # Intermediate: 3 steps
                else:
                    num_steps = 4  # Advanced: 4 steps
                
                # Create scenario-based ordering questions based on topic
                ordering_scenarios = {
                    "greetings": [
                        ["Say hello", "Introduce yourself", "Ask their name", "Say nice to meet you"],
                        ["Meet someone", "Shake hands", "Exchange names", "Start conversation"],
                        ["Wave hello", "Smile and greet", "Ask how they are", "Listen to response"]
                    ],
                    "food": [
                        ["Look at menu", "Choose dish", "Place order", "Receive food"],
                        ["Enter restaurant", "Find table", "Call waiter", "Order meal"],
                        ["Feel hungry", "Decide what to eat", "Go to restaurant", "Enjoy meal"]
                    ],
                    "travel": [
                        ["Check bus schedule", "Wait at stop", "Board bus", "Pay fare"],
                        ["Pack bags", "Leave home", "Reach station", "Board train"],
                        ["Ask for directions", "Follow the route", "Find destination", "Arrive safely"]
                    ],
                    "shopping": [
                        ["Enter shop", "Browse items", "Select product", "Pay at counter"],
                        ["Make shopping list", "Go to market", "Buy groceries", "Return home"],
                        ["See advertisement", "Visit store", "Try product", "Make purchase"]
                    ],
                }
                
                # Default generic sequences if topic not found
                default_scenarios = [
                    ["Start conversation", "Exchange information", "Make plans", "Say goodbye"],
                    ["Greet person", "Ask question", "Get answer", "Thank them"],
                    ["Meet someone", "Talk briefly", "Share contact", "Part ways"]
                ]
                
                # Find matching scenario or use default
                scenario_list = None
                for key in ordering_scenarios:
                    if key in topic.lower():
                        scenario_list = ordering_scenarios[key]
                        break
                
                if not scenario_list:
                    scenario_list = default_scenarios
                
                # Pick a random scenario and select the right number of steps
                chosen_scenario = random.choice(scenario_list)
                selected_steps = chosen_scenario[:num_steps]
                
                # Create unique key to avoid repetition
                ordering_key = (qtype, tuple(selected_steps), lvl)
                if ordering_key in used_questions:
                    # Try another scenario
                    for _ in range(3):
                        chosen_scenario = random.choice(scenario_list)
                        selected_steps = chosen_scenario[:num_steps]
                        ordering_key = (qtype, tuple(selected_steps), lvl)
                        if ordering_key not in used_questions:
                            break
                
                used_questions.add(ordering_key)
                
                # Create correct order
                correct_order = selected_steps.copy()
                
                # Create shuffled version
                shuffled = correct_order.copy()
                attempts = 0
                while shuffled == correct_order and attempts < 10:
                    random.shuffle(shuffled)
                    attempts += 1
                
                prompt_en = f"Put these {num_steps} steps in the correct order:"
                prompt_ml = f"Ee {num_steps} padangale sheriyaya kramathil aakanam:"
                
                # Create Malayalam translations for common action steps
                ml_translations = {
                    "Say hello": "Namaskaram parayuka",
                    "Introduce yourself": "Ninte periyum parayuka",
                    "Ask their name": "Avarde peru chodikuka",
                    "Say nice to meet you": "Kandathil santhosham ennu parayuka",
                    "Look at menu": "Menu nokkuka",
                    "Choose dish": "Dish thiranjedukuka",
                    "Place order": "Order cheyyuka",
                    "Receive food": "Bakshanam kittuka",
                    "Check bus schedule": "Bus samayam nokkuka",
                    "Wait at stop": "Stop il kaathirikkuka",
                    "Board bus": "Bus il kayaruka",
                    "Pay fare": "Paisa kodukuka",
                    "Enter shop": "Kada kayaruka",
                    "Browse items": "Saamaan nokkuka",
                    "Select product": "Product thiranjedukuka",
                    "Pay at counter": "Counter il paisa kodukuka",
                }
                
                # Store each step with its correct position
                answers = [
                    {
                        "text_en": step,
                        "text_ml": ml_translations.get(step, step),  # Use translation if available
                        "order_index": correct_order.index(step),
                        "is_correct": True
                    }
                    for step in shuffled
                ]
                
            # === Matching pairs ===
            elif qtype == 'matching_pairs':
                En = [en for en, ml in pairs]
                Ml = [ml for en, ml in pairs]
                if len(En) >= 3:
                    En_pick = random.sample(En, 3)
                    Ml_pick = random.sample(Ml, 3)
                    prompt_en = "Match each English phrase to Malayalam: " + ' | '.join(En_pick)
                    prompt_ml = "English vaakyanagale Malayalathil tharathamyam cheyyuka: " + ' | '.join(En_pick)
                    answers = [
                        {"text_en": en, "text_ml": ml, "is_correct": True, "order_index": idx}
                        for idx, (en, ml) in enumerate(zip(En_pick, Ml_pick))
                    ]
                else:
                    # Fallback to text input
                    prompt_en = "Translate: " + en_ml_pair[0]
                    prompt_ml = "Paribhashapeduthu: " + en_ml_pair[0]
                    answers = [{"text_en": en_ml_pair[1], "text_ml": en_ml_pair[1], "is_correct": True}]
                    qtype = QuestionType.text_input
                    
            if not prompt_en:
                prompt_en = f"About: {topic.capitalize()} (level {lvl.value})"
            if not prompt_ml:
                prompt_ml = f"Vishayam: {topic.capitalize()} (level {lvl.value})"
                
            qtype_enum = qtype if isinstance(qtype, QuestionType) else QuestionType.text_input
            
            q = QuizQuestion(
                question_type=qtype_enum,
                prompt_en=prompt_en,
                prompt_ml=prompt_ml,  # Now using actual Malayalam transliteration
                difficulty_level=lvl,
                hint_en=None,
                hint_ml=None,
                explanation_en=None,
                explanation_ml=None,
                xp_value=10 if lvl == LearningLevel.beginner else 20 if lvl == LearningLevel.intermediate else 30,
                order_index=idx,
                is_active=True,
            )
            questions.append({"qq": q, "answers": answers})
    
    random.shuffle(questions)
    return questions[:54]  # Return 54 questions (18 per level)

def generate_conversation(prompt: str, max_retries=3, base_wait=1800) -> str:
    """
    Call Gemini API with automatic retry and exponential backoff for 429 errors.
    
    Args:
        prompt: The text prompt for Gemini
        max_retries: Number of retry attempts (default 3)
        base_wait: Base wait time in seconds (default 1800 = 30 minutes)
    
    Returns:
        Generated conversation text from Gemini
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
            
            # Handle 429 specifically before raising
            if r.status_code == 429:
                wait = base_wait * (2 ** attempt)  # Exponential backoff
                print(f"⏳ [WARNING] Gemini 429 Too Many Requests – sleeping for {wait//60} minutes (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
                
            r.raise_for_status()
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
            
        except requests.HTTPError as e:
            if r.status_code == 429 and attempt < max_retries - 1:
                wait = base_wait * (2 ** attempt)
                print(f"🔄 [RETRY] Gemini quota exceeded; pausing for {wait//60} minutes (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                print(f"❌ [ERROR] Gemini API failed: {e}")
                raise
                
    raise RuntimeError(f'Gemini API failed after {max_retries} attempts due to repeated 429 errors')

# ====== SPLIT ENGLISH & MALAYALAM ======
def split_conversation(convo: str):
    en_lines = []
    ml_lines = []

    for line in convo.split("\n"):
        if "|" in line:
            parts = line.split("|")

            en_part = parts[0].strip()  # Keep full "EN: Hello"
            ml_part = parts[1].strip()  # Keep full "ML: Namaskaram"

            en_lines.append(en_part)
            ml_lines.append(ml_part)

    return "\n".join(en_lines), "\n".join(ml_lines)

# ====== MAIN DB INSERT ======
def main():
    session = SessionLocal()
    used_contexts = set()  # Track contexts to avoid repetition
    
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
                print(f"📚 Starting {unit.title} ({unit_slug}) - Will generate {lessons_per_unit} lessons")
                print(f"{'='*80}\n")
                
                for i in range(lessons_per_unit):
                    lesson_slug = f"{unit.slug}-lesson-{i+1}"
                    lesson = (
                        session.query(Lesson)
                        .filter(Lesson.unit_id == unit.id, Lesson.slug == lesson_slug)
                        .one_or_none()
                    )
                    if lesson is not None:
                        print(f"   ⏭️  [SKIP] Lesson exists: {lesson.title}")
                        continue
                    
                    # Each lesson gets a different conversation difficulty
                    # But questions will include ALL 3 levels
                    conversation_level = CONFIG["levels"][i % len(CONFIG["levels"])]
                    topic = unit_slug  # USE ONLY the scenario for prompts and answers
                    
                    # Try to generate unique context (retry up to 5 times if duplicate)
                    max_context_attempts = 5
                    pairs = None
                    
                    for attempt in range(max_context_attempts):
                        # Pass lesson and unit numbers to force variety
                        prompt = build_prompt(topic, conversation_level, i, unit_idx)
                        try:
                            gemini_output = generate_conversation(prompt)
                            pairs = parse_gemini_conversation(gemini_output)
                            if not pairs:
                                raise ValueError("Empty conversation from Gemini")
                            
                            # Check if context is truly unique (check individual lines, not just tuple)
                            # Convert to set of lines to check overlap
                            current_lines = set([en.lower().strip() for en, ml in pairs])
                            
                            # Check against all previously used lines
                            is_duplicate = False
                            for used_ctx in used_contexts:
                                used_lines = set([en.lower().strip() for en, ml in used_ctx])
                                # If more than 30% overlap, consider it duplicate
                                overlap = len(current_lines & used_lines)
                                if overlap > len(current_lines) * 0.3:
                                    is_duplicate = True
                                    break
                            
                            if not is_duplicate:
                                used_contexts.add(tuple(pairs))
                                break
                            else:
                                print(f"   ⚠️  Similar context detected ({overlap} overlapping lines), regenerating... (attempt {attempt+1}/{max_context_attempts})")
                                if attempt == max_context_attempts - 1:
                                    # Force accept on last attempt
                                    used_contexts.add(tuple(pairs))
                                    print(f"   ⚠️  Accepted context despite similarity (max attempts reached)")
                                    break
                        except Exception as e:
                            print(f"   ❌ [GEMINI ERROR] Could not get dialog for {lesson_slug}: {e}")
                            if attempt == max_context_attempts - 1:
                                continue
                    
                    if not pairs:
                        print(f"   ⏭️  Skipping {lesson_slug} - could not generate context")
                        continue
                    context_str_en = "\n".join(en for en, ml in pairs)
                    context_str_ml = "\n".join(ml for en, ml in pairs)
                    lesson = Lesson(
                        unit_id=unit.id,
                        title=f"Lesson {i + 1}",
                        slug=lesson_slug,
                        summary=None,
                        level=conversation_level,  # Conversation difficulty, not question mix
                        order_index=i,
                        is_active=True,
                    )
                    session.add(lesson)
                    session.commit()
                    session.refresh(lesson)
                    mctx = MemeContext(
                        lesson_id=lesson.id,
                        context_title=None,
                        context_text_en=context_str_en,
                        context_text_ml=context_str_ml,
                        explanation_notes=None,
                        source_url=None,
                        is_active=True,
                    )
                    session.add(mctx)
                    session.commit()
                    session.refresh(mctx)
                    # Always use scenario topic string (unit_slug) for Q/A creation
                    questions = build_questions_from_pairs(pairs, topic)
                    for q_idx, qset in enumerate(questions):
                        qq = qset["qq"]
                        qq.lesson_id = lesson.id
                        qq.meme_context_id = mctx.id
                        qq.order_index = q_idx
                        session.add(qq)
                        session.commit()
                        session.refresh(qq)
                        for a_idx, a in enumerate(qset["answers"]):
                            ans = QuizAnswer(
                                question_id=qq.id,
                                answer_text_en=a["text_en"],
                                answer_text_ml=a["text_ml"],
                                is_correct=a["is_correct"],
                                order_index=a_idx,
                            )
                            session.add(ans)
                        session.commit()
                    # Count questions by level
                    level_counts = {}
                    for q in questions:
                        lvl = q["qq"].difficulty_level
                        level_counts[lvl] = level_counts.get(lvl, 0) + 1
                    
                    level_str = ", ".join([f"{lvl.value}: {count}" for lvl, count in sorted(level_counts.items())])
                    print(f"   ✅ {lesson.title} (conversation: {conversation_level.value}) - {len(questions)} questions ({level_str})")
                
                print(f"\n🎉 Completed {unit.title} - All {lessons_per_unit} lessons done!\n")
    finally:
        session.close()

if __name__ == "__main__":
    main()
