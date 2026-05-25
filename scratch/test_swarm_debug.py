import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api", "src"))
os.environ["MOCK_LLM"] = "true"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://ava:ava@localhost:5432/ava"
os.environ["LANGGRAPH_DATABASE_URL"] = "postgresql://ava:ava@localhost:5432/ava"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

async def debug_run():
    from ava_api.agents.demo_plan import demo_three_persona_plan
    from ava_api.agents.swarm_graph import run_swarm_pipeline, compile_swarm_graph
    from ava_api.db import RunModel, init_tables, get_session_factory
    from ava_api.agents.persona_graphs import compile_persona_subgraph, PERSONA_TYPES
    from ava_api.schemas import ExecutionPlan, PlanTask
    from ava_api.agents.personas import execute_persona_task

    await init_tables()
    plan = demo_three_persona_plan()
    run_id = uuid.uuid4()
    thread_id = str(uuid.uuid4())

    # Let's test calling execute_persona_task directly for each task to see if they raise errors!
    for task in plan.tasks:
        print(f"Executing task {task.id} ({task.persona}) directly...")
        try:
            res = await execute_persona_task(
                run_id=run_id,
                plan=plan,
                task=task,
                prior_results={},
            )
            print(f"Task {task.id} success!")
        except Exception as e:
            print(f"Task {task.id} failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_run())
