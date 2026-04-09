import asyncio
import os
import sys
import uuid

# PYTHONPATH set edilmeli
sys.path.append(os.getcwd())

print("DEBUG: Auto-Approve started")

try:
    from sqlalchemy import select
    from packages.persistence.session import session_scope
    from packages.persistence.models import CEOSuggestedTask
    from packages.orchestration.ceo.engine import get_ceo_engine
    print("DEBUG: Imports successful")
except Exception as e:
    print(f"DEBUG: Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

async def main():
    print("DEBUG: Inside main")
    try:
        async with session_scope() as db:
            res = await db.execute(
                select(CEOSuggestedTask).where(CEOSuggestedTask.status == "suggested")
            )
            suggestions = res.scalars().all()
            
            if not suggestions:
                print("DEBUG: No suggestions found to approve")
                return

            print(f"DEBUG: Found {len(suggestions)} suggestions")
            
            ceo = get_ceo_engine()
            count = 0
            for sug in suggestions:
                if count >= 10: # Limit safe run
                    break
                print(f"DEBUG: Approving {sug.title} ({sug.id})")
                try:
                    # engine.manual_approve_suggestion handles its own session_scope internally?
                    # No, engine.manual_approve_suggestion uses its own internal session_scope.
                    # This might cause a conflict if we are inside a session_scope.
                    # Let's call it outside or handle session better.
                    pass
                except Exception as e:
                    print(f"DEBUG: Error in loop: {e}")
                count += 1
            
        # Refactor: Call outside session
        ceo = get_ceo_engine()
        for sug in suggestions[:10]:
             print(f"ACTION: Approving {sug.id}")
             res = await ceo.manual_approve_suggestion(sug.id)
             print(f"RESULT: {res}")

    except Exception as e:
        print(f"DEBUG: Execution error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
