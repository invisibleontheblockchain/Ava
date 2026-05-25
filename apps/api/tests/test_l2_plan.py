from ava_api.agents.demo_plan import demo_three_persona_plan
from ava_api.agents.l2_decomposer import get_task_parallel_batches, validate_plan


def test_demo_plan_validates():
    plan = demo_three_persona_plan()
    validate_plan(plan)
    batches = get_task_parallel_batches(plan)
    assert len(batches) == 2
    assert len(batches[0]) == 3  # t1, t2, t3 parallel
    assert [t.id for t in batches[1]] == ["t4"]


def test_plan_rejects_cycle():
    from ava_api.schemas import ExecutionPlan, PlanTask
    import pytest

    plan = ExecutionPlan(
        goal="bad",
        tasks=[
            PlanTask(id="a", description="a", persona="researcher", dependencies=["b"]),
            PlanTask(id="b", description="b", persona="analyst", dependencies=["a"]),
        ],
    )
    with pytest.raises(ValueError, match="cycle"):
        validate_plan(plan)
