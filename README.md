# Markwave Users Dashboard

A full-stack application for managing buffalo cart users via referrals. Backend built with FastAPI and Neo4j, frontend with React.

## Features

- Create users via referral (mobile number and name)
- Maintain referral types: new_referral or existing_customer
- Record purchases
- Dashboard with tabs for new referrals and existing customers

## Setup

### Prerequisites

- Python 3.8+
- Node.js 14+
- Neo4j database running locally (default: neo4j://localhost:7687, user: neo4j, password: password)

### Backend Setup

1. cd backend
2. pip install -r requirements.txt
3. Update Neo4j credentials in main.py if needed
4. uvicorn main:app --reload

### Frontend Setup

1. cd frontend
2. npm install
3. npm start

## API Endpoints

- POST /users/ : Create or update user
- GET /users/referrals : Get new referrals
- GET /users/customers : Get existing customers
- POST /purchases/ : Record purchase

## Neo4j Schema

- User node: {mobile, name, referral_type}
- Purchase node: {id} with relationship PURCHASED from User
