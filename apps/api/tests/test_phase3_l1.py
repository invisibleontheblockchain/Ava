from ava_api.agents.l2_decomposer import validate_plan
from ava_api.schemas import ExecutionPlan, PlanTask


def test_plan_schema_valid():
    plan = ExecutionPlan(
        goal="test",
        tasks=[
            PlanTask(id="t1", description="a", persona="researcher"),
            PlanTask(id="t2", description="b", persona="writer", dependencies=["t1"]),
        ],
    )
    validate_plan(plan)
