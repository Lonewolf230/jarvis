'''
    Module will contain the embedded class that will help us embed chunks of text into vector representation using OpenAI embeddings.
    we are using weaviate so it will be both vectors (semantic search) and inverted index(searchable text).
'''
from jarvis.llm_utils import client
from jarvis.logger import setup_logger
from jarvis.settings import settings

logger=setup_logger('embedder')

EMBEDDING_MODEL = settings.EMBEDDING_MODEL

class Embedder():

    def embed(self,chunks:list)->list[float]:
        '''
            This function will embed the chunks of text into vector representation using OpenAI embeddings.
            It will return a list of vectors.
        '''
        # shortcut: one request for all chunks, API caps at 2048 inputs per call; batch above that
        try:
            response = client.embeddings.create(model=EMBEDDING_MODEL, input=chunks)
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error occurred while embedding chunks: {e}")
            raise e

embedder = Embedder()