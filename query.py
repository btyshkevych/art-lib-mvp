import sys
import weaviate
import weaviate.classes as wvc
import torch
from sentence_transformers import SentenceTransformer
from langchain_ollama import ChatOllama

def ask_llm(prompt: str, payload: str):
    """Wrapper for LLM chat"""
    messages = [(prompt),(payload)]
    ai_msg = llm.invoke(messages)
    return ai_msg

def print_bsa_results(response, summarize:bool):
    """Defines how to print bsa results in shell."""
    for index, obj in enumerate(response.objects, start=1):
        if summarize:
            text = ask_llm(prompt="Напиши короткий зміст наступного тексту на 150 слів.", payload=obj.properties["text"]).content
        else:
            text = obj.properties["text"]
        print(f'РЕЗУЛЬТАТ ПОШУКУ {index}:\nПункт: {obj.properties["number"]}\nТекст: {text}\n' )

def print_mod_orders_results(response, summarize:bool):
    """Defines how to print mod orders results in shell."""
    for index, obj in enumerate(response.objects, start=1):
        if summarize:
            text_content = ask_llm(prompt="Напиши короткий зміст наступного тексту на 250 слів.", payload=obj.properties["text_content"]).content
        else:
            text_content = obj.properties["text_content"]
        print(f'РЕЗУЛЬТАТ ПОШУКУ {index}:\nНазва: {obj.properties["title"]}\nПосилання: {obj.properties["page_url"]}\nТекст: {text_content}\n')

#TO DO: redo these functions (print_bsa_results, print_mod_orders_results) to avoid a duplication of code.

print_options = {
    "bsa_db": print_bsa_results,
    "mod_orders_db": print_mod_orders_results
    }

def search(source="bsa_db", query="", certainty=0.75, limit=1, summarize=False):
    """Search in weaviate database."""
    query_vec = model.encode(query)
    client = weaviate.connect_to_local()
    db = client.collections.use(source)

    response = db.query.near_vector(
        near_vector=query_vec,
        limit=limit,
        certainty=certainty,
        return_metadata=wvc.query.MetadataQuery(certainty=True)
        )

    print_result = print_options.get(source)
    print_result(response, summarize)

    client.close()


if __name__ == "__main__":

    model = SentenceTransformer('lang-uk/ukr-paraphrase-multilingual-mpnet-base')
    llm = ChatOllama(model="gemma3:270m",temperature=0)

    if len(sys.argv) == 6:
        search(source=sys.argv[1], query=sys.argv[2], certainty=float(sys.argv[3]), limit=int(sys.argv[4]), summarize=bool(int(sys.argv[5])))
    else:
        print("Додайте після назви файлу: [джерело пошуку: bsa_db або mod_orders_db] [термін пошуку] [релевантність від 0 до 1] [кількість результатів - число 1 і більше] [додати короткий зміст від AI - 1 або 0]\nНаприклад:\nquery.py bsa_db \"Бойовий наказ командира артилерійського дивізіону включає наступні розділи\" 0.75 5 0\n\nабо\n\nquery.py mod_orders_db \"Про передачу квартир у комунальну власність\" 0.75 5 0")

