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
    allow_origins=["http://localhost:3000"],  # React dev server
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

def get_driver():
    return GraphDatabase.driver(URI, auth=AUTH)

@app.on_event("shutdown")
def close_driver():
    # Note: Since driver is created per request, we don't close globally
    pass

class UserCreate(BaseModel):
    mobile: str
    name: str
    referral_type: str  # 'new_referral' or 'existing_customer'
    verified: bool = False

class UserUpdate(BaseModel):
    name: Optional[str] = None
    referral_type: Optional[str] = None
    verified: Optional[bool] = None
    email: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    occupation: Optional[str] = None
    income_level: Optional[str] = None
    family_size: Optional[int] = None
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
                    "message": "User already exists",
                    "user": existing_props
                }

            # Create or update user, assigning a stable unique id on first creation
            result = session.run(
                "MERGE (u:User {mobile: $mobile}) "
                "ON CREATE SET u.id = randomUUID() "
                "SET u.name = $name, u.referral_type = $referral_type, u.verified = $verified "
                "RETURN u.id AS id, u.mobile AS mobile, u.name AS name, u.referral_type AS referral_type, u.verified AS verified",
                mobile=User.mobile,
                name=User.name,
                referral_type=User.referral_type,
                verified=User.verified,
            )
            record = result.single()
            return {
                "message": "User created or updated",
                "user": {
                    "id": record["id"],
                    "mobile": record["mobile"],
                    "name": record["name"],
                    "referral_type": record["referral_type"],
                    "verified": record["verified"],
                },
            }
    finally:
        driver.close()

@app.put("/users/{mobile}")
async def update_user(mobile: str, user_update: UserUpdate):
    driver = get_driver()
    try:
        with driver.session() as session:
            # Check if user exists
            result = session.run("MATCH (u:User {mobile: $mobile}) RETURN u", mobile=mobile)
            user = result.single()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Build dynamic SET clause based on provided fields
            set_clauses = []
            params = {"mobile": mobile}
            
            # Handle standard fields
            if user_update.name is not None:
                set_clauses.append("u.name = $name")
                params["name"] = user_update.name
            
            if user_update.referral_type is not None:
                set_clauses.append("u.referral_type = $referral_type")
                params["referral_type"] = user_update.referral_type
            
            if user_update.verified is not None:
                set_clauses.append("u.verified = $verified")
                params["verified"] = user_update.verified
            
            # Handle new fields
            if user_update.email is not None:
                set_clauses.append("u.email = $email")
                params["email"] = user_update.email
            
            if user_update.address is not None:
                set_clauses.append("u.address = $address")
                params["address"] = user_update.address
            
            if user_update.phone is not None:
                set_clauses.append("u.phone = $phone")
                params["phone"] = user_update.phone
            
            if user_update.city is not None:
                set_clauses.append("u.city = $city")
                params["city"] = user_update.city
            
            if user_update.state is not None:
                set_clauses.append("u.state = $state")
                params["state"] = user_update.state
            
            if user_update.pincode is not None:
                set_clauses.append("u.pincode = $pincode")
                params["pincode"] = user_update.pincode
            
            if user_update.occupation is not None:
                set_clauses.append("u.occupation = $occupation")
                params["occupation"] = user_update.occupation
            
            if user_update.income_level is not None:
                set_clauses.append("u.income_level = $income_level")
                params["income_level"] = user_update.income_level
            
            if user_update.family_size is not None:
                set_clauses.append("u.family_size = $family_size")
                params["family_size"] = user_update.family_size
            
            # Handle custom dynamic fields
            if user_update.custom_fields:
                for key, value in user_update.custom_fields.items():
                    # Sanitize key name for Neo4j
                    safe_key = key.replace(" ", "_").replace("-", "_")
                    set_clauses.append(f"u.{safe_key} = ${safe_key}")
                    params[safe_key] = value
            
            if set_clauses:
                query = f"MATCH (u:User {{mobile: $mobile}}) SET {', '.join(set_clauses)} RETURN u"
                result = session.run(query, **params)
                updated = result.single()["u"] if result.single() else None
                updated_data = dict(updated) if updated is not None else None
            else:
                updated_data = None

            return {"message": "User updated successfully", "updated_fields": len(set_clauses), "user": updated_data}
    finally:
        driver.close()


@app.put("/users/id/{user_id}")
async def update_user_by_id(user_id: str, user_update: UserUpdate):
    """Update user using generated unique id instead of mobile."""
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("MATCH (u:User {id: $id}) RETURN u", id=user_id)
            user = result.single()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            set_clauses = []
            params = {"id": user_id}

            if user_update.name is not None:
                set_clauses.append("u.name = $name")
                params["name"] = user_update.name

            if user_update.referral_type is not None:
                set_clauses.append("u.referral_type = $referral_type")
                params["referral_type"] = user_update.referral_type

            if user_update.verified is not None:
                set_clauses.append("u.verified = $verified")
                params["verified"] = user_update.verified

            if user_update.email is not None:
                set_clauses.append("u.email = $email")
                params["email"] = user_update.email

            if user_update.address is not None:
                set_clauses.append("u.address = $address")
                params["address"] = user_update.address

            if user_update.phone is not None:
                set_clauses.append("u.phone = $phone")
                params["phone"] = user_update.phone

            if user_update.city is not None:
                set_clauses.append("u.city = $city")
                params["city"] = user_update.city

            if user_update.state is not None:
                set_clauses.append("u.state = $state")
                params["state"] = user_update.state

            if user_update.pincode is not None:
                set_clauses.append("u.pincode = $pincode")
                params["pincode"] = user_update.pincode

            if user_update.occupation is not None:
                set_clauses.append("u.occupation = $occupation")
                params["occupation"] = user_update.occupation

            if user_update.income_level is not None:
                set_clauses.append("u.income_level = $income_level")
                params["income_level"] = user_update.income_level

            if user_update.family_size is not None:
                set_clauses.append("u.family_size = $family_size")
                params["family_size"] = user_update.family_size

            if user_update.custom_fields:
                for key, value in user_update.custom_fields.items():
                    safe_key = key.replace(" ", "_").replace("-", "_")
                    set_clauses.append(f"u.{safe_key} = ${safe_key}")
                    params[safe_key] = value

            if set_clauses:
                query = f"MATCH (u:User {{id: $id}}) SET {', '.join(set_clauses)} RETURN u"
                result = session.run(query, **params)
                updated = result.single()["u"] if result.single() else None
                updated_data = dict(updated) if updated is not None else None
            else:
                updated_data = None

            return {"message": "User updated successfully", "updated_fields": len(set_clauses), "user": updated_data}
    finally:
        driver.close()

@app.get("/users/{mobile}")
async def get_user_details(mobile: str):
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("MATCH (u:User {mobile: $mobile}) RETURN u", mobile=mobile)
            user_record = result.single()
            
            if not user_record:
                raise HTTPException(status_code=404, detail="User not found")
            
            user_node = user_record["u"]
            user_data = dict(user_node)
            
            return user_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        driver.close()


@app.get("/users/id/{user_id}")
async def get_user_details_by_id(user_id: str):
    """Fetch full user details using generated unique id instead of mobile."""
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("MATCH (u:User {id: $id}) RETURN u", id=user_id)
            user_record = result.single()

            if not user_record:
                raise HTTPException(status_code=404, detail="User not found")

            user_node = user_record["u"]
            user_data = dict(user_node)

            return user_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        driver.close()


@app.get("/users/referrals")
async def get_new_referrals():
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("MATCH (u:User {referral_type: 'new_referral'}) RETURN u.id, u.mobile, u.name, u.verified")
            Users = [
                {
                    "id": record["u.id"],
                    "mobile": record["u.mobile"],
                    "name": record["u.name"],
                    "verified": record["u.verified"],
                }
                for record in result
            ]
        return Users
    finally:
        driver.close()


@app.get("/users/customers")
async def get_existing_customers():
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("MATCH (u:User {referral_type: 'existing_customer'}) RETURN u.id, u.mobile, u.name, u.verified")
            Users = [
                {
                    "id": record["u.id"],
                    "mobile": record["u.mobile"],
                    "name": record["u.name"],
                    "verified": record["u.verified"],
                }
                for record in result
            ]
        return Users
    finally:
        driver.close()

@app.post("/users/verify")
async def verify_user(user: UserVerify):
    driver = get_driver()
    try:
        with driver.session() as session:
            # Check if user exists and is new_referral and not verified
            result = session.run(
                "MATCH (u:User {mobile: $mobile}) RETURN u.referral_type AS type, u.verified AS verified, properties(u) AS user_props",
                mobile=user.mobile
            )
            record = result.single()
            if record["verified"]:
                return {"statuscode":200,"status": "success", "message": "User is already verified", "user": record["user_props"]}
            elif record and record["type"] == "new_referral":
                # Generate OTP
                otp = str(random.randint(100000, 999999))
                # Update with device info and verified
                session.run(
                    "MATCH (u:User {mobile: $mobile}) SET u.device_id = $device_id, u.device_model = $device_model, u.verified = true",
                    mobile=user.mobile, device_id=user.device_id, device_model=user.device_model
                )
                return {"statuscode":200,"status": "success", "otp": otp, "message": "User verified and device info stored"}
            else:
                return {"statuscode":300,"status": "error", "message": "User not found, not a new referral"}
    finally:
        driver.close()

@app.post("/purchases/")
async def create_purchase(purchase: Purchase):
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run(
                "MATCH (u:User {mobile: $User_mobile}) "
                "CREATE (u)-[:PURCHASED {item: $item, details: $details}]->(p:Purchase {id: randomUUID()})",
                User_mobile=purchase.User_mobile, item=purchase.item, details=purchase.details
            )
        return {"message": "Purchase recorded"}
    finally:
        driver.close()
