"""Demo execution plan for Phase 2 go/no-go (3 parallel personas)."""

from ava_api.schemas import ExecutionPlan, PlanTask


def demo_three_persona_plan(goal: str = "Phase 2 parallel persona validation") -> ExecutionPlan:
    return ExecutionPlan(
        goal=goal,
        estimated_duration_minutes=10,
        tasks=[
            PlanTask(
                id="t1",
                description="Research key facts and sources for the goal",
                persona="researcher",
                dependencies=[],
                estimated_blocks=["web", "prompt"],
                output_type="text",
            ),
            PlanTask(
                id="t2",
                description="Build a structured comparison table from research angles",
                persona="analyst",
                dependencies=[],
                estimated_blocks=["prompt", "table"],
                output_type="table",
            ),
            PlanTask(
                id="t3",
                description="Draft executive summary prose",
                persona="writer",
                dependencies=[],
                estimated_blocks=["prompt", "memo"],
                output_type="text",
            ),
            PlanTask(
                id="t4",
                description="Synthesize all persona outputs into a final report",
                persona="writer",
                dependencies=["t1", "t2", "t3"],
                estimated_blocks=["prompt", "report"],
                output_type="text",
            ),
        ],
        deliverables=["report"],
        clarifications_needed=[],
    )
