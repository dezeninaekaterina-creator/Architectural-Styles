from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import uuid

app = FastAPI()

class DealRequest(BaseModel):
    application_id: str
    amount: float


def init_db():
    conn = sqlite3.connect("deal.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contracts(
        id TEXT PRIMARY KEY,
        application_id TEXT,
        amount REAL,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


@app.post("/deal")
def create_deal(data: DealRequest):

    conn = sqlite3.connect("deal.db")
    cursor = conn.cursor()

    contract_id = str(uuid.uuid4())

    cursor.execute(
        "INSERT INTO contracts VALUES (?, ?, ?, ?)",
        (contract_id, data.application_id, data.amount, "Активен")
    )

    conn.commit()
    conn.close()

    return {
        "contract_id": contract_id,
        "status": "Активен"
    }


@app.get("/contracts/{application_id}")
def get_contract(application_id: str):

    conn = sqlite3.connect("deal.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM contracts WHERE application_id=?",
        (application_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"error": "not found"}

    return {
        "id": row[0],
        "application_id": row[1],
        "amount": row[2],
        "status": row[3]
    }