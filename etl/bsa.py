import re
import json
import pypdf
import torch
from sentence_transformers import SentenceTransformer
import weaviate
import weaviate.classes as wvc
from tqdm import tqdm
from local_toolkit import clean_up_text


def split_to_chapters(text: str) -> list:
    """
    The function splits continious text to paragraphs using paragraph number as delimeter e.g. 1. 2. ... 456.
    Here I use approach chunking by semantic markers. More explanation: https://docs.weaviate.io/weaviate/starter-guides/generative
    """
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
    
    #
    # Step 1. Prepare text for vectorization
    #
    reader = pypdf.PdfReader("../data/БСА.pdf")
    bsa = " ".join([reader.pages[i].extract_text() for i in range(0, len(reader.pages))])
    bsa = clean_up_text(bsa)
    bsa = split_to_chapters(bsa)

    #
    # Step 2. Vectorize text using lang-uk/ukr-paraphrase-multilingual-mpnet-base
    #    
    model = SentenceTransformer('lang-uk/ukr-paraphrase-multilingual-mpnet-base')
    for i in bsa:
        i["vector"] = model.encode(i["text"])

    #
    # Step 3. Import to Weaviate
    # Weaviate boilarplate: https://docs.weaviate.io/weaviate/quickstart/local
    #
    client = weaviate.connect_to_local()
    print(client.is_ready())

    if client.collections.exists("bsa_db"):
        client.collections.delete("bsa_db")
        
    bsa_db = client.collections.create(
        name="bsa_db",
        vector_config=wvc.config.Configure.Vectors.self_provided()
        )

    bsa_objs = list()
    for i, d in enumerate(bsa):
        bsa_objs.append(wvc.data.DataObject(
            properties={
            "number": d["number"],
            "text_content": d["text"]
            },
            vector=d["vector"]
            )
        )

    bsa_db = client.collections.use("bsa_db")
    bsa_db.data.insert_many(bsa_objs)
    client.close()

    #
    # Step 4. Back-up data
    #
    for i in bsa:
        i["vector"] = i["vector"].tolist()
    with open("../data/bsa.json", "w") as f:
        json.dump(bsa, f)

