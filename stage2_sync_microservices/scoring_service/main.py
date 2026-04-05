from fastapi import FastAPI
from pydantic import BaseModel
import time

app = FastAPI()

class ScoreRequest(BaseModel):
    client_name: str
    amount: float
    client_score: int


@app.post("/score")
def calculate_score(data: ScoreRequest):

    # имитация долгой ML модели
    time.sleep(2)

    if data.client_score > 800:
        status = "Выдан"
    elif data.client_score > 600:
        status = "Одобрено" if data.amount <= 100000 else "Ручная_проверка"
    else:
        status = "Отказ"

    return {
        "status": status
    }