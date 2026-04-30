import pytest

from core.processor import clean_text, split_into_sentences, chunk_text

def test_clean_text():
    
    text_for_cleaning = "  Some Text.[citation needed] in wiki-ish format   "
    cleaned_text = clean_text(text_for_cleaning)

    assert cleaned_text == "Some Text. in wiki-ish format"

def test_chunking():
    
    text_for_chunking = "  Some Text.[citation needed] in wiki-ish format.   Some test to separate? on sentences.   "
    chunks = chunk_text(text_for_chunking)

    assert len(chunks) == 2
    assert chunks == ["in wiki-ish format. Some test to separate? on sentences.", "on sentences."]

def test_empty_chunking():
    
    text_for_chunking = ""
    with pytest.raises(ValueError, match="No sentences found in the uploaded file."):
        chunks = chunk_text(text_for_chunking)