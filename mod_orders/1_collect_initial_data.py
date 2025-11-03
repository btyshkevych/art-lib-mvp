import requests
import re
import pypdf
import io
import json
import sys
from tqdm import tqdm

def get_orders_metadata (size: int) -> list:
  """TO DO: document function. Add error handling"""
  PAYLOAD = {"sort":[{"acceptance_date":{"order":"desc"}},{"publishedAt":{"order":"desc"}}],
     "query":{"bool":{"must":[{"term":{"locale":"uk"}},{"terms_set":{"document_tags_type":{"terms":["nakazi"],"minimum_should_match_script":{"source":"1"}}}},{"term":{"type":"documents"}}]}},"_source":["title","slug","publishedAt","locale","type","id","tags","document_tags_type","document_tags_diyalnist","acceptance_date"],
     "from":0,
     "size":size}
  resp = requests.post("https://mod.gov.ua/lookup/search?search_type=dfs_query_then_fetch", json=PAYLOAD)
  resp_dct = json.loads(resp.content.decode())
  metadata = [i["_source"] for i in resp_dct["hits"]["hits"]]
  return metadata

def get_pdf_urls(slug: str) -> list:
  """TO DO: document function. Add error handling"""
  page_url = f"https://mod.gov.ua/diyalnist/normativno-pravova-baza/{slug}"
  resp = requests.get(page_url)
  pdf_urls = list(set(re.findall(r"https\:\/\/mod\.gov\.ua\/assets\/[A-z0-9_]+\.pdf", resp.content.decode())))
  return pdf_urls

def pdf_to_plain_text (url: str) -> str:
  """TO DO: document function. Add error handling"""
  response = requests.get(url)
  memory_obj = io.BytesIO(response.content)
  pdf = pypdf.PdfReader(memory_obj)
  plain_text = " ".join([pdf.pages[i].extract_text() for i in range(0, len(pdf.pages))])
  return plain_text

def clean_up_text(text: str) -> str:
  """TO DO: document function. Add error handling"""
  text = re.sub("\\n", " ", text)
  text = re.sub(r"\s+", " ", text)
  # Add more options
  return text


if __name__ == "__main__":

  if len(sys.argv) > 1:
    SAMPLE_SIZE = sys.argv[1]
  else:
    SAMPLE_SIZE = 10

  mod_orders = get_orders_metadata(SAMPLE_SIZE)

  for i in tqdm(mod_orders):
    i["page_url"] = f'https://mod.gov.ua/diyalnist/normativno-pravova-baza/{i["slug"]}'
    try:
      pdf_urls = get_pdf_urls(i["slug"])
      plain_text = map(pdf_to_plain_text, pdf_urls)
      clean_text = map(clean_up_text, list(plain_text))
      i["pdf_urls"] = pdf_urls
      i["text_content"] = (" ".join(list(clean_text)))

    except Exception as e:
      print(f'Can not to process {i["page_url"]} due to error: {e}')
      i["pdf_urls"] = None
      i["text_content"] = None

  with open("mod_orders.json", "w") as f:
    json.dump(mod_orders, f)
