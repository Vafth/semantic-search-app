from pydantic import ValidationError
import pytest

from routers.embed import EmbedRequest

def test_embed_request_wrong_model():
    with pytest.raises(ValidationError):
        EmbedRequest(
            model="123",
            texts=["123", "123"],
            batch_size=32
        )

def test_embed_request_empty_texts():
    with pytest.raises(ValidationError):
        EmbedRequest(
            model="small_model",
            texts="123",
            batch_size=32
        )

def test_embed_request_valid():
    req = EmbedRequest(
        model="small_model",
        texts=["hello", "world"],
        batch_size=32
    )
    assert req.model == "small_model"
    assert len(req.texts) == 2