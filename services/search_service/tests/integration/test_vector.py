from repository.vector import build_filename_filter, query_collection, deep_search
from qdrant_client.models import FieldCondition, MatchAny

from schemas.search import SearchHit

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