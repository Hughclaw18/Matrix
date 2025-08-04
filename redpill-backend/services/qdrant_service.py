from qdrant_client import QdrantClient, models
from config.constants import QDRANT_COLLECTION_NAME
from utils.common import get_qdrant_config

class QdrantService:
    def __init__(self):
        config = get_qdrant_config()
        self.client = QdrantClient(host=config["host"], port=config["port"], api_key=config["api_key"])
        self.collection_name = QDRANT_COLLECTION_NAME

    def create_collection(self, vector_size: int, distance_metric: models.Distance = models.Distance.COSINE):
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=distance_metric),
        )

    async def upsert_vectors(self, ids: list, vectors: list, payloads: list):
        await self.client.upsert_points(
            collection_name=self.collection_name,
            points=models.Batch(ids=ids, vectors=vectors, payloads=payloads),
        )

    def search_vectors(self, query_vector: list, limit: int = 5):
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
        )