# Markwave Users Dashboard

Backend API for managing buffalo cart users via referrals. Built with FastAPI and Neo4j.

## Features

- Create users via referral (mobile number and name)
- Maintain referral types: new_referral or existing_customer
- Record purchases
- API endpoints for new referrals and existing customers

## Setup

### Prerequisites

- Python 3.8+
- Neo4j database running locally (default: neo4j://localhost:7687, user: neo4j, password: password)

### Backend Setup

1. cd backend
2. pip install -r requirements.txt
3. Update Neo4j credentials in main.py if needed
4. uvicorn main:app --reload

## API Endpoints

- POST /users/ : Create or update user
- GET /users/referrals : Get new referrals
- GET /users/customers : Get existing customers
- POST /purchases/ : Record purchase

## Neo4j Schema

- User node: {mobile, name, referral_type}
- Purchase node: {id} with relationship PURCHASED from User
