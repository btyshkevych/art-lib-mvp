import sys
import weaviate
from langchain_ollama import ChatOllama

def ai_assist(prompt: str, payload: str):
    """TO DO: document function. Add error handling"""
    messages = [(prompt),(payload)]
    ai_msg = llm.invoke(messages)
    return ai_msg


def semantic_search(query="", limit=1, ai_assist_enabled=False):
    """TO DO: document function. Add error handling"""
    client = weaviate.connect_to_local()
    
    db = client.collections.use("bsa")
    response = db.query.near_text(
        query=query,
        certainty = 0.5,
        limit=limit
    )
    
    text_results = []
    number_results = []
    for index, obj in enumerate(response.objects, start=1):
        print(f'РЕЗУЛЬТАТ ПОШУКУ {index}:\nПункт: {obj.properties["number"]}\nТекст: {obj.properties["text"]}\n' )
        text_results.append(obj.properties["text"])
        number_results.append(obj.properties["number"])
        
    if ai_assist_enabled:
        print(f'СТВОРЮЮ ПІДСУМОК НАСТУПНИХ ПУНКТІВ БСА: {" ".join(number_results)} ...')
        summary = ai_assist(prompt="Напиши короткий зміст наступного тексту на 250 слів.", payload=". ".join(text_results))
        print(f'КОРОТКИЙ ПІДСУМОК НАСТУПНИХ ПУНКТІВ БСА: {" ".join(number_results)}:\n{summary.content}')
              
    client.close()


if __name__ == "__main__":

  llm = ChatOllama(model="llama3.2",temperature=0.15)

  if len(sys.argv) == 4:
    semantic_search(query=sys.argv[1], limit=int(sys.argv[2]), ai_assist_enabled=bool(int(sys.argv[3])))
  else:
    print("Додайте після назви файлу: [термін пошуку] [кількість результатів - число 1 і більше] [додати короткий зміст від AI - 1 або 0]\nНаприклад:\nquery_mod_orders.py закупівлі 5 0\nquery_mod_orders.py \"грошове забезпечення\" 2 1")
