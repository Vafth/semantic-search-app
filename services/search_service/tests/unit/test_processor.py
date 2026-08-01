from core.processor import deduplicate_results
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from core.processor import (
    _score_sentence,
    _filter_chunk_to_relevant_sentences,
    refine_results,
)
from schemas.search import SearchHit, SearchParams


def mock_httpx(scores: list[float]):
    """Build a mock AsyncClient context manager returning scores in order."""
    responses = [
        MagicMock(json=MagicMock(return_value={"score": s}), raise_for_status=MagicMock())
        for s in scores
    ]
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=responses)

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    return mock_ctx


import pytest
from core.processor import (
    _score_sentence,
    _filter_chunk_to_relevant_sentences,
    refine_results,
)
from schemas.search import SearchHit, SearchParams


# ── _score_sentence ───────────────────────────────────────────────────────────

async def test_score_sentence_returns_score_from_model_service():
    # WireMock returns 0.85 for any /similarity request
    score = await _score_sentence("Mars", "Mars is a red planet", "small_model")
    assert score == 0.85


# ── _filter_chunk_to_relevant_sentences ───────────────────────────────────────

async def test_filter_single_sentence_skips_scoring():
    # len(sentences) <= 1 → returns immediately, no httpx call at all
    result = await _filter_chunk_to_relevant_sentences(
        "Mars", "Only one sentence here.", "small_model", min_score=0.5
    )
    assert result == "Only one sentence here."


async def test_filter_keeps_sentences_above_min_score():
    # WireMock returns 0.85 for every sentence; min_score=0.5 → all kept
    chunk = "Mars is a planet. Jupiter is very big. Saturn has rings."
    result = await _filter_chunk_to_relevant_sentences(
        "Mars", chunk, "small_model", min_score=0.5
    )
    assert "Mars is a planet" in result
    assert "Jupiter" in result
    assert "Saturn" in result


async def test_filter_returns_best_when_none_meet_min_score():
    # WireMock returns 0.85 but min_score=0.99 → nothing qualifies
    # → returns the sentence with best score (all tied, so first one)
    chunk = "Mars is a planet. Jupiter is very big. Saturn has rings."
    result = await _filter_chunk_to_relevant_sentences(
        "Mars", chunk, "small_model", min_score=0.99
    )
    assert "Mars is a planet" in result
    assert "Jupiter" not in result


# ── refine_results ────────────────────────────────────────────────────────────

async def test_refine_results_keeps_text_when_score_qualifies(search_params):
    # WireMock returns 0.85; search_params.score=0.5+0.0 → sentences kept
    hits = [
        SearchHit(text="Mars is a planet. Jupiter is big.", score=0.8, chunk_index=0, filename="test.txt"),
    ]
    result = await refine_results(hits, search_params)

    assert len(result) == 1
    assert result[0].score == 0.8          # unchanged
    assert result[0].filename == "test.txt"  # unchanged
    assert "Mars" in result[0].text


async def test_refine_results_empty_list(search_params):
    result = await refine_results([], search_params)
    assert result == []