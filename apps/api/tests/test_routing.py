import pytest

from ava_api.platform.routing import _estimate_confidence, _pick_model


def test_confidence_low_for_uncertain():
    assert _estimate_confidence("I don't know") < 0.5


def test_pick_model_defaults():
    m = _pick_model("research")
    assert isinstance(m, str)
