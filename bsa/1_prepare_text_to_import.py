import re
import json
import pypdf

def clean_up_text(text: str) -> str:
    """TO DO: document function. Add error handling"""
    text = re.sub("\\n", " ", text)
    text = re.sub(r"\s+", " ", text)
    # Add more options
    return text


def split_to_chapters(text: str) -> list:
    """TO DO: document function. Add error handling"""
    chanks = re.split(r"(\d{1,3}\.\s{1})", text)
    chapters = []
    for i in range(1, len(chanks)-1):
        if len(chanks[i])>100 and len(chanks[i-1])<=5:
            p = {"number": chanks[i-1].strip(), "text": chanks[i].strip()}
            chapters.append(p)
        else:
            pass
    return chapters


if __name__ == "__main__":
    
    reader = pypdf.PdfReader("БСА.pdf")
    bsa = " ".join([reader.pages[i].extract_text() for i in range(0, len(reader.pages))])
    bsa = clean_up_text(bsa)
    bsa = split_to_chapters(bsa)
    
    with open("bsa.json", "w") as f:
        json.dump(bsa, f)

