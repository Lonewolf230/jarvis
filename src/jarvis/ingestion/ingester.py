from datetime import datetime

from jarvis.ingestion.embedder import embedder,Embedder
from jarvis.parsing.parser import parser,Parser
from jarvis.utils.store import Store

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

    def reindex(self,file_id:str,file_bytes:bytes,created_at:datetime,updated_at:datetime)->int:
        '''
            This function will replace the stored chunks of one file with a fresh parse of its bytes.
            file_id is the vault-relative path. It will return the number of chunks stored.
        '''
        chunks = self.parser.parse(file_id,file_bytes)
        vectors = self.embedder.embed(chunks) if chunks else []  # the embeddings API rejects empty input
        return self.store.upsert_file(file_id,chunks,vectors,created_at,updated_at)

