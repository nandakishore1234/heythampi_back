"""
Clear all auto-generated test data to allow fresh regeneration
"""
from sqlalchemy.orm import sessionmaker
from app.db.session import sync_engine
from app.models.content import Section, Unit, Lesson
from app.models.meme import MemeContext
from app.models.quiz import QuizQuestion, QuizAnswer

SessionLocal = sessionmaker(bind=sync_engine, autoflush=False, expire_on_commit=False)

def main():
    session = SessionLocal()
    try:
        # Delete in reverse order due to foreign keys
        deleted_answers = session.query(QuizAnswer).delete()
        deleted_questions = session.query(QuizQuestion).delete()
        deleted_contexts = session.query(MemeContext).delete()
        deleted_lessons = session.query(Lesson).delete()
        deleted_units = session.query(Unit).delete()
        deleted_sections = session.query(Section).delete()
        
        session.commit()
        
        print(f"✅ Cleared database:")
        print(f"   - {deleted_answers} answers")
        print(f"   - {deleted_questions} questions")
        print(f"   - {deleted_contexts} contexts")
        print(f"   - {deleted_lessons} lessons")
        print(f"   - {deleted_units} units")
        print(f"   - {deleted_sections} sections")
        print("\n🚀 Ready for fresh content generation!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
