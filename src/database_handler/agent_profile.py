import mysql.connector
import json
import os
from src.app_config import app_config
from src.schema.celeb import AgentProfile
import logging
from typing import Optional, List


class AgentProfileDatabaseHandler:
    def __init__(self):
        """Initialize database connection."""
        self.connection = None
        # self.connect_to_database()

    def connect_to_database(self):
        """Establish a connection to the MySQL database."""
        try:
            if not all(
                [
                    app_config.DB_NAME,
                    app_config.DB_USER,
                    app_config.DB_PASS,
                    app_config.DB_HOST,
                ]
            ):
                raise ValueError(
                    "Database credentials are missing. Check your configuration."
                )

            # import pdb; pdb.set_trace()
            self.connection = mysql.connector.connect(
                host=app_config.DB_HOST,
                port=22653,
                user=app_config.DB_USER,
                password=app_config.DB_PASS,
                database=app_config.DB_NAME,
            )
            # import pdb; pdb.set_trace()

            print("Database connection established.")

        except mysql.connector.Error as e:
            print(f"Database connection error: {e}")
            self.connection = None

    def execute_query(self, query, values=None):
        """Execute a query with optional values."""
        if not self.connection:
            print("No database connection. Query execution failed.")
            return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, values or ())
                self.connection.commit()
                return True
        except mysql.connector.Error as e:
            print(f"MySQL Error {e.errno}: {e.msg}")
            raise  "Ensure the error is propagated so `insert_from_dict` can catch it"

    def insert_from_dict(self, table_name, data_dict):
        if not data_dict:
            print("❌ Data dictionary is empty. Insert failed.")
            return {"status": "error", "message": "Data dictionary is empty."}
        try:
            flatten_data_dict = self.flatten_agent_profile(data_dict)
            columns = list(flatten_data_dict.keys())
            values = list(flatten_data_dict.values())
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(values))})"

            # Use cursor.lastrowid to get the auto-generated id and fetch the created record
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, tuple(values))
                self.connection.commit()
                agent_id = cursor.lastrowid

                # Fetch the created record to get createdAt
                fetch_query = f"SELECT id, createdAt FROM {table_name} WHERE id = %s"
                cursor.execute(fetch_query, (agent_id,))
                created_record = cursor.fetchone()

            print("✅ Insert successful.")
            # Return the original data_dict along with success status, agent_id, and createdAt
            return {
                **data_dict,
                "agent_id": agent_id,
                "createdAt": created_record["createdAt"] if created_record else None,
                "status": "success",
                "message": "Agent profile inserted successfully.",
            }
        except mysql.connector.IntegrityError as e:
            if e.errno == 1062:  # Duplicate entry error
                print(f"❌ Duplicate Entry Error: {e}")
                return {
                    "status": "error",
                    "message": "Duplicate entry: This agent name already exists.",
                }
            else:
                print(f"❌ Integrity error: {e}")
                return {"status": "error", "message": f"Integrity error: {e}"}
        except mysql.connector.Error as e:
            print(f"❌ Database query error: {e}")
            return {"status": "error", "message": f"Database query error: {e}"}
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def insert_from_disk(self, table_name, json_folder_path):
        """Reads all JSON files from a folder and inserts them into the database."""
        if not os.path.exists(json_folder_path):
            print("❌ JSON folder not found.")
            return

        print("📂 Testing insert from all JSON files in the folder...")

        for file_name in os.listdir(json_folder_path):
            if file_name.endswith(".json"):
                file_path = os.path.join(json_folder_path, file_name)
                try:
                    with open(file_path, "r") as file:
                        agents_data = json.load(file)
                        self.insert_from_dict(table_name, agents_data)
                        print(f"✅ Successfully inserted data from {file_name}")

                except FileNotFoundError:
                    print(f"❌ File {file_name} not found.")
                except json.JSONDecodeError:
                    print(f"❌ Error decoding JSON file {file_name}.")
                except Exception as e:
                    print(f"❌ Unexpected error processing {file_name}: {e}")

        print("✅ All JSON files processed.")

    def show_tables(self):
        """Show all tables in the database."""
        query = "SHOW TABLES;"
        if not self.connection:
            print("❌ No database connection.")
            return
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                tables = cursor.fetchall()
                print("📋 Tables in database:")
                for table in tables:
                    print(f"  - {table[0]}")
        except mysql.connector.Error as e:
            print(f"❌ Error fetching tables: {e}")

    def drop_table(self, table_name):
        """Drop a specific table from the database."""
        query = f"DROP TABLE IF EXISTS {table_name};"
        if self.execute_query(query):
            print(f"✅ Table `{table_name}` dropped successfully.")

    def clear_table(self, table_name):
        """Clear all data from a table without dropping it."""
        query = f"TRUNCATE TABLE {table_name};"
        if self.execute_query(query):
            print(f"✅ All data removed from `{table_name}`.")

    def close_connection(self):
        """Explicitly close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            print("🔒 Database connection closed.")
        else:
            print("ℹ️ No active database connection to close.")

    @staticmethod
    def flatten_agent_profile(data):
        return {
            "agent_name": data["identity"].get("agentName", ""),
            "avatar": data["identity"].get("avatar", ""),
            "system_prompt": data["identity"].get("system", ""),
            "bio": data["identity"].get("bio", ""),
            "lore": data["identity"].get("lore", ""),
            "formal_casual": data["behavior"]["communication_style"].get(
                "formal_casual", 50
            ),
            "serious_humorous": data["behavior"]["communication_style"].get(
                "serious_humorous", 50
            ),
            "concise_detailed": data["behavior"]["communication_style"].get(
                "concise_detailed", 50
            ),
            "neutral_opinionated": data["behavior"]["communication_style"].get(
                "neutral_opinionated", 50
            ),
            "llm_model": data["knowledge"].get("llm_model", ""),
            "custom_knowledge": data["knowledge"].get("custom_knowledge", ""),
            "post_example": data["knowledge"].get("post_example", ""),
            "twitter": data["social"].get("twitter", ""),
            "discord": data["social"].get("discord", ""),
            "telegram": data["social"].get("telegram", ""),
            "website": data["social"].get("website", ""),
            "instagram": data["social"].get("instagram", ""),
            "creator_id": data["creator_id"],
            "topic": ", ".join(
                data["behavior"].get("topic", [])
            ),  # Store as a comma-separated string
            "personality_traits": ", ".join(
                data["behavior"].get("personality_traits", [])
            ),
            "rules": ", ".join(
                data.get("rules", [])
            ),  # Convert list to comma-separated string
            "token_contract": data.get("token_contract", ""),
            "popularity_score": data.get("popularity_score", ""),
            "bondingAddress": data.get("bondingAddress", ""),
            "symbol": data.get("symbol", ""),
            "symbol_name": data.get("symbol_name", ""),
        }

    @staticmethod
    def unflatten_agent_profile(row):
        return {
            "agent_id": row.get("id", ""),
            "identity": {
                "agentName": row.get("agent_name", ""),
                "avatar": row.get("avatar", ""),
                "system": row.get("system_prompt", ""),
                "bio": row.get("bio", ""),
                "lore": row.get("lore", ""),
            },
            "behavior": {
                "topic": row.get("topic", "").split(
                    ", "
                ),  # Convert CSV string back to a list
                "personality_traits": row.get("personality_traits", "").split(", "),
                "communication_style": {
                    "formal_casual": row.get("formal_casual", 50),
                    "serious_humorous": row.get("serious_humorous", 50),
                    "concise_detailed": row.get("concise_detailed", 50),
                    "neutral_opinionated": row.get("neutral_opinionated", 50),
                },
            },
            "knowledge": {
                "llm_model": row.get("llm_model", ""),
                "custom_knowledge": row.get("custom_knowledge", ""),
                "post_example": row.get("post_example", ""),
            },
            "social": {
                "twitter": row.get("twitter", ""),
                "discord": row.get("discord", ""),
                "telegram": row.get("telegram", ""),
                "website": row.get("website", ""),
                "instagram": row.get("instagram", ""),
            },
            "rules": row.get("rules", "").split(", "),
            "creator_id": row.get("creator_id", ""),
            "createdAt": row.get(
                "createdAt", None
            ),  # Include createdAt in the response
            "token_contract": row.get("token_contract", ""),
            "popularity_score": row.get("popularity_score", ""),
            "listedAt": row.get("listedAt", ""),
            "bondingAddress": row.get("bondingAddress", ""),
            "symbol": row.get("symbol", ""),
            "symbol_name": row.get("symbol_name", ""),
        }

    def run_sql_script(self, file_path):
        """Run an external SQL script from a .sql file."""
        if not os.path.exists(file_path):
            print(f"❌ SQL file '{file_path}' not found.")
            return

        try:
            with open(file_path, "r") as file:
                sql_script = file.read()

            with self.connection.cursor() as cursor:
                for statement in sql_script.split(";"):
                    statement = statement.strip()
                    if statement:
                        cursor.execute(statement)
                self.connection.commit()
                print(f"✅ Successfully executed SQL script: {file_path}")

        except mysql.connector.Error as e:
            print(f"❌ Error executing SQL script '{file_path}': {e}")

    def get_all_profiles(self, table_name):
        """Get all agent profiles from the database, sorted by popularity_score in descending order."""
        query = f"SELECT * FROM {table_name} ORDER BY popularity_score DESC;"
        if not self.connection:
            print("❌ No database connection.")
            return []

        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query)
                profiles = cursor.fetchall()
                return profiles
        except mysql.connector.Error as e:
            print(f"❌ Error fetching agent profiles: {e}")
            return []

    def return_all_agent_profiles(self, table_name) -> AgentProfile:
        db_response = self.get_all_profiles(table_name)
        # import pdb; pdb.set_trace()
        profile = [self.unflatten_agent_profile(row) for row in db_response]
        # import pdb; pdb.set_trace()
        return profile

    def get_one_agent_profile(self, table_name, value, field="agent_name"):
        """
        Get a single agent profile from the database based on agent_name or symbol.
        
        Args:
            table_name: Name of the table
            value: Value to search for (agent name or symbol)
            field: Field to search in ('agent_name' or 'symbol')
            
        Returns:
            dict: Agent profile if found, None if not found
        """
        # if field not in ["agent_name", "symbol"]:
        #     print("❌ Invalid field. Must be 'agent_name' or 'symbol'")
        #     return None
            
        query = f"SELECT * FROM {table_name} WHERE {field} = %s;"
        if not self.connection:
            print("❌ No database connection.")
            return None
        try:
            # import pdb; pdb.set_trace()
            with self.connection.cursor(dictionary=True, buffered=True) as cursor:
                cursor.execute(query, (value,))
                # import pdb; pdb.set_trace()
                profile = cursor.fetchone()
                # import pdb; pdb.set_trace()
                return profile
        except mysql.connector.Error as e:
            print(f"❌ Error fetching agent profile: {e}")
            return None

    def get_agent_profile_by_creator(self, table_name, creator_id):
        """Get agent profiles from the database based on creator_id."""
        query = f"SELECT * FROM {table_name} WHERE creator_id = %s;"
        if not self.connection:
            print("❌ No database connection.")
            return None
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (creator_id,))
                profiles = cursor.fetchall()
                if not profiles:
                    return None
                # Convert the database rows to agent profile format
                return [self.unflatten_agent_profile(profile) for profile in profiles]
        except mysql.connector.Error as e:
            print(f"❌ Error fetching agent profile by creator_id: {e}")
            return None

    def get_agent_profile_by_id(self, table_name, agent_id):
        query = f"SELECT * FROM {table_name} WHERE id = %s;"
        if not self.connection:
            print("❌ No database connection.")
            return None
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (agent_id,))
                profile = cursor.fetchone()
                if not profile:
                    print(f"❌ No profile found for agent_id: {agent_id}")
                    return None
                # Convert the database row to agent profile format
                return self.unflatten_agent_profile(profile)
        except mysql.connector.Error as e:
            print(f"❌ Error fetching agent profile by id: {e}")
            return None

    def get_agent_profile_by_name(
        self, table_name: str, agent_name: str, limit: int = 10
    ) -> List[AgentProfile]:
        agent_name = agent_name.strip()

        query = f"""
            SELECT * FROM {table_name}
            WHERE LOWER(TRIM(agent_name)) LIKE LOWER(%s)
            LIMIT %s;
        """

        if not self.connection:
            print("❌ No database connection.")
            return []

        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (f"%{agent_name}%", limit))
                rows = cursor.fetchall()
                if not rows:
                    print(f"❌ No profiles found for agent_name: {agent_name}")
                    return []
                res = [self.unflatten_agent_profile(row) for row in rows]
                return res
        except mysql.connector.Error as e:
            print(f"❌ Error fetching agent profiles by name: {e}")
            return []

    def get_total_profiles_count(self, table_name: str) -> int:
        query = f"SELECT COUNT(*) as total FROM {table_name};"
        if not self.connection:
            print("❌ No database connection.")
            return 0

        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                return result["total"] if result else 0
        except mysql.connector.Error as e:
            print(f"❌ Error getting total profiles count: {e}")
            return 0

    def get_paginated_profiles(
        self,
        table_name: str,
        limit: int = 5,
        offset: int = 0,
        topic: str = None,
        agent_name: str = None,
    ) -> tuple[list[AgentProfile], int]:
        if not self.connection:
            print("❌ No database connection.")
            return [], 0

        # Base SELECT and COUNT queries
        base_query = f"""
            SELECT * FROM {table_name}
            WHERE 
                (%s IS NULL OR topic LIKE %s)
                AND (%s IS NULL OR agent_name LIKE %s)
            ORDER BY popularity_score DESC
        """
        count_query = f"""
            SELECT COUNT(*) as total FROM {table_name}
            WHERE 
                (%s IS NULL OR topic LIKE %s)
                AND (%s IS NULL OR agent_name LIKE %s)
        """

        try:
            # Prepare search patterns
            topic_pattern = f"%{topic}%" if topic else None
            agent_pattern = f"%{agent_name}%" if agent_name else None

            # Params for both count and base query
            search_params = (topic, topic_pattern, agent_name, agent_pattern)

            # Count total
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(count_query, search_params)
                total_count = cursor.fetchone()["total"]
                total_pages = (total_count + limit - 1) // limit if limit > 0 else 1

            # Adjust query for pagination
            if limit == 0:
                # Use maximum LIMIT to support OFFSET in MySQL
                query = base_query + " LIMIT 18446744073709551615 OFFSET %s"
                query_params = search_params + (offset,)
            else:
                query = base_query + " LIMIT %s OFFSET %s"
                query_params = search_params + (limit, offset)

            # Fetch results
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, query_params)
                profiles = cursor.fetchall()

            return [
                self.unflatten_agent_profile(profile) for profile in profiles
            ], total_pages

        except mysql.connector.Error as e:
            print(f"❌ Error fetching paginated profiles: {e}")
            return [], 0

    def delete_agent_profile(self, table_name: str, agent_id: str) -> bool:
        """
        Delete an agent profile from the database.

        Args:
            table_name: Name of the table
            agent_id: ID of the agent to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            cursor = self.connection.cursor()
            query = f"DELETE FROM {table_name} WHERE id = %s"
            cursor.execute(query, (agent_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Error deleting agent profile: {str(e)}")
            raise
        finally:
            cursor.close()

    def update_token_contract(
        self,
        table_name: str,
        agent_id: int,
        token_contract: str,
        bondingAddress: str,
        symbol: str,
    ) -> Optional[AgentProfile]:
        """
        Update the token_contract, bondingAddress, and symbol fields for a specific agent and return the updated profile.
        Only updates fields that are provided and not empty.

        Args:
            table_name: Name of the table
            agent_id: ID of the agent to update (integer)
            token_contract: New token contract address (optional)
            bondingAddress: New bonding address (optional)
            symbol: New symbol (optional)

        Returns:
            Optional[AgentProfile]: Updated agent profile if successful, None if failed
        """
        if not self.connection:
            print("❌ No database connection.")
            return None

        try:
            with self.connection.cursor(dictionary=True) as cursor:
                # First check if the agent exists
                check_query = f"SELECT * FROM {table_name} WHERE id = %s"
                cursor.execute(check_query, (agent_id,))
                if not cursor.fetchone():
                    print(f"❌ No agent found with ID: {agent_id}")
                    return None

                # Build dynamic update query based on provided values
                update_fields = []
                update_values = []

                if token_contract is not None and token_contract.strip():
                    update_fields.append("token_contract = %s")
                    update_values.append(token_contract)

                if bondingAddress is not None and bondingAddress.strip():
                    update_fields.append("bondingAddress = %s")
                    update_values.append(bondingAddress)

                if symbol is not None and symbol.strip():
                    update_fields.append("symbol = %s")
                    update_values.append(symbol)

                # If no fields to update, return current profile
                if not update_fields:
                    print(f"ℹ️ No fields to update for agent {agent_id}")
                    cursor.execute(check_query, (agent_id,))
                    current_profile = cursor.fetchone()
                    return (
                        self.unflatten_agent_profile(current_profile)
                        if current_profile
                        else None
                    )

                # Add agent_id to values for WHERE clause
                update_values.append(agent_id)

                # Construct and execute the update query
                update_query = f"""
                    UPDATE {table_name} 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """

                cursor.execute(update_query, update_values)
                self.connection.commit()

                # Fetch the updated profile
                cursor.execute(check_query, (agent_id,))
                updated_profile = cursor.fetchone()
                if updated_profile:
                    print(f"✅ Successfully updated fields for agent {agent_id}")
                    return self.unflatten_agent_profile(updated_profile)
                else:
                    print(f"❌ Failed to fetch updated profile for agent {agent_id}")
                    return None

        except mysql.connector.Error as e:
            print(f"❌ Error updating fields: {e}")
            self.connection.rollback()
            return None

    def get_agent_id_by_name(self, table_name: str, agent_name: str) -> Optional[int]:
        if not self.connection:
            print("❌ No database connection.")
            return None

        try:
            with self.connection.cursor(dictionary=True) as cursor:
                query = f"SELECT id FROM {table_name} WHERE agent_name = %s"
                cursor.execute(query, (agent_name,))
                result = cursor.fetchone()
                return result["id"] if result else None
        except mysql.connector.Error as e:
            print(f"❌ Error fetching agent ID by name: {e}")
            return None

    def get_agent_name_by_id(self, table_name: str, agent_id: int) -> Optional[str]:
        """
        Get agent name from the database based on agent_id.

        Args:
            table_name: Name of the table
            agent_id: ID of the agent to search for

        Returns:
            Optional[str]: Agent name if found, None if not found
        """
        if not self.connection:
            print("❌ No database connection.")
            return None

        try:
            with self.connection.cursor(dictionary=True) as cursor:
                query = f"SELECT agent_name FROM {table_name} WHERE id = %s"
                cursor.execute(query, (agent_id,))
                result = cursor.fetchone()
                # import pdb; pdb.set_trace()
                return result["agent_name"] if result else None
        except mysql.connector.Error as e:
            print(f"❌ Error fetching agent name by ID: {e}")
            return None

    def __del__(self):
        """Close the database connection when the object is deleted."""
        self.close_connection()


# if __name__ == "__main__":
#     db_handler = AgentProfileDatabaseHandler()
#     db_handler.connect_to_database()
#     db_handler.show_tables()
#     path="/Users/tridungduong16/Documents/xeleb-agent/src/sql_script/get_all_profiles.sql"
#     db_handler.run_sql_script(path)




# db_handler.run_sql_script('/Users/tridungduong/Documents/xeleb-agent/src/sql_script/create_agent_table.sql')
# res = db_handler.run_sql_script('/Users/tridungduong/Documents/xeleb-agent/src/sql_script/get_all_profiles.sql')
# res = db_handler.return_all_agent_profiles("agent_profiles_v2")
# print(res)
# import pdb; pdb.set_trace()
# db_handler.show_tables()
# Drop a specific table (use with caution)
# db_handler.drop_table("agent_profiles")
# db_handler.show_tables()
# Clear all data from a table
# db_handler.clear_table("agent_profiles")
# Insert from disk (reads all JSON files in folder and inserts into database)
# json_folder_path = "/Users/tridungduong/Documents/xeleb-agent/dataset/agent_profile/"
# db_handler.insert_from_disk(app_config.TABLE_NAME, json_folder_path)
