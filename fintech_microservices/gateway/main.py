from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import uuid
import httpx

app = FastAPI()

SCORING_URL = "http://localhost:8001/score"
DEAL_URL = "http://localhost:8002/deal"


class Application(BaseModel):
    client_name: str
    amount: float
    client_score: int


def init_db():
    conn = sqlite3.connect("gateway.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications(
        id TEXT PRIMARY KEY,
        client_name TEXT,
        amount REAL,
        client_score INTEGER,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


@app.post("/apply")
async def create_application(app_data: Application):

    app_id = str(uuid.uuid4())

    conn = sqlite3.connect("gateway.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO applications VALUES (?, ?, ?, ?, ?)",
        (app_id, app_data.client_name, app_data.amount, app_data.client_score, "В_обработке")
    )

    conn.commit()

    # запрос к scoring сервису
    async with httpx.AsyncClient() as client:
        response = await client.post(
            SCORING_URL,
            json=app_data.dict()
        )

    status = response.json()["status"]

    cursor.execute(
        "UPDATE applications SET status=? WHERE id=?",
        (status, app_id)
    )

    # если одобрено → создаем договор
    if status in ["Одобрено", "Выдан"]:

        async with httpx.AsyncClient() as client:
            await client.post(
                DEAL_URL,
                json={
                    "application_id": app_id,
                    "amount": app_data.amount
                }
            )

    conn.commit()
    conn.close()

    return {
        "application_id": app_id,
        "status": status
    }


@app.get("/applications/{application_id}")
def get_application(application_id: str):

    conn = sqlite3.connect("gateway.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM applications WHERE id=?",
        (application_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404)

    return {
        "id": row[0],
        "client_name": row[1],
        "amount": row[2],
        "client_score": row[3],
        "status": row[4]
    }