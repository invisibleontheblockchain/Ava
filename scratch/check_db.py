import asyncio
import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api", "src"))
os.environ["DATABASE_URL"] = "postgresql+asyncpg://ava:ava@localhost:5432/ava"

async def check_db():
    from ava_api.db import get_engine
    engine = get_engine()
    async with engine.connect() as conn:
        # Check tables
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public';"))
        tables = [r[0] for r in result.fetchall()]
        print("Tables in public schema:", tables)

        # Check agent_memory columns
        if "agent_memory" in tables:
            result = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'agent_memory';"))
            cols = result.fetchall()
            print("Columns in agent_memory:", cols)

if __name__ == "__main__":
    asyncio.run(check_db())
