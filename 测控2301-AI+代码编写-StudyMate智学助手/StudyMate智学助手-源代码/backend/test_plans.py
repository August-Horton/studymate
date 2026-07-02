import sys
sys.path.insert(0, '.')

from routers import plans
from models import StudyPlan
from database import SessionLocal

print("Testing plans module...")

try:
    # Test 1: Test the get_plan function directly
    print("\nTest 1: Testing get_plan...")
    db = SessionLocal()
    try:
        result = db.query(StudyPlan).filter(
            StudyPlan.user_id == 1,
            StudyPlan.course_id == 1
        ).first()
        print(f"Query result: {result}")
        if result:
            print(f"exam_date type: {type(result.exam_date)}")
            print(f"daily_tasks: {result.daily_tasks}")
            print(f"overall_advice: {result.overall_advice}")
            
            import json
            plan_data = {
                "exam_date": result.exam_date.strftime("%Y-%m-%d"),
                "target_score": result.target_score,
                "daily_plan": json.loads(result.daily_tasks) if result.daily_tasks else {},
                "overall_advice": result.overall_advice or ""
            }
            print(f"Formatted plan: {plan_data}")
    except Exception as e:
        print(f"Error in query: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
