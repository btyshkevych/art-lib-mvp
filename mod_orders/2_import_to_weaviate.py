import json
from tqdm import tqdm
import weaviate
from weaviate.classes.config import Configure


with open("mod_orders_1000.json") as f:
    mod_orders_data = json.load(f)
# Get rid of scanned documents that contains no text (less that 100 symbols)
mod_orders_data = [i for i in mod_orders_data if len(i["text_content"])>100]


# Weaviate boilarplate
# https://docs.weaviate.io/weaviate/quickstart/local
client = weaviate.connect_to_local()
print(client.is_ready())
# client.collections.delete_all()

mod_orders_db = client.collections.create(
    name="mod_orders_db",
    vector_config=Configure.Vectors.text2vec_ollama(
        api_endpoint="http://host.docker.internal:11434",
        model="nomic-embed-text",
    )
)

with mod_orders_db.batch.fixed_size(batch_size=10) as batch:
    for i in tqdm(mod_orders_data):
        batch.add_object(
            {
                "title": i["title"],
                "page_url": i["page_url"],
                "text_content": i["text_content"],
                "pdf_urls": i["pdf_urls"],
            }
        )
        if batch.number_errors > 10:
            print("Batch import stopped due to excessive errors.")
            break

failed_objects = mod_orders_db.batch.failed_objects
if failed_objects:
    print(f"Number of failed imports: {len(failed_objects)}")
    print(f"First failed object: {failed_objects[0]}")        
    
client.close()