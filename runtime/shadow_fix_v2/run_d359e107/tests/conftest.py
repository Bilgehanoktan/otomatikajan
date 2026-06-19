import pytest
import asyncio

@pytest.fixture(scope="function")
def event_loop():
    """
    Custom event loop fixture for pytest-asyncio to ensure each test runs
    in a fully isolated event loop, preventing 'Event loop is closed' errors.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    
    # Clean up any lingering async tasks before closing
    try:
        current_task = asyncio.current_task(loop)
        pending = [t for t in asyncio.all_tasks(loop) if t is not current_task]
        for task in pending:
            task.cancel()
        if pending:
            # Shield pending tasks or finish them cleanly
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except Exception:
        pass
    finally:
        try:
            import libs.db.session as db_session
            if db_session._engine is not None:
                loop.run_until_complete(db_session._engine.dispose())
                db_session._engine = None
        except Exception:
            pass
        
        try:
            loop.close()
        except Exception:
            pass
