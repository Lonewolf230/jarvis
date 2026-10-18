from ingester import Ingester
from store import Store
from embedder import embedder
from llm_utils import invoke_llm

def feed_to_ingester(ingester:Ingester):
    for file_name in ["company_policy_rag_corpus/documents/annual_leave_policy.pdf",
                      "company_policy_rag_corpus/documents/acceptable_use_and_device_policy.docx",
                      "company_policy_rag_corpus/documents/annual_leave_policy_v1_superseded.txt"]:
        ingester.ingest(file_name)


def basic_rag(user_query:str):
    store = Store()
    try:
        embedded_query = embedder.embed([user_query])[0]
        results = store.search(user_query, embedded_query, k=5)
        invoked_response = invoke_llm(user_query,results)
        
        print(f"User Query: {user_query}")
        print(f"\n\nRetrieved Context: {results}")
        print(f"\n\nLLM Response: {invoked_response}")
        
    finally:
        store.close()
    
    
if __name__ == "__main__":
    basic_rag("How many days of medical leave are allowed in a year?")
    