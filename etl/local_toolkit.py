# Shared functions for ETL operations.
import re


def clean_up_text(text: str) -> str:
    """Get rid of newlines and multiple spaces."""
    text = re.sub("\\n", " ", text)
    text = re.sub(r"\s+", " ", text)
    # Add more options here in the future.
    return text