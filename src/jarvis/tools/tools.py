'''
Tools for the LLM to use from
'''
from jarvis.guardrails import has_secret, redact
from jarvis.utils.web_search import search
from jarvis.utils.store import store
from jarvis.ingestion.embedder import embedder

def untrusted(tag:str, text:str, **attrs)->str:
    '''
        Wraps text we do not control in <tag ...>...</tag> so the model can tell data from instructions.
        Any closing tag inside the text is removed, so the text cannot end the wrapper early and escape it.
        Credentials in the text are redacted, because a tool result is saved to Postgres and re-sent on later turns.
    '''
    clean = lambda v: str(v).replace('"', "'").replace("<", "").replace(">", "")
    head = "".join(f' {k}="{clean(v)}"' for k, v in attrs.items() if v is not None)
    return f"<{tag}{head}>\n{redact(str(text)).replace(f'</{tag}>', '')}\n</{tag}>"

def web_search(query:str,k:int=3)->str:
    '''
        This function will search the web for the query and return the k best matching results from the web.
        Uses tavily API to search the web and return the results.
        
        Response chunks are in the form of a list of dictionaries with the following keys:
        - title: The title of the web page
        - url: The URL of the web page
        - snippet: A snippet of the content of the web page
    '''
    if has_secret(query):  # the query leaves for a third party; an error goes back to the model as a tool message
        raise ValueError("The query looks like it contains a secret, so it was not sent. Search without it.")
    # shortcut: tags lower the chance an injected instruction is followed, they do not stop it; upgrade with an output/query check
    return "\n".join(untrusted("web_result", r["snippet"], url=r["url"], title=r["title"]) for r in search.search(query=query, k=k))

def search_documents(user_query:str)->str:
    '''
    Use this when you want to query the user's own knowledge base which consists of obsidian vault docs and general pdf, word 
    files uploaded to this system every now and then. This might also contain stuff about user preferred answers since it is their notes

    Each result is a <document> tag whose body is the text, with attributes file_id (a vault note path usable with read_note/write_note, or an uploaded file name),
    page_no (pdf only, else missing) and slice_start/slice_end (character offsets of the chunk in the file, or in its page when page_no is set).
    '''
    try:
        embedded_query = embedder.embed([user_query])[0]
        results = store.search(user_query, embedded_query, k=5)
        return "\n".join(untrusted("document", r["text"], file_id=r["file_id"], page_no=r["page_no"],
                                    slice_start=r["slice_start"], slice_end=r["slice_end"]) for r in results)
    except Exception as e:
        return f"<document file_id='error' error='{str(e)}'>search_documents failed: {str(e)}</document>"