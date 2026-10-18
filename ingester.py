from embedder import embedder,Embedder
from parser import parser,Parser
from store import Store

class Ingester():
    def __init__(self,store:Store):
        self.parser = parser or Parser()
        self.store = store
        self.embedder = embedder or Embedder()
        
    def ingest(self,file_name:str):
        '''
            This function will ingest the file and store the chunks and their vectors into the weaviate database.
            It will return the number of chunks ingested.
        '''
        with open(file_name,'rb') as f:
            file_bytes = f.read()
        chunks = self.parser.parse(file_name,file_bytes)
        vectors = self.embedder.embed(chunks)
        return self.store.insert(chunks,vectors)
    
