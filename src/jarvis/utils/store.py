from datetime import datetime
from pathlib import Path

import weaviate
from weaviate.classes.config import Configure, DataType, Property, Tokenization
from weaviate.classes.query import Filter
from weaviate.util import generate_uuid5
from jarvis.settings import settings
from jarvis.logger import setup_logger

logger=setup_logger('store')

COLLECTION = settings.COLLECTION


class Store():

    def __init__(self):
        self.client = weaviate.connect_to_local(
            port=8080,
            host="localhost"
        )
        if not self.client.collections.exists(COLLECTION):
            # self_provided: we send our own OpenAI vectors, Weaviate does not embed
            self.client.collections.create(
                COLLECTION,
                vector_config=Configure.Vectors.self_provided(),
                properties=[
                    Property(name="text", data_type=DataType.TEXT),
                    # FIELD tokenization: filters on a path match the whole path, not shared words
                    Property(name="file_id", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
                    Property(name="file_name", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
                    Property(name="chunk_index", data_type=DataType.INT),
                    Property(name="slice_start", data_type=DataType.INT),
                    Property(name="slice_end", data_type=DataType.INT),
                    Property(name="page_no", data_type=DataType.INT),
                    Property(name="created_at", data_type=DataType.DATE),
                    Property(name="updated_at", data_type=DataType.DATE),
                ],
            )
            logger.info(f"Collection {COLLECTION} created")
        self.collection = self.client.collections.get(COLLECTION)
        # collections made before these properties existed need them added in place
        existing = {p.name for p in self.collection.config.get().properties}
        for name in ("slice_start", "slice_end", "page_no"):
            if name not in existing:
                self.collection.config.add_property(Property(name=name, data_type=DataType.INT))

    def upsert_file(self, file_id:str, chunks:list, vectors:list, created_at:datetime, updated_at:datetime)->int:
        '''
            This function will replace all chunks of one file (file_id = vault-relative path).
            Chunk ids come from file_id and position, so a retry overwrites instead of duplicating.
            Leftover chunks of a longer earlier version are deleted after the new ones are written,
            so the file is never missing from the index.
        '''
        if len(chunks) != len(vectors):
            logger.error("Chunks and vectors must be of the same length")
            raise ValueError("Chunks and vectors must be of the same length")
        with self.collection.batch.dynamic() as batch:
            for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                batch.add_object(
                    properties={
                        "text": chunk.text,
                        "file_id": file_id,
                        "file_name": Path(file_id).name,
                        "chunk_index": i,
                        "slice_start": chunk.slice_start,
                        "slice_end": chunk.slice_end,
                        # weaviate stores no null: omit the key for non-paged files
                        **({"page_no": chunk.page_no} if chunk.page_no is not None else {}),
                        "created_at": created_at,
                        "updated_at": updated_at,
                    },
                    vector=vector,
                    uuid=generate_uuid5(f"{file_id}:{i}"),
                )
        if self.collection.batch.failed_objects:
            logger.error(f"{len(self.collection.batch.failed_objects)} chunks of {file_id} failed to insert")
            raise RuntimeError(f"{len(self.collection.batch.failed_objects)} chunks of {file_id} failed to insert")
        self.collection.data.delete_many(
            where=Filter.by_property("file_id").equal(file_id)
            & Filter.by_property("chunk_index").greater_or_equal(len(chunks))
        )
        return len(chunks)

    def delete_file(self, file_id:str)->None:
        '''
            This function will delete every chunk of one file (file_id = vault-relative path).
        '''
        self.collection.data.delete_many(where=Filter.by_property("file_id").equal(file_id))

    def search(self, query:str, vector:list, k:int=5)->list:
        '''
            This function will do a hybrid search: vector similarity plus keyword match on the text.
            It will return the k best matching chunks as dicts: text, file_id, slice_start, slice_end, page_no.
        '''
        result = self.collection.query.hybrid(query=query, vector=vector, limit=k, query_properties=["text"])
        keys = ("text", "file_id", "slice_start", "slice_end", "page_no")
        return [{k: obj.properties.get(k) for k in keys} for obj in result.objects]

    def close(self):
        self.client.close()

