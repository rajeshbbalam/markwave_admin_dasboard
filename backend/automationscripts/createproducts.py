import json
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
ENV_PATH = BACKEND_DIR / ".env"
load_dotenv(ENV_PATH)

if not os.getenv("NEO4J_URI"):
    raise RuntimeError("NEO4J_URI is missing. Ensure backend/.env is correctly configured.")
if not os.getenv("NEO4J_PASSWORD"):
    raise RuntimeError("NEO4J_PASSWORD is missing. Ensure backend/.env is correctly configured.")

URI = os.getenv("NEO4J_URI")
AUTH = ("neo4j", os.getenv("NEO4J_PASSWORD"))


PRODUCTS_JSON_PATH = BASE_DIR / "products.json"


def get_driver():
    return GraphDatabase.driver(URI, auth=AUTH)


def load_products(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"products.json not found at: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("products.json must contain a list of products")

    return data


def main():
    products = load_products(PRODUCTS_JSON_PATH)

    driver = get_driver()
    try:
        with driver.session() as session:
            session.run(
                """
                CREATE CONSTRAINT product_id_unique IF NOT EXISTS
                FOR (p:PRODUCT)
                REQUIRE p.id IS UNIQUE
                """
            )

            result = session.run(
                """
                UNWIND $products AS product
                MERGE (p:PRODUCT:BUFFALO {id: product.id})
                SET p.breed = product.breed,
                    p.age = product.age,
                    p.milkYield = product.milkYield,
                    p.price = product.price,
                    p.inStock = product.inStock,
                    p.insurance = product.insurance,
                    p.buffalo_images = product.buffalo_images,
                    p.description = product.description
                RETURN count(p) AS nodes_upserted
                """,
                products=products,
            )

            record = result.single()
            upserted = record["nodes_upserted"] if record else 0
            print(f"Upserted {upserted} PRODUCT:BUFFALO nodes into Neo4j.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
