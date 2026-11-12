from datetime import datetime, timezone
from pathlib import Path

from jarvis.ingestion.embedder import embedder,Embedder
from jarvis.parsing.parser import parser,Parser
from jarvis.utils.store import Store

class Ingester():
    def __init__(self,store:Store):
        self.parser = parser or Parser()
        self.store = store
        self.embedder = embedder or Embedder()
        
    def ingest(self,file_name:str)->int:
        '''
            This function will ingest an uploaded file from disk. It is stored under file_id "uploads/<name>"
            so it cannot collide with a vault note, and uploading the same name again replaces the old chunks.
            It will return the number of chunks ingested.
        '''
        path = Path(file_name)
        st = path.stat()
        to_utc = lambda t: datetime.fromtimestamp(t, tz=timezone.utc)
        return self.reindex(f"uploads/{path.name}", path.read_bytes(), to_utc(getattr(st, "st_birthtime", st.st_mtime)), to_utc(st.st_mtime))

    def reindex(self,file_id:str,file_bytes:bytes,created_at:datetime,updated_at:datetime)->int:
        '''
            This function will replace the stored chunks of one file with a fresh parse of its bytes.
            file_id is the vault-relative path. It will return the number of chunks stored.
        '''
        chunks = self.parser.parse(file_id,file_bytes)
        vectors = self.embedder.embed([c.text for c in chunks]) if chunks else []  # the embeddings API rejects empty input
        return self.store.upsert_file(file_id,chunks,vectors,created_at,updated_at)

