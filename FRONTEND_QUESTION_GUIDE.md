# Frontend Question Handling Guide

## Database Structure Overview

### QuizQuestion Table
- `prompt_en`: Question text in English
- `prompt_ml`: Question text in Malayalam (transliterated)
- `question_type`: Type of question (enum)
- `difficulty_level`: beginner/intermediate/advanced

### QuizAnswer Table
- `answer_text_en`: Answer text in English
- `answer_text_ml`: Answer text in Malayalam (transliterated)
- `is_correct`: Boolean indicating if this is a correct answer
- `order_index`: Used for ordering questions (indicates correct position)

---

## Question Type Implementations

### 1. Multiple Choice Single (`multiple_choice_single`)

**Database Structure:**
```json
{
  "question": {
    "prompt_en": "What does this mean: 'Hello, how are you?'",
    "prompt_ml": "Ithu enthaanu artham: 'Hello, how are you?'?"
  },
  "answers": [
    {"answer_text_en": "Namaskaram, sukhamano?", "is_correct": true},
    {"answer_text_en": "Sari, nanni", "is_correct": false},
    {"answer_text_en": "Enthu vishesham?", "is_correct": false},
    {"answer_text_en": "Poyi varaam", "is_correct": false}
  ]
}
```

**Frontend Logic:**
1. Display all answers as radio buttons or single-choice options
2. User selects ONE answer
3. Check if selected answer has `is_correct = true`
4. Award XP if correct

---

### 2. Multiple Choice Multi (`multiple_choice_multi`)

**Database Structure:**
```json
{
  "question": {
    "prompt_en": "Which of these are responses in the conversation?",
    "prompt_ml": "Ivayil ethokkeya samsaarathil ullathu?"
  },
  "answers": [
    {"answer_text_en": "Hello!", "is_correct": true},
    {"answer_text_en": "How are you?", "is_correct": true},
    {"answer_text_en": "Incorrect 42", "is_correct": false},
    {"answer_text_en": "Incorrect 89", "is_correct": false}
  ]
}
```

**Frontend Logic:**
1. Display all answers as checkboxes
2. User can select MULTIPLE answers
3. Check if user selected ALL answers where `is_correct = true` AND didn't select any where `is_correct = false`
4. Award XP only if EXACTLY correct

---

### 3. True/False (`true_false`)

**Database Structure:**
```json
{
  "question": {
    "prompt_en": "'Hello' is a greeting.",
    "prompt_ml": "'Hello' oru abhivaadanamanu."
  },
  "answers": [
    {"answer_text_en": "True", "answer_text_ml": "Sheriyaanu", "is_correct": true},
    {"answer_text_en": "False", "answer_text_ml": "Thettaanu", "is_correct": false}
  ]
}
```

**Frontend Logic:**
1. Display two buttons: "True" and "False"
2. User selects one
3. Check if selected answer has `is_correct = true`
4. Award XP if correct

---

### 4. Text Input / Fill-in-the-Blank (`text_input`)

**Database Structure:**
```json
{
  "question": {
    "prompt_en": "Fill in the blank: Hello, ____ are you?",
    "prompt_ml": "Ozhivaayi ullathu nirakkuka: Hello, ____ are you?"
  },
  "answers": [
    {"answer_text_en": "how", "is_correct": true}
  ]
}
```

**OR (Translation type):**
```json
{
  "question": {
    "prompt_en": "Translate this to Malayalam (English letters): Hello",
    "prompt_ml": "Ithu Malayalathil ezhuthuka (English akshrangalil): Hello"
  },
  "answers": [
    {"answer_text_en": "Namaskaram", "is_correct": true}
  ]
}
```

**Frontend Logic:**
1. Display text input field
2. User types their answer
3. Compare user input with `answer_text_en` (case-insensitive, trimmed)
4. **Fuzzy matching recommended**: Accept if similarity > 80% (use library like `fuzzywuzzy`)
5. Award XP if match

---

### 5. Ordering / Sequencing (`ordering`)

**Database Structure:**
```json
{
  "question": {
    "prompt_en": "Put these lines in the correct conversation order:",
    "prompt_ml": "Ee vaakyangale sheriyaya kramathil aakanam:"
  },
  "answers": [
    {"answer_text_en": "How are you?", "order_index": 1, "is_correct": true},
    {"answer_text_en": "Hello!", "order_index": 0, "is_correct": true},
    {"answer_text_en": "I'm good, thanks!", "order_index": 2, "is_correct": true}
  ]
}
```

**Frontend Logic:**
1. Display all answers as draggable items (initially in database order - which is shuffled)
2. User drags to reorder them
3. After user submits, compare their order with `order_index`:
   ```javascript
   // User's final order
   const userOrder = ["Hello!", "How are you?", "I'm good, thanks!"];
   
   // Check if each item is in correct position
   const isCorrect = answers.every((answer, userPosition) => {
     return answer.order_index === userPosition;
   });
   ```
4. Award XP only if entire sequence is correct

**Example:**
- Database stores answers with:
  - Answer 1: text="How are you?", order_index=1
  - Answer 2: text="Hello!", order_index=0
  - Answer 3: text="I'm good!", order_index=2
- User must arrange them so the answer with order_index=0 is first, order_index=1 is second, etc.

---

### 6. Matching Pairs (`matching_pairs`)

**Database Structure:**
```json
{
  "question": {
    "prompt_en": "Match each English phrase to Malayalam:",
    "prompt_ml": "English vaakyanagale Malayalathil tharathamyam cheyyuka:"
  },
  "answers": [
    {"answer_text_en": "Hello", "answer_text_ml": "Namaskaram", "order_index": 0, "is_correct": true},
    {"answer_text_en": "Thank you", "answer_text_ml": "Nanni", "order_index": 1, "is_correct": true},
    {"answer_text_en": "Goodbye", "answer_text_ml": "Poyi varaam", "order_index": 2, "is_correct": true}
  ]
}
```

**Frontend Logic:**
1. Display two columns:
   - Left: All `answer_text_en` values
   - Right: All `answer_text_ml` values (shuffled)
2. User draws lines connecting matches
3. Check if each pair matches the correct `answer_text_en` with its `answer_text_ml`
4. Award XP only if ALL pairs are correct

**Alternative UI (simpler):**
- Show English phrase
- Dropdown to select corresponding Malayalam phrase
- Repeat for each pair

---

## XP Award System

Based on question difficulty:
- **Beginner**: 10 XP
- **Intermediate**: 20 XP
- **Advanced**: 30 XP

```javascript
// Award XP on correct answer
if (isAnswerCorrect) {
  const xp = question.xp_value; // From database
  awardUserXP(userId, xp);
}
```

---

## API Response Format (Suggested)

```json
{
  "lesson_id": 1,
  "questions": [
    {
      "id": 123,
      "question_type": "ordering",
      "prompt_en": "Put these lines in the correct conversation order:",
      "prompt_ml": "Ee vaakyangale sheriyaya kramathil aakanam:",
      "difficulty_level": "beginner",
      "xp_value": 10,
      "hint_en": null,
      "answers": [
        {
          "id": 456,
          "answer_text_en": "How are you?",
          "answer_text_ml": "Sukhamano?",
          "order_index": 1,
          "is_correct": true
        },
        {
          "id": 457,
          "answer_text_en": "Hello!",
          "answer_text_ml": "Namaskaram!",
          "order_index": 0,
          "is_correct": true
        }
      ],
      "context": {
        "context_text_en": "Hello!\nHow are you?",
        "context_text_ml": "Namaskaram!\nSukhamano?"
      }
    }
  ]
}
```

---

## Testing the Questions

Run this query to see a sample question with answers:

```sql
SELECT 
  q.id,
  q.question_type,
  q.prompt_en,
  q.difficulty_level,
  q.xp_value,
  json_agg(
    json_build_object(
      'answer_text_en', a.answer_text_en,
      'answer_text_ml', a.answer_text_ml,
      'order_index', a.order_index,
      'is_correct', a.is_correct
    ) ORDER BY a.order_index
  ) as answers
FROM quiz_questions q
LEFT JOIN quiz_answers a ON a.question_id = q.id
WHERE q.question_type = 'ordering'
GROUP BY q.id
LIMIT 1;
```

