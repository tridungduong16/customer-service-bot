# from src.database_handler.qdrant_handler import QdrantHandler
# from qdrant_client.http.models import Distance, VectorParams

# MARKDOWN_FOLDER="./dataset/markdown_files"
# COLLECTION_NAME = "knowledgebase"



# def test_retrieve_documents(qdrant: QdrantHandler, collection_name: str):
#     """Test retrieving documents from Qdrant."""
#     print("\n=== Testing Document Retrieval ===")
    
#     try:
#         info = qdrant.client.get_collection(collection_name=collection_name)
#         print(f"Collection Info:")
#         print(f"- Name: {info.name}")
#         print(f"- Vector Size: {info.vectors_config.size}")
#         print(f"- Points Count: {info.points_count}")
#     except Exception as e:
#         print(f"Error getting collection info: {e}")
#         return

#     # Test 2: Search with a sample query
#     sample_queries = [
#         "Changpeng Zhao was born in?",
#     ]
    
#     print("\nSearch Results:")
#     for query in sample_queries:
#         print(f"\nQuery: '{query}'")
#         results = qdrant.search_similar_texts(query, limit=3)
#         if results:
#             for i, result in enumerate(results, 1):
#                 print(f"\nResult {i}:")
#                 print(f"Score: {result['score']:.4f}")
#                 print(f"Text snippet: {result['payload']['text'][:200]}...")
#                 print(f"Filename: {result['payload']['filename']}")
#         else:
#             print("No results found")

#     # Test 3: Get all documents
#     try:
#         print("\nAll Documents in Collection:")
#         scroll_response = qdrant.client.scroll(
#             collection_name=collection_name,
#             limit=10  # Limit to 10 documents for testing
#         )
#         for point in scroll_response[0]:
#             print(f"\nDocument ID: {point.id}")
#             print(f"Filename: {point.payload['filename']}")
#             print(f"Text snippet: {point.payload['text'][:100]}...")
#     except Exception as e:
#         print(f"Error retrieving all documents: {e}")

# def main():
#     qdrant = QdrantHandler()
#     qdrant.connect_to_database()
#     try:
        # import pdb; pdb.set_trace()
        # if not qdrant.connect_to_database():
        #     print("Failed to connect to Qdrant database")
        #     return
        # if qdrant.client.collection_exists(COLLECTION_NAME):
        #     qdrant.client.delete_collection(collection_name=COLLECTION_NAME)
        #     print(f"🗑️ Deleted existing collection: {COLLECTION_NAME}")

        # qdrant.client.create_collection(collection_name=COLLECTION_NAME, vectors_config=VectorParams(size=768, distance=Distance.COSINE))
        # print(f"✅ Created collection: {COLLECTION_NAME}")
        # if qdrant.insert_markdown_directory(MARKDOWN_FOLDER, COLLECTION_NAME):
        #     print("✅ Successfully processed all markdown files")
        # else:
        #     print("❌ Failed to process some markdown files")
        # test_retrieve_documents(qdrant, COLLECTION_NAME)
#     except Exception as e:
#         print(f"❌ An error occurred: {str(e)}")
#     finally:
#         qdrant.close_connection()

# if __name__ == "__main__":
#     main() 