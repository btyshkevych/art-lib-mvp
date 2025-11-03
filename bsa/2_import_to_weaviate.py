from tqdm import tqdm
import weaviate
from weaviate.classes.config import Configure


with open("bsa.json") as f:
    bsa_chapters = json.load(f)

# Weaviate boilarplate
# https://docs.weaviate.io/weaviate/quickstart/local
client = weaviate.connect_to_local()
print(client.is_ready())
# client.collections.delete_all()

bsa = client.collections.create(
    name="bsa",
    vector_config=Configure.Vectors.text2vec_ollama(
        api_endpoint="http://host.docker.internal:11434",
        model="nomic-embed-text",
    )
)

with bsa.batch.fixed_size(batch_size=10) as batch:
    for i in tqdm(bsa_chapters):
        batch.add_object(
            {
                "number": i["number"],
                "text": i["text"]
            }
        )
        if batch.number_errors > 10:
            print("Batch import stopped due to excessive errors.")
            break

failed_objects = bsa.batch.failed_objects
if failed_objects:
    print(f"Number of failed imports: {len(failed_objects)}")
    print(f"First failed object: {failed_objects[0]}")        
        
client.close()
