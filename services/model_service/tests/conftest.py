import pytest
from unittest.mock import MagicMock
from core.processor import manager

@pytest.fixture(autouse=True)
def mock_models():
    mock = MagicMock()
    manager.models = {
        "small_model":        mock,
        "normal_model":       mock,
        "multilingual_model": mock,
    }
    yield