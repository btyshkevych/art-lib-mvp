import sys
import os
import weaviate
import weaviate.classes as wvc
import torch
from sentence_transformers import SentenceTransformer
from langchain.agents import create_agent
from dotenv import load_dotenv

TEMPLATES = {
    "bsa_db": [("Пункт №", "number"), ("Текст", "text_content")],
    "mod_orders_db": [("Назва", "title"),("Посилання", "page_url"),("Знайдений фрагмент тексту", "text_content_chunk")]
    }

def ask_llm(prompt: str, payload: str):
    """Wrapper for LLM chat"""
    messages = {"messages": [{"role": "user", "content": f"{prompt}: {payload}"}]}
    ai_msg = agent.invoke(messages)
    return ai_msg

def print_results(response, template:list[tuple], summarize: bool):
    """Defines how to print bsa results in command line."""
    results = []
    for index, obj in enumerate(response.objects, start=1):
        res = [f'{i[0]}: {obj.properties[i[1]]}\n' for i in template]
        if summarize:
            summary = ask_llm(prompt="Напиши короткий зміст наступного тексту на 100 слів.", payload=obj.properties["text_content"])
            res = res[:-1]
            res.append(f'Короткий зміст документу: {summary["messages"][1].content}\n')
        results.append(f'РЕЗУЛЬТАТ ПОШУКУ {index}:\n{"".join(res)}')
    print("\n\n".join(results))


def query(source="bsa_db", query="", certainty=0.75, limit=1, summarize=False):
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

    print_results(response=response, template=TEMPLATES[source], summarize=summarize)
    client.close()


if __name__ == "__main__":

    load_dotenv()
    os.getenv("OPENAI_API_KEY")
    model = SentenceTransformer('lang-uk/ukr-paraphrase-multilingual-mpnet-base')
    
    agent = create_agent(
        model="gpt-5-nano",
        system_prompt="You are a helpful assistant"
        )

    if len(sys.argv) == 6:
        query(source=sys.argv[1], query=sys.argv[2], certainty=float(sys.argv[3]), limit=int(sys.argv[4]), summarize=bool(int(sys.argv[5])))
    else:
        print("Додайте після назви файлу: [джерело пошуку: bsa_db або mod_orders_db] [термін пошуку] [релевантність від 0 до 1] [кількість результатів - число 1 і більше] [додати короткий зміст від AI - 1 або 0]\nНаприклад:\nquery.py bsa_db \"Бойовий наказ командира артилерійського дивізіону включає наступні розділи\" 0.75 5 0\n\nабо\n\nquery.py mod_orders_db \"Про передачу квартир у комунальну власність\" 0.75 5 0")

