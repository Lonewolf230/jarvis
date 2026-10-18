import weaviate
from weaviate.classes.config import Configure, DataType, Property

from logger import setup_logger

logger=setup_logger('store')

COLLECTION = "Jarvis"


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
                properties=[Property(name="text", data_type=DataType.TEXT)],
            )
            logger.info(f"Collection {COLLECTION} created")
        self.collection = self.client.collections.get(COLLECTION)

    def insert(self, chunks:list, vectors:list)->int:
        '''
            This function will insert the chunks and their vectors into the weaviate database.
            It will return the number of chunks inserted.
        '''
        if len(chunks) != len(vectors):
            logger.error("Chunks and vectors must be of the same length")
            raise ValueError("Chunks and vectors must be of the same length")
        logger.info(f"Inserting {len(chunks)} chunks into the database")
        with self.collection.batch.dynamic() as batch:
            for chunk, vector in zip(chunks, vectors, strict=True):
                batch.add_object(properties={"text": chunk}, vector=vector)
        if self.collection.batch.failed_objects:
            logger.error(f"{len(self.collection.batch.failed_objects)} objects failed to insert")
            raise RuntimeError(f"{len(self.collection.batch.failed_objects)} objects failed to insert")
        return len(chunks)

    def search(self, query:str, vector:list, k:int=5)->list:
        '''
            This function will do a hybrid search: vector similarity plus keyword match on the text.
            It will return the k best matching chunks of text.
        '''
        result = self.collection.query.hybrid(query=query, vector=vector, limit=k)
        return [obj.properties["text"] for obj in result.objects]

    def close(self):
        self.client.close()

