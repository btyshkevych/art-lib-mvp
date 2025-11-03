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
  
  db = client.collections.use("mod_orders_db")
  response = db.query.near_text(
    query=query,
    certainty = 0.5,
    limit=limit
    )

  for index, obj in enumerate(response.objects, start=1):
    if ai_assist_enabled:
      summary = ai_assist(prompt="Напиши короткий зміст наступного тексту на 250 слів.", payload=obj.properties["text_content"])
      summary_content = f'Короткий зміст від llama3.2: {summary.content}\n'
    else:
      summary_content = ''
    
    print(f'РЕЗУЛЬТАТ ПОШУКУ {index}:\nНазва: {obj.properties["title"]}\nПосилання: {obj.properties["page_url"]}\n{summary_content}' )
  
  client.close()


if __name__ == "__main__":

  llm = ChatOllama(model="llama3.2",temperature=0.15)

  if len(sys.argv) == 4:
    semantic_search(query=sys.argv[1], limit=int(sys.argv[2]), ai_assist_enabled=bool(int(sys.argv[3])))
  else:
    print("Додайте після назви файлу: [термін пошуку] [кількість результатів - число 1 і більше] [додати короткий зміст від AI - 1 або 0]\nНаприклад:\nquery_mod_orders.py закупівлі 5 0\nquery_mod_orders.py \"грошове забезпечення\" 2 1")
