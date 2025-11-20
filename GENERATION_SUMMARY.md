# Content Generation Summary

## ✅ What's Been Fixed

### 1. **Malayalam Text Generation**
- ✅ All questions now have proper Malayalam (transliterated) in `prompt_ml`
- ✅ Answers include both `answer_text_en` and `answer_text_ml`
- ✅ Malayalam is in English letters (romanized), NOT Malayalam script
- ✅ Example: "Namaskaram, sukhamano?" instead of "നമസ്കാരം"

### 2. **Context Length (4 Lines Max)**
- ✅ Each lesson generates exactly 2 conversation turns = 4 lines total
- ✅ Format: 2 English lines + 2 Malayalam lines
- ✅ No more long conversations

### 3. **No Duplicate Questions**
- ✅ Tracks used question pairs within each lesson
- ✅ Retries up to 10 times to find unique content
- ✅ Each lesson has fresh questions

### 4. **No Duplicate Contexts**
- ✅ Tracks used conversation pairs globally
- ✅ Retries up to 3 times if duplicate context detected
- ✅ Each lesson has a unique conversation

### 5. **All 3 Levels in Each Lesson**
- ✅ Every lesson contains:
  - 18 beginner questions
  - 18 intermediate questions
  - 18 advanced questions
- ✅ Total: 54 questions per lesson

### 6. **Sequential Unit Completion**
- ✅ Completes ALL lessons in Unit 1 before moving to Unit 2
- ✅ Clear progress logging shows: Section → Unit → Lesson
- ✅ Example output:
  ```
  ================================================================================
  📚 Starting Unit 1 (greetings) - Will generate 5 lessons
  ================================================================================
  
     ✅ Lesson 1 (conversation: beginner) - 54 questions (beginner: 18, intermediate: 18, advanced: 18)
     ✅ Lesson 2 (conversation: intermediate) - 54 questions (beginner: 18, intermediate: 18, advanced: 18)
     ...
  
  🎉 Completed Unit 1 - All 5 lessons done!
  ```

### 7. **Fixed Ordering Questions**
- ✅ Stores each line separately with correct `order_index`
- ✅ Frontend can shuffle and validate against order_index
- ✅ See `FRONTEND_QUESTION_GUIDE.md` for implementation details

### 8. **Gemini API 429 Handling**
- ✅ Automatic retry with exponential backoff
- ✅ Waits 30 min → 1 hour → 2 hours on rate limits
- ✅ Script resumes automatically after quota resets

---

## 📊 Current Structure

### Full Curriculum (Production Mode)
```
10 Sections
  └─ 7 Units per Section
      └─ 5 Lessons per Unit
          └─ 54 Questions per Lesson (18 beginner + 18 intermediate + 18 advanced)

Total: 10 × 7 × 5 × 54 = 18,900 questions
```

### Test Mode
```
TEST_MODE=true
  1 Section
    └─ 1 Unit
        └─ 1 Lesson
            └─ 54 Questions
```

---

## 🎯 Question Types Distribution

Each lesson includes all 6 question types across all 3 difficulty levels:

1. **Multiple Choice Single** - Select one correct answer
2. **Multiple Choice Multi** - Select multiple correct answers
3. **True/False** - Boolean choice
4. **Text Input** - Fill-in-blank or translation
5. **Ordering** - Arrange conversation lines in correct sequence
6. **Matching Pairs** - Match English phrases to Malayalam

---

## 🗄️ Database Schema

### Sections
- `title`: "Section 1"
- `slug`: "daily-life"
- `description`: Topic description

### Units
- `title`: "Unit 1"
- `slug`: "greetings" (clean topic name)
- `description`: Scenario description
- Belongs to: Section

### Lessons
- `title`: "Lesson 1"
- `slug`: "greetings-lesson-1"
- `level`: Conversation difficulty (beginner/intermediate/advanced)
- Belongs to: Unit

### MemeContext
- `context_text_en`: English conversation (max 2 turns)
- `context_text_ml`: Malayalam conversation (transliterated)
- Belongs to: Lesson

### QuizQuestions
- `question_type`: Enum (multiple_choice_single, etc.)
- `prompt_en`: Question in English
- `prompt_ml`: Question in Malayalam (transliterated)
- `difficulty_level`: beginner/intermediate/advanced
- `xp_value`: 10/20/30 based on level
- Belongs to: Lesson, MemeContext

### QuizAnswers
- `answer_text_en`: Answer in English
- `answer_text_ml`: Answer in Malayalam (transliterated)
- `is_correct`: Boolean
- `order_index`: Position (for ordering questions)
- Belongs to: QuizQuestion

---

## 🚀 How to Run

### Clear existing data:
```bash
cd /home/nandakishore/projects/heythambi_back
source .venv/bin/activate
python -m scripts.clear_test_data
```

### Test mode (1 lesson):
```bash
TEST_MODE=true python -m scripts.auto_generate_content
```

### Full production run (all 350 lessons):
```bash
python -m scripts.auto_generate_content
```

### Check progress:
```sql
-- Count lessons by section/unit
SELECT 
  s.title as section,
  u.title as unit,
  COUNT(l.id) as lesson_count
FROM sections s
JOIN units u ON u.section_id = s.id
LEFT JOIN lessons l ON l.unit_id = u.id
GROUP BY s.id, s.title, u.id, u.title
ORDER BY s.order_index, u.order_index;

-- Count questions by lesson
SELECT 
  l.title,
  l.level,
  COUNT(q.id) as question_count,
  COUNT(CASE WHEN q.difficulty_level = 'beginner' THEN 1 END) as beginner_q,
  COUNT(CASE WHEN q.difficulty_level = 'intermediate' THEN 1 END) as intermediate_q,
  COUNT(CASE WHEN q.difficulty_level = 'advanced' THEN 1 END) as advanced_q
FROM lessons l
LEFT JOIN quiz_questions q ON q.lesson_id = l.id
GROUP BY l.id, l.title, l.level
ORDER BY l.id;
```

---

## 🔧 Environment Variables

Required in `.env`:
```env
GEMINI_API_KEY=AIzaSyA3i2-CCWkjUdQ1xeX8Ze3EU3dRwP-wi5A
FIREBASE_STORAGE_BUCKET=admin-d41a2.appspot.com
```

---

## 📝 Next Steps for Frontend

1. Read `FRONTEND_QUESTION_GUIDE.md` for detailed implementation
2. Create API endpoints to fetch:
   - Lessons by Unit
   - Questions by Lesson (with answers and context)
3. Implement UI for each question type
4. Handle XP awards and user progression
5. Track completed lessons and unlock next units

---

## 🎮 Gamification Features

### XP System
- Beginner questions: 10 XP
- Intermediate questions: 20 XP
- Advanced questions: 30 XP
- Max XP per lesson: 54 × (10+20+30)/3 = 1,080 XP

### Progression
- Users must complete lessons sequentially
- Units unlock after completing previous unit
- Sections unlock after completing previous section
- Track user level based on total XP earned

---

## ⚠️ Known Limitations

1. **Gemini API Rate Limits**: Free tier has strict quotas
   - Script automatically handles 429 errors with retry
   - Consider upgrading to paid tier for large-scale generation

2. **Context Uniqueness**: With 350 lessons, some similarity is expected
   - Script tries to avoid exact duplicates
   - But topics may naturally overlap

3. **Malayalam Quality**: Depends on Gemini's transliteration
   - Review generated content periodically
   - May need manual corrections for specific phrases

---

## 📞 Support

For questions about:
- **Database structure**: See `app/models/`
- **Question handling**: See `FRONTEND_QUESTION_GUIDE.md`
- **Generation logic**: See `scripts/auto_generate_content.py`

