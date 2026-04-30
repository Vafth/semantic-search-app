from core.processor import deduplicate_results

def test_deduplicate_results(search_with_multiple_points):
    deduplicated_list = deduplicate_results(search_with_multiple_points, 3)

    assert len(deduplicated_list) == 2    