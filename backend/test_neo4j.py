import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
AUTH = ("neo4j", os.getenv("NEO4J_PASSWORD"))

def test_connection():
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            print("Neo4j connection successful!")

            with driver.session(database="neo4j") as session:
                result = session.run("RETURN 'Hello, Neo4j!' AS message")
                record = result.single()
                print(record["message"])
    except Exception as e:
        print(f"Neo4j connection failed: {e}")

if __name__ == "__main__":
    test_connection()
