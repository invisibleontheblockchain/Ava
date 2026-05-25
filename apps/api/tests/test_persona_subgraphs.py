from ava_api.agents.persona_graphs import PERSONA_TYPES, compile_persona_subgraph


def test_each_persona_compiles():
    for persona in PERSONA_TYPES:
        g = compile_persona_subgraph(persona)
        assert g is not None
