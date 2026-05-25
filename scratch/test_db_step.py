import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api", "src"))
os.environ["DATABASE_URL"] = "postgresql+asyncpg://ava:ava@localhost:5432/ava"

async def test_step_by_step():
    from ava_api.db import init_tables, get_session_factory, get_engine
    
    print("Step 1: Running init_tables()...")
    try:
        await init_tables()
        print("init_tables() succeeded!")
    except Exception as e:
        print("init_tables() failed!")
        import traceback
        traceback.print_exc()
        return

    print("\nStep 2: Checking if transaction is aborted by doing a simple query...")
    engine = get_engine()
    async with engine.connect() as conn:
        try:
            res = await conn.execute(text("SELECT 1;"))
            print("Simple query succeeded:", res.scalar())
        except Exception as e:
            print("Simple query failed:", e)
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    from sqlalchemy import text
    asyncio.run(test_step_by_step())
