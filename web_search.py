from tavily import TavilyClient
from settings import settings

class WebSearch:
    def __init__(self):
        self.client = TavilyClient(
            api_key=settings.TAVILY_API_KEY,
        )
    
    def search(self, query:str, k:int=2)->list[dict[str,str]]:
        '''
            This function will search the web for the query and return the k best matching chunks of text.
        '''
        response = self.client.search(query=query, max_results=k,include_raw_content=True)
        results=[]
        
        for result in response["results"]:
            results.append({
                "title": result["title"],
                "url": result["url"],
                "snippet": result["content"]
            })
            
        return results

search = WebSearch()
search.search("Who is Lionel Messi?", k=2)