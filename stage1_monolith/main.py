#Основной код
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import uuid

app = FastAPI()

class Application(BaseModel):
    client_name: str
    amount: float
    client_score: int

#Инициализация БД
def init_db():
    conn = sqlite3.connect('monolith.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY,
            client_name TEXT NOT NULL,
            amount REAL NOT NULL,
            client_score INTEGER NOT NULL,
            status TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS contracts (
            id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

def scoring_logic(client_score: int, amount: float) -> str:
    import time
    time.sleep(2)

    if client_score > 800:
        return "Выдан"
    elif client_score > 600:
        return "Одобрено" if amount <= 100000 else "Ручная_проверка"
    else:
        return "Отказ"

#ЭНДПОИНТ 1: POST /apply - создание заявки и вызов скоринга
@app.post("/apply")
def create_application(app_data: Application):
    app_id = str(uuid.uuid4())
    conn = sqlite3.connect('monolith.db')
    cursor = conn.cursor()

    cursor.execute("INSERT INTO applications (id, client_name, amount, client_score, status) VALUES (?, ?, ?, ?, ?)",
        (app_id, app_data.client_name, app_data.amount, app_data.client_score, "В_обработке"))
    conn.commit()

    #Синхронный вызов скоринга внутри процесса
    status = scoring_logic(app_data.client_score, app_data.amount)

    cursor.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))

    if status == "Одобрено" or status == "Выдан":
        contract_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO contracts (id, application_id, amount, status) VALUES (?, ?, ?, ?)",
            (contract_id, app_id, app_data.amount, "Активен"))

    conn.commit()
    conn.close()

    return {"status": status, "application_id": app_id}

#ЭНДПОИНТ 2: GET /applications/{application_id} - получение статуса заявки
@app.get("/applications/{application_id}")
def get_application(application_id: str):
    conn = sqlite3.connect('monolith.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM applications WHERE id = ?", (application_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    return {"id": row[0],
        "client_name": row[1],
        "amount": row[2],
        "client_score": row[3],
        "status": row[4]}

#ЭНДПОИНТ 3: GET /contracts/{application_id} - получение договора по заявке
@app.get("/contracts/{application_id}")
def get_contract(application_id: str):
    conn = sqlite3.connect('monolith.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM contracts WHERE application_id = ?", (application_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Договор не найден")

    return {"id": row[0],
        "application_id": row[1],
        "amount": row[2],
        "status": row[3]}

