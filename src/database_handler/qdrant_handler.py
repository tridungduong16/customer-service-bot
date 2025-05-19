from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from typing import List, Optional, Dict, Any
import logging
import os
import markdown
from bs4 import BeautifulSoup
import hashlib
from src.app_config import app_config
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_community.document_compressors.rankllm_rerank import RankLLMRerank
from langchain_core.documents import Document
# from langchain.retrievers.document_compressors import FlashrankRerank
from typing import List
from sentence_transformers import SentenceTransformer
# from flashrank.reranker import FlashrankRerank
from flashrank import Ranker, RerankRequest


class QdrantHandler:
    def __init__(self):
        """Initialize Qdrant client."""
        self.client = None
        self.collection_name = app_config.QDRANT_COLLECTION_NAME
        self.vector_size = 768
        self.llm_model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True)
        self.reranker = Ranker(max_length=128)
        # self.reranker = Ranker(model_name="rank_zephyr_7b_v1_full", max_length=5000) # adjust max_length based on your passage length
        # self.reranker = FlashrankRerank(score_threshold = 0.8, top_n=3, model="ms-marco-MiniLM-L-12-v2")
        # self.reranker = Ranker(model_name="rank-T5-flan")



        # Initialize FlashrankRerank with proper configuration
        # self.reranker = FlashrankRerank(
        #     model="ms-marco-MiniLM-L-6-v2",  # Use a pre-trained model
        #     top_n=3  # Number of documents to rerank
        # )
        # self.reranker.model_rebuild()  # Rebuild the model with the new configuration

    def get_embedding(self, text: str) -> List[float]:
        return self.llm_model.encode(text).tolist()

    def connect_to_database(self):
        """Establish connection to Qdrant database."""
        try:
            # import pdb; pdb.set_trace()
            self.client = QdrantClient(
                url=app_config.QDRANT_URL,
                api_key=app_config.QDRANT_API_KEY,
                prefer_grpc=False
            )
            # import pdb; pdb.set_trace()
            logging.info("✅ Qdrant connection established")
            return True
        except Exception as e:
            logging.error(f"❌ Qdrant connection error: {e}")
            self.client = None
            return False

    def create_collection(self, collection_name: Optional[str] = None):
        """Create a new collection in Qdrant."""
        if not self.client:
            logging.error("❌ No Qdrant connection")
            return False

        try:
            collection = collection_name or self.collection_name
            self.client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            logging.info(f"✅ Collection '{collection}' created successfully")
            return True
        except Exception as e:
            logging.error(f"❌ Error creating collection: {e}")
            return False

    def read_markdown_file(self, file_path: str) -> str:
        """Read and parse markdown file content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # Convert markdown to HTML
                html = markdown.markdown(content)
                # Extract text from HTML
                soup = BeautifulSoup(html, 'html.parser')
                return soup.get_text()
        except Exception as e:
            logging.error(f"❌ Error reading file {file_path}: {e}")
            return ""

    # def get_next_doc_id(self, collection_name: Optional[str] = None) -> int:
    #     """Get the next available document ID by checking collection size."""
    #     if not self.client:
    #         return 1  # Start from 1 if no connection
    #     try:
    #         # import pdb; pdb.set_trace()
    #         collection = collection_name or self.collection_name
    #         info = self.client.get_collection(collection_name=collection)
    #         return info.points_count + 1
    #     except Exception as e:
    #         logging.error(f"❌ Error getting collection size: {e}")
    #         return 1

    def generate_doc_id(self, filename: str) -> int:
        """Generate a document ID from filename hash."""
        # Create a hash of the filename
        hash_object = hashlib.md5(filename.encode())
        # Convert hash to integer and take modulo to get a reasonable size
        return int(hash_object.hexdigest(), 16) % 1000000

    def process_markdown_directory(self, directory_path: str, collection_name: Optional[str] = None) -> List[Dict]:
        """Process all markdown files in a directory."""
        points = []
        # next_id = self.get_next_doc_id(collection_name)
        
        for filename in os.listdir(directory_path):
            if filename.endswith('.md'):
                file_path = os.path.join(directory_path, filename)
                content = self.read_markdown_file(file_path)
                if content:
                    doc_id = self.generate_doc_id(filename)
                    points.append({
                        "id": doc_id,
                        "vector": None,  # Will be set by save_text_to_qdrant
                        "payload": {
                            "text": content,
                            "filename": filename,
                            "file_path": file_path
                        }
                    })
        # import pdb; pdb.set_trace()
        return points

    def insert_markdown_directory(self, directory_path: str, collection_name: Optional[str] = None) -> bool:
        """
        Process and insert all markdown files from a directory into Qdrant.
        
        Args:
            directory_path: Path to directory containing markdown files
            collection_name: Collection to insert into. If None, uses default from config.
            
        Returns:
            bool: True if all files were processed successfully, False otherwise
        """
        if not self.client:
            logging.error("❌ No Qdrant connection")
            return False

        if not os.path.exists(directory_path):
            logging.error(f"❌ Directory {directory_path} does not exist")
            return False

        try:
            points = self.process_markdown_directory(directory_path, collection_name)
            logging.info(f"✅ Found {len(points)} markdown files to process")
            import pdb; pdb.set_trace()
            success = True
            for point in points:
                if not self.save_text_to_qdrant(
                    id=point["id"],
                    text=point["payload"]["text"],
                    metadata={
                        "filename": point["payload"]["filename"],
                        "file_path": point["payload"]["file_path"]
                    },
                    collection_name=collection_name
                ):
                    success = False
                    logging.error(f"❌ Failed to insert document: {point['payload']['filename']}")
                else:
                    logging.info(f"✅ Successfully inserted document: {point['payload']['filename']}")

            return success
        except Exception as e:
            logging.error(f"❌ Error processing markdown directory: {e}")
            return False

    def insert_vectors(self, points: List[Dict[str, Any]], collection_name: Optional[str] = None) -> bool:
        if not self.client:
            logging.error("❌ No Qdrant connection")
            return False

        try:
            collection = collection_name or self.collection_name
            self.client.upsert(
                collection_name=collection,
                points=points
            )
            logging.info(f"✅ Successfully inserted {len(points)} vectors")
            return True
        except Exception as e:
            logging.error(f"❌ Error inserting vectors: {e}")
            return False

    def search_vectors(self, query_vector: List[float], limit: int = 10,
                       collection_name: Optional[str] = None,
                       score_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        if not self.client:
            logging.error("❌ No Qdrant connection")
            return []

        try:
            collection = collection_name or self.collection_name
            search_params = {}
            if score_threshold is not None:
                search_params["score_threshold"] = score_threshold

            results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=limit,
                **search_params
            )

            return [{
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            } for result in results]

        except Exception as e:
            logging.error(f"❌ Error searching vectors: {e}")
            return []

    def delete_vectors(self, point_ids: List[int], collection_name: Optional[str] = None) -> bool:
        if not self.client:
            logging.error("❌ No Qdrant connection")
            return False

        try:
            collection = collection_name or self.collection_name
            self.client.delete(
                collection_name=collection,
                points_selector=models.PointIdsList(points=point_ids)
            )
            logging.info(f"✅ Successfully deleted {len(point_ids)} vectors")
            return True
        except Exception as e:
            logging.error(f"❌ Error deleting vectors: {e}")
            return False

    def get_collection_info(self, collection_name: Optional[str] = None) -> Dict[str, Any]:
        if not self.client:
            logging.error("❌ No Qdrant connection")
            return {}

        try:
            collection = collection_name or self.collection_name
            info = self.client.get_collection(collection_name=collection)
            return {
                "name": info.name,
                "vector_size": info.vectors_config.size,
                "distance": info.vectors_config.distance,
                "points_count": info.points_count
            }
        except Exception as e:
            logging.error(f"❌ Error getting collection info: {e}")
            return {}

    def save_text_to_qdrant(self, id: int, text: str, metadata: dict = {}, collection_name: Optional[str] = None) -> bool:
        """Embed the text and store it in Qdrant."""
        vector = self.get_embedding(text)
        return self.insert_vectors([{
            "id": id,
            "vector": vector,
            "payload": {
                "text": text,
                **metadata
            }
        }], collection_name)

    def search_similar_texts(self, query: str, limit: int = 7) -> List[Dict[str, Any]]:
        """
        Search Qdrant for texts similar to the input query and rerank them using a reranker.

        Args:
            query (str): The user query for similarity search.
            limit (int): Number of initial candidates to retrieve. Default is 7.

        Returns:
            List[Dict[str, Any]]: Reranked list of documents with score, id, payload, and text.
        """
        # Step 1: Embed the query
        query_vector = self.get_embedding(query)

        # Step 2: Search vector DB
        results = self.search_vectors(query_vector=query_vector, limit=limit)
        if not results:
            return []

        # Step 3: Format results into reranker-friendly format
        passages = [
            {
                "id": str(doc["id"]),
                "text": doc["payload"]["text"],
                "meta": {k: v for k, v in doc["payload"].items() if k != "text"}
            }
            for doc in results
        ]

        # Step 4: Run reranking
        # import pdb; pdb.set_trace()
        rerank_request = RerankRequest(query=query, passages=passages)
        reranked = self.reranker.rerank(rerank_request)
        reranked = reranked[0:5]
        # import pdb; pdb.set_trace()
        for i in reranked:
            print(i.get("text"))
            print("--------------------------------")
        # import pdb; pdb.set_trace()
        # Step 5: Format output
        final_results = [
            {
                "score": item.get("score"),
                "id": item.get("id"),
                "text": item.get("text"),
                "payload": item.get("meta", {})
            }
            for item in reranked
        ]
        return final_results


    def close_connection(self):
        if self.client:
            self.client.close()
            self.client = None
            logging.info("🔒 Qdrant connection closed")
        else:
            logging.info("ℹ️ No active Qdrant connection to close")

    def __del__(self):
        self.close_connection()
