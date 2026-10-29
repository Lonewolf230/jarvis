'''
Tools for the LLM to use from
'''
from web_search import search
from store import Store
from embedder import embedder

def web_search(query:str,k:int=3)->list[dict[str,str]]:
    '''
        This function will search the web for the query and return the k best matching results from the web.
        Uses tavily API to search the web and return the results.
        
        Response chunks are in the form of a list of dictionaries with the following keys:
        - title: The title of the web page
        - url: The URL of the web page
        - snippet: A snippet of the content of the web page
    '''
    return search.search(query=query, k=k)

def search_documents(user_query:str)->list[dict[str,str]]:
    '''
    This is something that searches Northstar works internal documents for relevant information for a user query.
    This function will use a basic RAG (Retrieval-Augmented Generation) approach to answer the user's query.
    It will search the store for relevant information for a user query from our internal sources.
    
    '''
    store = Store()
    try:
        embedded_query = embedder.embed([user_query])[0]
        results = store.search(user_query, embedded_query, k=5)
        return results
                    
    finally:
        store.close()