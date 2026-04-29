import pytest
from core.processor import manager

def test_get_unknown_model_raises():
    with pytest.raises(ValueError, match="not loaded"):
        manager.get_model("nonexistent")

def test_get_model_returns_mock():
    model = manager.get_model("small_model")
    assert model is not None