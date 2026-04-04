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

#Тест по этапу 1 (скорее, для нас полезно)
!pip install fastapi uvicorn requests

#Тест по этапу 1 (скорее, для нас полезно)
import threading
import uvicorn
import time
import requests

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)

server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

time.sleep(3)

BASE_URL = "http://localhost:8000"

#Тест 1: Создание заявки с высоким скорингом (850) - ожидается "Выдан"
response = requests.post(f"{BASE_URL}/apply", json={
    "client_name": "Иван Петров",
    "amount": 50000,
    "client_score": 850})
print("Тест 1 (высокий скоринг 850):", response.json())
app_id = response.json()['application_id']

#Тест 2: Получение заявки по ID
response = requests.get(f"{BASE_URL}/applications/{app_id}")
print("Тест 2 (получение заявки):", response.json())

#Тест 3: Получение договора по ID заявки
response = requests.get(f"{BASE_URL}/contracts/{app_id}")
print("Тест 3 (получение договора):", response.json())

#Тест 4: Создание заявки со средним скорингом (750) и крупной суммой - ожидается "Ручная_проверка"
response = requests.post(f"{BASE_URL}/apply", json={
    "client_name": "Мария Сидорова",
    "amount": 150000,
    "client_score": 750})
print("Тест 4 (средний скоринг 750 + крупная сумма):", response.json())

#Тест 5: Создание заявки с низким скорингом (350) - ожидается "Отказ"
response = requests.post(f"{BASE_URL}/apply", json={
    "client_name": "Алексей Иванов",
    "amount": 10000,
    "client_score": 350})
print("Тест 5 (низкий скоринг 350):", response.json())

#Тест 6: Демонстрация синхронной блокировки - 3 параллельных запроса выполняются последовательно
import threading
import time

def make_request(i):
    start = time.time()
    response = requests.post(f"{BASE_URL}/apply", json={
        "client_name": f"Клиент {i}",
        "amount": 50000,
        "client_score": 800})
    print(f"Тест 6 (запрос {i}): {time.time() - start:.2f} сек - {response.json()['status']}")

print("\nТест 6 (3 параллельных запроса - демонстрация блокировки):")
threads = []
for i in range(3):
    t = threading.Thread(target=make_request, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
