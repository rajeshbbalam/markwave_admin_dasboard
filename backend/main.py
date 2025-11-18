import os
import random
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class UserVerify(BaseModel):
    mobile: str
    device_id: str
    device_model: str

class Purchase(BaseModel):
    User_mobile: str
    item: str  # e.g., 'buffalo'
    details: str

@app.post("/Users/")
async def create_User(User: UserCreate):
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run(
                "MERGE (u:User {mobile: $mobile}) "
                "SET u.name = $name, u.referral_type = $referral_type, u.verified = $verified",
                mobile=User.mobile, name=User.name, referral_type=User.referral_type, verified=User.verified
            )
        return {"message": "User created or updated"}
    finally:
        driver.close()

@app.get("/Users/referrals")
async def get_new_referrals():
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("MATCH (u:User {referral_type: 'new_referral'}) RETURN u.mobile, u.name, u.verified")
            Users = [{"mobile": record["u.mobile"], "name": record["u.name"], "verified": record["u.verified"]} for record in result]
        return Users
    finally:
        driver.close()

@app.get("/Users/customers")
async def get_existing_customers():
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("MATCH (u:User {referral_type: 'existing_customer'}) RETURN u.mobile, u.name, u.verified")
            Users = [{"mobile": record["u.mobile"], "name": record["u.name"], "verified": record["u.verified"]} for record in result]
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
                "MATCH (u:User {mobile: $mobile}) RETURN u.referral_type AS type, u.verified AS verified",
                mobile=user.mobile
            )
            record = result.single()
            if record and record["type"] == "new_referral" and not record["verified"]:
                # Generate OTP
                otp = str(random.randint(100000, 999999))
                # Update with device info and verified
                session.run(
                    "MATCH (u:User {mobile: $mobile}) SET u.device_id = $device_id, u.device_model = $device_model, u.verified = true",
                    mobile=user.mobile, device_id=user.device_id, device_model=user.device_model
                )
                return {"status": "success", "otp": otp, "message": "User verified and device info stored"}
            else:
                return {"status": "error", "message": "User not found, not a new referral, or already verified"}
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
