import os
import random
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from neo4j import GraphDatabase
from pydantic import BaseModel
import datetime
from neo4j.time import Date

# Load environment variables from backend/.env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

# Validate Neo4j environment variables
if not os.getenv("NEO4J_URI"):
    raise RuntimeError("NEO4J_URI is missing. Ensure backend/.env is correctly configured.")
if not os.getenv("NEO4J_PASSWORD"):
    raise RuntimeError("NEO4J_PASSWORD is missing. Ensure backend/.env is correctly configured.")

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR, html=True), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main frontend page"""
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return f.read()
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Markwave Admin Dashboard</title>
        <style>
            body { font-family: sans-serif; margin: 2rem; }
            h1 { color: #333; }
            a { color: #007bff; text-decoration: none; }
        </style>
    </head>
    <body>
        <h1>Markwave Admin Dashboard</h1>
        <p>FastAPI backend is running.</p>
        <p><a href="/docs">API Documentation (Swagger UI)</a></p>
        <p><a href="/health">Health Check</a></p>
    </body>
    </html>
    """

@app.get("/favicon.ico")
async def favicon():
    """Return a minimal favicon to avoid 404s"""
    return FileResponse("static/favicon.ico") if os.path.exists("static/favicon.ico") else {"status": "no favicon"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Neo4j connection
URI = os.getenv("NEO4J_URI")
AUTH = ("neo4j", os.getenv("NEO4J_PASSWORD"))

def build_update_clauses(user_update: UserUpdate) -> tuple[list, dict]:
    set_clauses = []
    params = {}

    # Standard fields
    if user_update.name is not None:
        set_clauses.append("u.name = $name")
        params["name"] = user_update.name
    if user_update.email is not None:
        set_clauses.append("u.email = $email")
        params["email"] = user_update.email
        set_clauses.append("u.verified = true")
        set_clauses.append("u.isFormFilled = true")
    if user_update.first_name is not None:
        set_clauses.append("u.first_name = $first_name")
        params["first_name"] = user_update.first_name
    if user_update.last_name is not None:
        set_clauses.append("u.last_name = $last_name")
        params["last_name"] = user_update.last_name
    if user_update.gender is not None:
        set_clauses.append("u.gender = $gender")
        params["gender"] = user_update.gender
    if user_update.occupation is not None:
        set_clauses.append("u.occupation = $occupation")
        params["occupation"] = user_update.occupation
    if user_update.dob is not None:
        try:
            dob_date = datetime.datetime.strptime(user_update.dob, '%m-%d-%Y').date()
            set_clauses.append("u.dob = $dob")
            params["dob"] = dob_date
        except ValueError:
            # Invalid date format, skip or handle
            pass
    if user_update.address is not None:
        set_clauses.append("u.address = $address")
        params["address"] = user_update.address
    if user_update.city is not None:
        set_clauses.append("u.city = $city")
        params["city"] = user_update.city
    if user_update.state is not None:
        set_clauses.append("u.state = $state")
        params["state"] = user_update.state
    if user_update.aadhar_number is not None:
        set_clauses.append("u.aadhar_number = $aadhar_number")
        params["aadhar_number"] = user_update.aadhar_number
    if user_update.pincode is not None:
        set_clauses.append("u.pincode = $pincode")
        params["pincode"] = user_update.pincode
    if user_update.aadhar_front_image_url is not None:
        set_clauses.append("u.aadhar_front_image_url = $aadhar_front_image_url")
        params["aadhar_front_image_url"] = user_update.aadhar_front_image_url
    if user_update.aadhar_back_image_url is not None:
        set_clauses.append("u.aadhar_back_image_url = $aadhar_back_image_url")
        params["aadhar_back_image_url"] = user_update.aadhar_back_image_url
    if user_update.verified is not None:
        set_clauses.append("u.verified = $verified")
        params["verified"] = user_update.verified
    # Custom fields
    if user_update.custom_fields:
        for key, value in user_update.custom_fields.items():
            safe_key = key.replace(" ", "_").replace("-", "_")
            set_clauses.append(f"u.{safe_key} = ${safe_key}")
            params[safe_key] = value

    return set_clauses, params

def get_driver():
    return GraphDatabase.driver(URI, auth=AUTH)


class UserCreate(BaseModel):
    mobile: str
    first_name: str
    last_name: str
    refered_by_mobile: str  
    refered_by_name: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    referral_type: Optional[str] = None
    verified: Optional[bool] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    dob: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    aadhar_number: Optional[int] = None
    pincode: Optional[str] = None
    income_level: Optional[str] = None
    family_size: Optional[int] = None
    aadhar_front_image_url: Optional[str] = None
    aadhar_back_image_url: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None

class UserVerify(BaseModel):
    mobile: str
    device_id: str
    device_model: str

class Purchase(BaseModel):
    User_mobile: str
    item: str  # e.g., 'buffalo'
    details: str


@app.post("/users/")
async def create_User(User: UserCreate):
    try:
        driver = get_driver()
        try:
            with driver.session() as session:
                # Check if user already exists
                existing = session.run(
                    "MATCH (u:User {mobile: $mobile}) RETURN u",
                    mobile=User.mobile
                ).single()

                if existing:
                    existing_props = dict(existing["u"])
                    return {
                        "statuscode": 200,
                        "status": "success",
                        "message": "User already exists",
                        "user": existing_props
                    }

                # Create or update user, assigning a stable unique id on first creation
                result = session.run(
                    "MERGE (u:User {mobile: $mobile}) "
                    "ON CREATE SET u.id = randomUUID() "
                    "SET u.first_name = $first_name,u.last_name = $last_name,u.mobile = $mobile,u.refered_by_mobile = $refered_by_mobile,u.refered_by_name = $refered_by_name "
                    "RETURN u.id AS id, u.mobile AS mobile, u.first_name AS first_name, u.last_name AS last_name,u.refered_by_mobile AS refered_by_mobile,u.refered_by_name AS refered_by_name",
                    mobile=User.mobile,
                    first_name=User.first_name,
                    last_name=User.last_name,
                    refered_by_mobile=User.refered_by_mobile,
                    refered_by_name=User.refered_by_name
                )
                record = result.single()
                return {
                    "statuscode": 201,
                    "status": "success",
                    "message": "User created or updated",
                    "user": {
                        "id": record["id"],
                        "mobile": record["mobile"],
                        "first_name": record["first_name"],
                        "last_name": record["last_name"],
                        "refered_by_mobile": record["refered_by_mobile"],
                        "refered_by_name": record["refered_by_name"],
                    },
                }
        finally:
            driver.close()
    except Exception as e:
        return {"statuscode": 500, "status": "error", "message": str(e)}

@app.put("/users/{mobile}")
async def update_user(mobile: str, user_update: UserUpdate):
    try:
        driver = get_driver()
        try:
            with driver.session() as session:
                # Check if user exists
                result = session.run("MATCH (u:User {mobile: $mobile}) RETURN u", mobile=mobile)
                user = result.single()
                
                if not user:
                    return {"statuscode": 404, "status": "error", "message": "User not found"}
                
                set_clauses, params = build_update_clauses(user_update)
                params["mobile"] = mobile
                
                if set_clauses:
                    query = f"MATCH (u:User {{mobile: $mobile}}) SET {', '.join(set_clauses)} RETURN u"
                    result = session.run(query, **params)
                    updated = result.single()["u"] if result.single() else None
                    updated_data = dict(updated) if updated is not None else None
                else:
                    updated_data = None
               
                return {"statuscode": 200, "status": "success", "message": "User updated successfully", "updated_fields": len(set_clauses), "user": updated_data}
        finally:
            driver.close()
    except Exception as e:
        return {"statuscode": 500, "status": "error", "message": str(e)}


@app.put("/users/id/{user_id}")
async def update_user_by_id(user_id: str, user_update: UserUpdate):
    try:
        driver = get_driver()
        try:
            with driver.session() as session:
                result = session.run("MATCH (u:User {id: $id}) RETURN u", id=user_id)
                user = result.single()

                if not user:
                    return {"statuscode": 404, "status": "error", "message": "User not found"}

                set_clauses, params = build_update_clauses(user_update)
                params["id"] = user_id

                if set_clauses:
                    query = f"MATCH (u:User {{id: $id}}) SET {', '.join(set_clauses)} RETURN u"
                    result = session.run(query, **params)
                    record = result.single()
                    updated = record["u"] if record else None
                    updated_data = dict(updated) if updated is not None else None
                    # Convert dob to dd-mm-yyyy string if present
                    if updated_data and 'dob' in updated_data:
                       dob = updated_data['dob']
                       if isinstance(dob, datetime.date):
                            updated_data['dob'] = dob.strftime('%d-%m-%Y')
                       elif isinstance(dob, Date):
                            updated_data['dob'] = f"{dob.day:02d}-{dob.month:02d}-{dob.year}"
                else:
                    updated_data = None

                return {"statuscode": 200, "status": "success", "message": "User updated successfully", "updated_fields": len(set_clauses), "user": updated_data}
        finally:
            driver.close()
    except Exception as e:
        return {"statuscode": 500, "status": "error", "message": str(e)}

@app.get("/users/referrals")
async def get_new_referrals():
    try:
        driver = get_driver()
        try:
            with driver.session() as session:
                result = session.run("MATCH (u:User {verified: false}) RETURN u.id, u.mobile, u.name, u.verified")
                Users = [
                    {
                        "id": record["u.id"],
                        "mobile": record["u.mobile"],
                        "name": record["u.name"],
                        "verified": record["u.verified"],
                    }
                    for record in result
                ]
            return {"statuscode": 200, "status": "success", "users": Users}
        finally:
            driver.close()
    except Exception as e:
        return {"statuscode": 500, "status": "error", "message": str(e)}


@app.get("/users/customers")
async def get_existing_customers():
    try:
        driver = get_driver()
        try:
            with driver.session() as session:
                result = session.run("MATCH (u:User {verified:true}) RETURN u")
                Users = [dict(record["u"]) for record in result]
            return {"statuscode": 200, "status": "success", "users": Users}
        finally:
            driver.close()
    except Exception as e:
        return {"statuscode": 500, "status": "error", "message": str(e)}


@app.get("/users/{mobile}")
async def get_user_details(mobile: str):
    try:
        driver = get_driver()
        try:
            with driver.session() as session:
                result = session.run("MATCH (u:User {mobile: $mobile}) RETURN u", mobile=mobile)
                user_record = result.single()
                
                if not user_record:
                    return {"statuscode": 404, "status": "error", "message": "User not found"}
                
                user_node = user_record["u"]
                user_data = dict(user_node)
                
                return {"statuscode": 200, "status": "success", "user": user_data}
        finally:
            driver.close()
    except Exception as e:
        return {"statuscode": 500, "status": "error", "message": str(e)}


@app.get("/users/id/{user_id}")
async def get_user_details_by_id(user_id: str):
    """Fetch full user details using generated unique id instead of mobile."""
    try:
        driver = get_driver()
        try:
            with driver.session() as session:
                result = session.run("MATCH (u:User {id: $id}) RETURN u", id=user_id)
                user_record = result.single()

                if not user_record:
                    return {"statuscode": 404, "status": "error", "message": "User not found"}

                user_node = user_record["u"]
                user_data = dict(user_node)
                # Convert dob to dd-mm-yyyy string if present
                if 'dob' in user_data:
                    dob = user_data['dob']
                    if isinstance(dob, datetime.date):
                        user_data['dob'] = dob.strftime('%d-%m-%Y')
                    elif isinstance(dob, Date):
                        user_data['dob'] = f"{dob.day:02d}-{dob.month:02d}-{dob.year}"

                return {"statuscode": 200, "status": "success", "user": user_data}
        finally:
            driver.close()
    except Exception as e:
        return {"statuscode": 500, "status": "error", "message": str(e)}


@app.get("/products/{product_id}")
async def get_product_details(product_id: str):
    """Return product details for a given product id. Currently returns a static sample for Murrah buffalo.
    The `product_id` path parameter is returned in the payload's `id` field.
    """
    # Static product sample — replace with DB lookup if needed later
    product = {
        "id": product_id if product_id else "MURRAH-001",
        "breed": "Murrah Buffalo",
        "age": 3,
        "milkYield": 12,
        "price": 175000,
        "inStock": True,
        "insurance": 13000,
        "buffalo_images": [
            "https://storage.googleapis.com/markwave-kart/img1.jpeg",
            "https://storage.googleapis.com/markwave-kart/img2.jpeg",
            "https://storage.googleapis.com/markwave-kart/img3.jpeg",
            "https://storage.googleapis.com/markwave-kart/img4.jpeg",
        ],
        "description": (
            "The Murrah is a premium dairy buffalo known for its jet-black coat, strong build, "
            "and curved horns. It is famous for high milk yield, rich fat content, and excellent "
            "adaptability to different climates."
        ),
    }

    return product


@app.get("/products")
async def get_products():
    """Return all buffalo products stored in Neo4j as PRODUCT:BUFFALO nodes."""
    try:
        driver = get_driver()
        try:
            with driver.session() as session:
                result = session.run("MATCH (p:PRODUCT:BUFFALO) RETURN p")
                products = [dict(record["p"]) for record in result]
            return {"statuscode": 200, "status": "success", "products": products}
        finally:
            driver.close()
    except Exception as e:
        return {"statuscode": 500, "status": "error", "message": str(e)}


@app.post("/users/verify")
async def verify_user(user: UserVerify):
    try:
        driver = get_driver()
        try:
            with driver.session() as session:
                # Check if user exists and is new_referral and not verified
                result = session.run(
                    "MATCH (u:User {mobile: $mobile}) RETURN u.referral_type AS type, u.verified AS verified, properties(u) AS user_props",
                    mobile=user.mobile
                )
                record = result.single()
                if not record:
                    return {"statuscode": 300, "status": "error", "message": "User not found"}
                if record["verified"]:
                    user_props = dict(record["user_props"])
                    # Convert dob to dd-mm-yyyy string if present
                    if 'dob' in user_props:
                        dob = user_props['dob']
                        if isinstance(dob, datetime.date):
                            user_props['dob'] = dob.strftime('%d-%m-%Y')
                        elif isinstance(dob, Date):
                            user_props['dob'] = f"{dob.day:02d}-{dob.month:02d}-{dob.year}"
                    return {"statuscode": 200, "status": "success", "message": "User already verified", "user": user_props}
                elif record and record["type"] == "new_referral":
                    # Generate OTP
                    otp = str(random.randint(100000, 999999))
                    # Update with device info and verified
                    session.run(
                        "MATCH (u:User {mobile: $mobile}) SET u.device_id = $device_id, u.device_model = $device_model",
                        mobile=user.mobile, device_id=user.device_id, device_model=user.device_model
                    )
                    user_props = dict(record["user_props"])
                    # Convert dob to dd-mm-yyyy string if present
                    if 'dob' in user_props:
                        dob = user_props['dob']
                        if isinstance(dob, datetime.date):
                            user_props['dob'] = dob.strftime('%d-%m-%Y')
                        elif isinstance(dob, Date):
                            user_props['dob'] = f"{dob.day:02d}-{dob.month:02d}-{dob.year}"
                    return {"statuscode": 200, "status": "success", "message": "New user verified", "otp": otp, "user": user_props}
                else:
                    return {"statuscode": 300, "status": "error", "message": "User not a new referral"}
        finally:
            driver.close()
    except Exception as e:
        return {"statuscode": 500, "status": "error", "message": str(e)}

@app.post("/purchases/")
async def create_purchase(purchase: Purchase):
    try:
        driver = get_driver()
        try:
            with driver.session() as session:
                session.run(
                    "MATCH (u:User {mobile: $User_mobile}) "
                    "CREATE (u)-[:PURCHASED {item: $item, details: $details}]->(p:Purchase {id: randomUUID()})",
                    User_mobile=purchase.User_mobile, item=purchase.item, details=purchase.details
                )
            return {"statuscode": 200, "status": "success", "message": "Purchase recorded"}
        finally:
            driver.close()
    except Exception as e:
        return {"statuscode": 500, "status": "error", "message": str(e)}

# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.getenv("PORT", 8000))
#     uvicorn.run("main:app", host="0.0.0.0", port=port)