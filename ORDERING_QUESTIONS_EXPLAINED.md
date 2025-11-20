# Ordering Questions - Complete Guide

## ✅ What's Fixed

### 1. **Different Difficulty Levels Have Different Line Counts**

- **Beginner**: 2 lines to order (easiest)
- **Intermediate**: 3 lines to order (medium)
- **Advanced**: 4 lines to order (hardest)

### 2. **Context Length Matches Question Difficulty**

Each lesson's conversation has enough lines for the questions:
- **Beginner conversations**: 2 turns (4 total lines: 2 EN + 2 ML)
- **Intermediate conversations**: 3 turns (6 total lines: 3 EN + 3 ML)
- **Advanced conversations**: 4 turns (8 total lines: 4 EN + 4 ML)

### 3. **No Duplicate Ordering Questions**

- Tracks used line combinations
- Retries up to 5 times to find unique ordering sets
- Ensures each ordering question is different

---

## 📊 Database Structure for Ordering Questions

### Example: Beginner Level (2 lines)

```json
{
  "question_id": 123,
  "question_type": "ordering",
  "difficulty_level": "beginner",
  "prompt_en": "Put these 2 lines in the correct conversation order:",
  "prompt_ml": "Ee 2 vaakyangale sheriyaya kramathil aakanam:",
  "answers": [
    {
      "id": 456,
      "answer_text_en": "I'm fine, thank you!",
      "answer_text_ml": "Njan nannayi, nanni!",
      "order_index": 1,
      "is_correct": true
    },
    {
      "id": 457,
      "answer_text_en": "How are you?",
      "answer_text_ml": "Sukhamano?",
      "order_index": 0,
      "is_correct": true
    }
  ]
}
```

### Example: Intermediate Level (3 lines)

```json
{
  "question_id": 124,
  "question_type": "ordering",
  "difficulty_level": "intermediate",
  "prompt_en": "Put these 3 lines in the correct conversation order:",
  "prompt_ml": "Ee 3 vaakyangale sheriyaya kramathil aakanam:",
  "answers": [
    {
      "id": 458,
      "answer_text_en": "What about you?",
      "answer_text_ml": "Ningalkko?",
      "order_index": 2,
      "is_correct": true
    },
    {
      "id": 459,
      "answer_text_en": "Hello!",
      "answer_text_ml": "Namaskaram!",
      "order_index": 0,
      "is_correct": true
    },
    {
      "id": 460,
      "answer_text_en": "I'm good, thanks!",
      "answer_text_ml": "Njan nannayi, nanni!",
      "order_index": 1,
      "is_correct": true
    }
  ]
}
```

### Example: Advanced Level (4 lines)

```json
{
  "question_id": 125,
  "question_type": "ordering",
  "difficulty_level": "advanced",
  "prompt_en": "Put these 4 lines in the correct conversation order:",
  "prompt_ml": "Ee 4 vaakyangale sheriyaya kramathil aakanam:",
  "answers": [
    {
      "id": 461,
      "answer_text_en": "Nice to meet you too!",
      "order_index": 3
    },
    {
      "id": 462,
      "answer_text_en": "Hello, my name is Ravi.",
      "order_index": 0
    },
    {
      "id": 463,
      "answer_text_en": "Nice to meet you, Ravi!",
      "order_index": 2
    },
    {
      "id": 464,
      "answer_text_en": "Hi Ravi, I'm Maya.",
      "order_index": 1
    }
  ]
}
```

---

## 🎯 Frontend Implementation

### Step-by-Step Guide

#### 1. Fetch the Question Data

```dart
// API Response
{
  "question": {
    "id": 123,
    "question_type": "ordering",
    "difficulty_level": "beginner",
    "prompt_en": "Put these 2 lines in the correct conversation order:",
    "xp_value": 10
  },
  "answers": [
    {"id": 456, "answer_text_en": "I'm fine, thank you!", "order_index": 1},
    {"id": 457, "answer_text_en": "How are you?", "order_index": 0}
  ]
}
```

#### 2. Display Answers (Already Shuffled from DB)

```dart
List<Answer> displayedAnswers = question.answers; // Use DB order (already shuffled)

// Show as draggable list
Widget buildOrderingQuestion() {
  return ReorderableListView(
    children: displayedAnswers.map((answer) {
      return ListTile(
        key: Key(answer.id.toString()),
        title: Text(answer.answerTextEn),
        trailing: Icon(Icons.drag_handle),
      );
    }).toList(),
    onReorder: (oldIndex, newIndex) {
      setState(() {
        if (newIndex > oldIndex) {
          newIndex -= 1;
        }
        final item = displayedAnswers.removeAt(oldIndex);
        displayedAnswers.insert(newIndex, item);
      });
    },
  );
}
```

#### 3. Validate User's Answer

```dart
bool checkOrderingAnswer(List<Answer> userOrderedList) {
  // Check if each answer is in its correct position
  for (int i = 0; i < userOrderedList.length; i++) {
    if (userOrderedList[i].orderIndex != i) {
      return false; // Wrong order
    }
  }
  return true; // All correct!
}
```

#### 4. Example Validation

User's final order:
```
1. "How are you?" (order_index: 0)
2. "I'm fine, thank you!" (order_index: 1)
```

Validation:
```
Position 0: answer.order_index = 0 ✅ Correct!
Position 1: answer.order_index = 1 ✅ Correct!
Result: PASS - Award 10 XP
```

If user submitted wrong order:
```
1. "I'm fine, thank you!" (order_index: 1)
2. "How are you?" (order_index: 0)
```

Validation:
```
Position 0: answer.order_index = 1 ❌ Should be 0!
Position 1: answer.order_index = 0 ❌ Should be 1!
Result: FAIL - No XP
```

---

## 🧪 Testing SQL Query

Check ordering questions in the database:

```sql
SELECT 
  q.id,
  q.difficulty_level,
  q.prompt_en,
  json_agg(
    json_build_object(
      'answer_text_en', a.answer_text_en,
      'order_index', a.order_index,
      'display_order', ROW_NUMBER() OVER (PARTITION BY q.id ORDER BY a.id)
    ) ORDER BY a.id
  ) as answers
FROM quiz_questions q
LEFT JOIN quiz_answers a ON a.question_id = q.id
WHERE q.question_type = 'ordering'
GROUP BY q.id, q.difficulty_level, q.prompt_en
LIMIT 10;
```

Expected output:
```
id  | difficulty_level | prompt_en                                      | answers
----|------------------|------------------------------------------------|-------------------
123 | beginner         | Put these 2 lines in the correct...           | [{"answer_text_en": "I'm fine", "order_index": 1}, {"answer_text_en": "How are you?", "order_index": 0}]
124 | intermediate     | Put these 3 lines in the correct...           | [{"answer_text_en": "What about you?", "order_index": 2}, ...]
125 | advanced         | Put these 4 lines in the correct...           | [{"answer_text_en": "Nice to meet...", "order_index": 3}, ...]
```

---

## 🎮 User Experience Flow

1. **User sees question**: "Put these 2 lines in the correct conversation order:"
2. **Sees shuffled lines**:
   - "I'm fine, thank you!"
   - "How are you?"
3. **Drags to reorder**:
   - "How are you?"
   - "I'm fine, thank you!"
4. **Submits answer**
5. **System validates**: Checks if position 0 has order_index=0, position 1 has order_index=1, etc.
6. **Shows result**: ✅ Correct! +10 XP

---

## 📈 Question Distribution

Per lesson (54 questions total):

### Beginner Questions (18 total)
- ~3 ordering questions with **2 lines each**

### Intermediate Questions (18 total)
- ~3 ordering questions with **3 lines each**

### Advanced Questions (18 total)
- ~3 ordering questions with **4 lines each**

---

## ⚠️ Important Notes

1. **Answers are already shuffled** when stored in the database
   - Frontend should display them in database order (which is shuffled)
   - Don't shuffle again on frontend

2. **order_index represents the CORRECT position** (0-based)
   - 0 = first in conversation
   - 1 = second in conversation
   - 2 = third in conversation
   - etc.

3. **All answers have is_correct = true** for ordering questions
   - Because all lines are part of the conversation
   - The correctness is determined by their ORDER, not by which lines are selected

4. **No duplicate ordering questions**
   - Each lesson has unique combinations
   - Even if same conversation pairs, they won't create identical ordering questions

---

## 🔧 Testing the Implementation

Run generation:
```bash
cd /home/nandakishore/projects/heythambi_back
source .venv/bin/activate
python -m scripts.clear_test_data
TEST_MODE=true python -m scripts.auto_generate_content
```

Then query to verify:
```sql
-- Count ordering questions by level
SELECT 
  difficulty_level,
  COUNT(*) as count,
  AVG(array_length(ARRAY(SELECT 1 FROM quiz_answers a WHERE a.question_id = q.id), 1)) as avg_lines
FROM quiz_questions q
WHERE question_type = 'ordering'
GROUP BY difficulty_level;

-- Expected output:
-- beginner    | 3 | 2.0
-- intermediate| 3 | 3.0
-- advanced    | 3 | 4.0
```

