import pytest
import uuid

from repository.vector import build_filename_filter
from qdrant_client.models import FieldCondition, MatchAny, PointStruct

from repository.vector import deep_search, build_filename_filter
from schemas.search import SearchHit, SearchParams


def test_build_filename_filter_single():
    f = build_filename_filter(["doc1.txt"])
    assert f.must == [FieldCondition(key="filename", match=MatchAny(any=["doc1.txt"]))]

def test_build_filename_filter_multiple():
    f = build_filename_filter(["doc1.txt", "doc2.txt"])
    assert f.must == [FieldCondition(key="filename", match=MatchAny(any=["doc1.txt", "doc2.txt"]))]


async def test_query_collection_single_point(search_with_single_point):

    search_results: list[SearchHit] = search_with_single_point
    assert len(search_results) == 1
    assert search_results[0].text == "Mars is the red planet"
    assert search_results[0].filename == "test.txt"


async def test_query_collection_multiple_point(search_with_multiple_points):
    
    search_results: list[SearchHit] = search_with_multiple_points
    
    assert len(search_results) == 3
    assert search_results[0].filename == "test.txt"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def deep_params():
    return SearchParams(
        query="Mars", model="small_model", filenames="test.txt",
        top_k=5, score=0.5, dif=0.0, deep=True, deep_min=0.0,
    )


@pytest.fixture
def borderline_point():
    # Vector [1.0, 0, 0...] has cosine ≈ 0.05 against [0.1]*384
    # Falls between deep_min=0.0 and score=0.5 → borderline candidate
    return [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=[1.0] + [0.0] * 383,
            payload={
                "text":        "Mars is a planet. It is red.",
                "filename":    "test.txt",
                "document_id": 1,
                "chunk_index": 10,
            }
        )
    ]


# ── deep_search ───────────────────────────────────────────────────────────────

async def test_deep_search_rescues_borderline_hit(qdrant_client, seed_factory, borderline_point, deep_params):
    # WireMock returns 0.85 >= params.score(0.5) → rescued
    await seed_factory(borderline_point)
    collection = "docs_small_r2"

    results = await deep_search(
        qdrant_client, collection, [0.1] * 384,
        deep_params, existing=set(), search_filter=None,
    )

    assert len(results) == 1
    assert results[0].chunk_index == 10
    assert results[0].filename == "test.txt"
    assert results[0].score == 0.85


async def test_deep_search_not_rescued_when_sentence_score_too_low(qdrant_client, seed_factory, borderline_point):
    # Set params.score=0.99 → WireMock's 0.85 doesn't qualify
    params = SearchParams(
        query="Mars", model="small_model", filenames="test.txt",
        top_k=5, score=0.99, dif=0.0, deep=True, deep_min=0.0,
    )
    await seed_factory(borderline_point)

    results = await deep_search(
        qdrant_client, "docs_small_r2", [0.1] * 384,
        params, existing=set(), search_filter=None,
    )

    assert len(results) == 0


async def test_deep_search_skips_chunk_already_in_existing(qdrant_client, seed_factory, borderline_point, deep_params):
    await seed_factory(borderline_point)

    results = await deep_search(
        qdrant_client, "docs_small_r2", [0.1] * 384,
        deep_params, existing={10}, search_filter=None,  # chunk 10 already found
    )

    assert len(results) == 0


async def test_deep_search_skips_hit_above_score_threshold(qdrant_client, seed_factory, deep_params):
    # Vector identical to query → cosine = 1.0 >= params.score(0.5) → skipped
    high_score_point = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=[0.1] * 384,
            payload={
                "text": "Mars is a planet. It is red.",
                "filename": "test.txt",
                "document_id": 1,
                "chunk_index": 20,
            }
        )
    ]
    await seed_factory(high_score_point)

    results = await deep_search(
        qdrant_client, "docs_small_r2", [0.1] * 384,
        deep_params, existing=set(), search_filter=None,
    )

    assert len(results) == 0


async def test_deep_search_empty_collection(qdrant_client, deep_params):
    results = await deep_search(
        qdrant_client, "docs_small_r2", [0.1] * 384,
        deep_params, existing=set(), search_filter=None,
    )
    assert results == []