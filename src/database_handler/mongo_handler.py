from pymongo import MongoClient
from typing import Optional, List, Dict, Any
import logging
import datetime
import atexit
from src.app_config import app_config
from src.schema.celeb import (
    ConversationInfor,
    UserThread,
    Message,
)


class BaseMongoDBHandler:
    def __init__(self, db_name: str, collection_name: str):
        """Initialize MongoDB connection."""
        self.client = None
        self.db = None
        self.collection = None
        self.db_name = db_name
        self.collection_name = collection_name
        atexit.register(self.close_connection)

    def connect_to_database(self):
        """Establish a connection to MongoDB."""
        try:
            if not all([app_config.MONGODB_URI, self.db_name, self.collection_name]):
                raise ValueError(
                    "❌ MongoDB credentials are missing. Check your configuration."
                )

            if not self.client:
                self.client = MongoClient(app_config.MONGODB_URI)
                self.db = self.client[self.db_name]
                self.collection = self.db[self.collection_name]
                print("✅ MongoDB connection established.")

        except Exception as e:
            print(f"❌ MongoDB connection error: {e}")
            self.close_connection()

    def insert_one(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a single document into MongoDB."""
        if not self.collection:
            return {"status": "error", "message": "No database connection"}

        try:
            result = self.collection.insert_one(data)
            inserted_doc = self.collection.find_one({"_id": result.inserted_id})
            print("✅ Document inserted successfully.")
            return {
                "status": "success",
                "message": "Document inserted successfully",
                "data": inserted_doc,
            }
        except Exception as e:
            print(f"❌ Error inserting document: {e}")
            return {"status": "error", "message": str(e)}

    def insert_many(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Insert multiple documents into MongoDB."""
        if not self.collection:
            return {"status": "error", "message": "No database connection"}

        try:
            result = self.collection.insert_many(data_list)
            print(f"✅ {len(result.inserted_ids)} documents inserted successfully.")
            return {
                "status": "success",
                "message": f"{len(result.inserted_ids)} documents inserted successfully",
                "inserted_ids": result.inserted_ids,
            }
        except Exception as e:
            print(f"❌ Error inserting documents: {e}")
            return {"status": "error", "message": str(e)}

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document in MongoDB."""
        if not self.collection:
            return None

        try:
            document = self.collection.find_one(query)
            return document
        except Exception as e:
            print(f"❌ Error finding document: {e}")
            return None

    def find_many(self, query: Dict[str, Any], limit: int = 0) -> List[Dict[str, Any]]:
        """Find multiple documents in MongoDB."""
        # import pdb; pdb.set_trace()
        # if not self.collection:
        #     return []
        # import pdb; pdb.set_trace()

        try:
            cursor = self.collection.find(query)
            if limit > 0:
                cursor = cursor.limit(limit)
            return list(cursor)
        except Exception as e:
            print(f"❌ Error finding documents: {e}")
            return []

    def update_one(
        self, query: Dict[str, Any], update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a single document in MongoDB."""
        if not self.collection:
            return {"status": "error", "message": "No database connection"}

        try:
            result = self.collection.update_one(query, {"$set": update_data})
            if result.modified_count > 0:
                print("✅ Document updated successfully.")
                return {
                    "status": "success",
                    "message": "Document updated successfully",
                    "modified_count": result.modified_count,
                }
            else:
                print("ℹ️ No document was updated.")
                return {
                    "status": "info",
                    "message": "No document was updated",
                    "modified_count": 0,
                }
        except Exception as e:
            print(f"❌ Error updating document: {e}")
            return {"status": "error", "message": str(e)}

    def delete_one(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a single document from MongoDB."""
        if not self.collection:
            return {"status": "error", "message": "No database connection"}

        try:
            result = self.collection.delete_one(query)
            if result.deleted_count > 0:
                print("✅ Document deleted successfully.")
                return {
                    "status": "success",
                    "message": "Document deleted successfully",
                    "deleted_count": result.deleted_count,
                }
            else:
                print("ℹ️ No document was deleted.")
                return {
                    "status": "info",
                    "message": "No document was deleted",
                    "deleted_count": 0,
                }
        except Exception as e:
            print(f"❌ Error deleting document: {e}")
            return {"status": "error", "message": str(e)}

    def delete_many(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Delete multiple documents from MongoDB."""
        if not self.collection:
            return {"status": "error", "message": "No database connection"}

        try:
            result = self.collection.delete_many(query)
            print(f"✅ {result.deleted_count} documents deleted successfully.")
            return {
                "status": "success",
                "message": f"{result.deleted_count} documents deleted successfully",
                "deleted_count": result.deleted_count,
            }
        except Exception as e:
            print(f"❌ Error deleting documents: {e}")
            return {"status": "error", "message": str(e)}

    def close_connection(self):
        """Close the MongoDB connection."""
        try:
            if self.client:
                self.client.close()
                self.client = None
                self.db = None
                self.collection = None
                print("🔒 MongoDB connection closed.")
        except Exception as e:
            print(f"⚠️ Error closing MongoDB connection: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.connect_to_database()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_connection()


class MemoryHandler(BaseMongoDBHandler):
    def __init__(self, db_name: str, collection_name: str):
        super().__init__(db_name, collection_name)

    def clear_collection(self):
        """Clear all documents from the collection."""
        self.collection.delete_many({})
        print(f"Collection '{self.collection.name}' cleared.")

    def clear_conversation(self, thread_infor: UserThread):
        """Clear a specific conversation."""
        result = self.collection.delete_one(
            {"user_id": thread_infor.user_id, "thread_id": thread_infor.thread_id}
        )
        if result.deleted_count > 0:
            print(
                f"Conversation for user_id '{thread_infor.user_id}' and thread_id '{thread_infor.thread_id}' cleared."
            )
            return True
        else:
            print(
                f"No conversation found for user_id '{thread_infor.user_id}' and thread_id '{thread_infor.thread_id}'."
            )
            return False

    def insert_or_update_conversation(self, conversation_infor: ConversationInfor):
        if not conversation_infor.messages:
            print("No messages provided. Skipping update.")
            return

        messages_as_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation_infor.messages
        ]

        result = self.collection.update_one(
            {
                "user_id": conversation_infor.user_thread_infor.user_id,
                "thread_id": conversation_infor.user_thread_infor.thread_id,
                "agent_name": conversation_infor.user_thread_infor.agent_name,
            },
            {
                "$setOnInsert": {
                    "user_id": conversation_infor.user_thread_infor.user_id,
                    "thread_id": conversation_infor.user_thread_infor.thread_id,
                    "agent_name": conversation_infor.user_thread_infor.agent_name,
                    "created_at": datetime.datetime.utcnow(),
                },
                "$push": {
                    "messages": {
                        "$each": messages_as_dicts,
                        # "$slice": -50,  # Keeps only the last 50 messages
                    }
                },
            },
            upsert=True,
        )

        if result.upserted_id:
            print("New conversation inserted.")
        else:
            print("Conversation updated, keeping only the last 50 messages.")

    def retrieve_conversation(self, thread_infor: UserThread) -> ConversationInfor:
        conversation = self.collection.find_one(
            {
                "user_id": thread_infor.user_id,
                "thread_id": thread_infor.thread_id,
                "agent_name": thread_infor.agent_name,
            }
        )
        if conversation:
            conversation["_id"] = str(conversation["_id"])  # Convert ObjectId to string
            return conversation
        print(
            f"No conversation found for user_id '{thread_infor.user_id}' and thread_id '{thread_infor.thread_id}'."
        )
        return {}

    def format_conversation(self, conversation: Dict) -> str:
        """Format the last two messages of a conversation."""
        if "messages" not in conversation or not isinstance(
            conversation["messages"], list
        ):
            raise ValueError(
                "Invalid conversation format. Must contain a 'messages' list."
            )

        try:
            last_message = conversation["messages"][-2:]
            formatted_messages = "\n".join(
                f"{message['role'].capitalize()}: {message['content']}"
                for message in last_message
            )
            return formatted_messages
        except KeyError as e:
            raise ValueError(f"Malformed message data. Missing key: {e}")


class MongoDBHandler(BaseMongoDBHandler):
    def __init__(self, db_name: str = None, collection_name: str = None):
        db_name = db_name or app_config.MONGODB_DB_NAME
        collection_name = collection_name or app_config.MONGODB_COLLECTION_NAME
        super().__init__(db_name, collection_name)



def main():
    # Initialize the memory handler with configured DB and collection
    # import pdb; pdb.set_trace()
    handler = MemoryHandler(
        db_name=app_config.MONGODB_DB_NAME,
        collection_name=app_config.MONGODB_COLLECTION_NAME
    )
    
    # Connect to MongoDB
    handler.connect_to_database()

    # Retrieve all conversations
    conversations = handler.find_many(query={})  # No filter = get all
    print(f"Total conversations retrieved: {len(conversations)}")

    for idx, conv in enumerate(conversations, start=1):
        conv_id = conv.get("_id", "N/A")
        user_id = conv.get("user_id", "N/A")
        thread_id = conv.get("thread_id", "N/A")
        agent_name = conv.get("agent_name", "N/A")
        messages = conv.get("messages", [])
        created_at = conv.get("created_at", "N/A")


        if True:

        # if agent_name == 'MISS CHINA AI':
            with open(f"conversation.txt", "a") as f:
                f.write(f"\n----------------------------- Conversation #{idx} -----------------------------\n")
                f.write(f"- ID: {conv_id}\n")
                f.write(f"- User ID: {user_id}\n")
                f.write(f"- Thread ID: {thread_id}\n")
                f.write(f"- Agent Name: {agent_name}\n")
                f.write(f"- Total Messages: {len(messages)}\n")
                f.write(f"- Created At: {created_at}\n")
                for message in messages[-50:]:  # Show last 3 messages
                    f.write(f"- {message.get('role', '').capitalize()}: {message.get('content', '')}\n")

    handler.close_connection()

if __name__ == "__main__":
    main()
