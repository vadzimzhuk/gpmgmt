from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from typing import List, Dict

app = FastAPI()

# Enable CORS for all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "workflows.db"

@app.get("/workflows", response_model=List[Dict])
def get_workflows():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Adjust the table/columns as needed for your schema
    cursor.execute("SELECT id, name, description, context, steps, created_at, updated_at, status FROM workflow_entities")
    # cursor.execute("SELECT * FROM workflow_entities")
    rows = cursor.fetchall()
    print(rows)
    conn.close()
    workflows = [
        {"name": row[1], "description": row[2], "context": row[3], "steps": row[4], "creation_date": row[5], "update_date": row[6], "status": row[7]} for row in rows
    ]
    return workflows

# To run: uvicorn db-web-server:app --reload --port 8000
