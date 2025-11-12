import requests
import re
import pypdf
import io
import json
import sys
from local_toolkit import clean_up_text
import torch
from sentence_transformers import SentenceTransformer
import weaviate
import weaviate.classes as wvc
from tqdm import tqdm
from local_toolkit import clean_up_text


def get_orders_metadata (size: int) -> list:
    """Retrieve executive orders metadata from mod.gov.ua API"""
    PAYLOAD = {"sort":[{"acceptance_date":{"order":"desc"}},{"publishedAt":{"order":"desc"}}],
               "query":{"bool":{"must":[{"term":{"locale":"uk"}},{"terms_set":{"document_tags_type":{"terms":["nakazi"],"minimum_should_match_script":{"source":"1"}}}},{"term":{"type":"documents"}}]}},"_source":["title","slug","publishedAt","locale","type","id","tags","document_tags_type","document_tags_diyalnist","acceptance_date"],
               "from":0,
               "size":size}
    resp = requests.post("https://mod.gov.ua/lookup/search?search_type=dfs_query_then_fetch", json=PAYLOAD)
    resp_dct = json.loads(resp.content.decode())
    metadata = [i["_source"] for i in resp_dct["hits"]["hits"]]
    return metadata

def get_pdf_urls(slug: str) -> list:
    """Retrieve URL to PDF documents from web pages."""
    page_url = f"https://mod.gov.ua/diyalnist/normativno-pravova-baza/{slug}"
    resp = requests.get(page_url)
    pdf_urls = list(set(re.findall(r"https\:\/\/mod\.gov\.ua\/assets\/[A-z0-9_]+\.pdf", resp.content.decode())))
    return pdf_urls

def pdf_to_plain_text (url: str) -> str:
    """Convert a PDF document (via URL) to plain text."""
    response = requests.get(url)
    memory_obj = io.BytesIO(response.content)
    pdf = pypdf.PdfReader(memory_obj)
    plain_text = " ".join([pdf.pages[i].extract_text() for i in range(0, len(pdf.pages))])
    return plain_text


if __name__ == "__main__":
    
    # Handle sapmple size
    if len(sys.argv) > 1:
        SAMPLE_SIZE = sys.argv[1]
    else:
        SAMPLE_SIZE = 10

    #
    # Step 1. Collect and process data
    #
    #mod_orders = get_orders_metadata(SAMPLE_SIZE)
    #for i in tqdm(mod_orders):
    #    i["page_url"] = f'https://mod.gov.ua/diyalnist/normativno-pravova-baza/{i["slug"]}'
    #    try:
    #        pdf_urls = get_pdf_urls(i["slug"])
    #        plain_text = map(pdf_to_plain_text, pdf_urls)
    #        clean_text = map(clean_up_text, list(plain_text))
    #        i["pdf_urls"] = pdf_urls
    #        i["text_content"] = (" ".join(list(clean_text)))
    #        
    #    except Exception as e:
    #        print(f'Can not to process {i["page_url"]} due to error: {e}')
    #        i["pdf_urls"] = None
    #        i["text_content"] = None
            
    #with open("../data/mod_orders.json", "w") as f:
    #    json.dump(mod_orders, f)

    #
    # Step 2. Vectorize text using lang-uk/ukr-paraphrase-multilingual-mpnet-base
    #    
    with open("../data/mod_orders_1000.json") as f:
        mod_orders = json.load(f)
    
    model = SentenceTransformer('lang-uk/ukr-paraphrase-multilingual-mpnet-base')
    for i in mod_orders:
        i["vector"] = model.encode(i["text_content"])
    
    #
    # Step 3. Import to Weaviate
    # Weaviate boilarplate: https://docs.weaviate.io/weaviate/quickstart/local
    #
    client = weaviate.connect_to_local()
    print(client.is_ready())
    
    if client.collections.exists("mod_orders_db"):
        client.collections.delete("mod_orders_db")
    
    mod_orders_db = client.collections.create(
        name="mod_orders_db",
        vector_config=wvc.config.Configure.Vectors.self_provided()
        )

    mod_orders_objs = list()
    for i, d in enumerate(mod_orders):
        mod_orders_objs.append(wvc.data.DataObject(
            properties={
            "title": d["title"],
            "page_url": d["page_url"],
            "text_content": d["text_content"],
            "pdf_urls": d["pdf_urls"],
            },
            vector=d["vector"]
            )
        )

    mod_orders_db = client.collections.use("mod_orders_db")
    mod_orders_db.data.insert_many(mod_orders_objs)
    client.close()

    #
    # Step 4. Back-up data
    #
    for i in mod_orders:
        i["vector"] = i["vector"].tolist()
    with open("../data/mod_orders.json", "w") as f:
        json.dump(mod_orders, f)

