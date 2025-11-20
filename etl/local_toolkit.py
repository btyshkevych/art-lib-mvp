# Shared functions for ETL operations.
import re

def clean_up_text(text: str) -> str:
    """Get rid of newlines and multiple spaces."""
    text = re.sub("\\n", " ", text)
    text = re.sub(r"\s+", " ", text)
    # Add more options here in the future.
    return text


def normalize_text(text:str, chunk_size:int, overlap_size:int) -> list[str]:
    """
    Splits long text to chunks with text owerlap.
    See why it is needed here: https://docs.weaviate.io/weaviate/starter-guides/generative
    """
    words = re.split(r"\s", text)
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[max(i - overlap_size, 0): i + chunk_size])
        chunks.append(chunk)
    return chunks