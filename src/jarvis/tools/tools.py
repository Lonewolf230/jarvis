'''
Tools for the LLM to use from
'''
from jarvis.utils.web_search import search
from jarvis.utils.store import Store
from jarvis.ingestion.embedder import embedder

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
    Use this when you want to query the user's own knowledge base which consists of obsidian vault docs and general pdf, word 
    files uploaded to this system every now and then. This might also contain stuff about user preferred answers since it is their notes

    Each result has text, file_id (a vault note path usable with read_note/write_note, or an uploaded file name),
    page_no (pdf only, else None) and slice_start/slice_end (character offsets of the chunk in the file, or in its page when page_no is set).
    '''
    store = Store()
    try:
        embedded_query = embedder.embed([user_query])[0]
        results = store.search(user_query, embedded_query, k=5)
        return results
                    
    finally:
        store.close()