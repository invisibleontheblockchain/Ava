import asyncio
import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api", "src"))
os.environ["DATABASE_URL"] = "postgresql+asyncpg://ava:ava@localhost:5432/ava"

async def test_pgvector_query():
    from ava_api.db import get_engine
    engine = get_engine()
    async with engine.connect() as conn:
        q = [0.0] * 384
        vec_literal = "[" + ",".join(str(x) for x in q) + "]"
        try:
            print("Executing pgvector query...")
            result = await conn.execute(
                text(
                    """
                    SELECT content, meta,
                           1 - (embedding_vec <=> :q::vector) AS score
                    FROM agent_memory
                    WHERE tenant_id = :tenant AND user_id = :user
                      AND embedding_vec IS NOT NULL
                    ORDER BY embedding_vec <=> :q::vector
                    LIMIT :k
                    """
                ),
                {"q": vec_literal, "tenant": "default", "user": "default", "k": 5},
            )
            print("Query succeeded! Rows count:", len(result.fetchall()))
        except Exception as e:
            print("Query failed with exception:")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pgvector_query())
