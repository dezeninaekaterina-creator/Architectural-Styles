# FinTech Credit Application System

## Описание проекта

Учебный проект по эволюции архитектуры FinTech-системы от монолита к событийно-ориентированной архитектуре (EDA) с API Gateway и паттерном Saga.

## Этапы проекта

### Этап 1: Монолит
- FastAPI + SQLite
- Вся логика в одном файле
- Синхронный вызов скоринга

### Этап 2: Синхронные микросервисы
- Разделение на Gateway, Scoring Service, Deal Service
- Взаимодействие через REST (HTTP)

### Этап 3: Event-Driven Architecture (EDA)
- Асинхронное взаимодействие через Redis Pub/Sub
- Заявки накапливаются в очереди при отказе сервисов

### Этап 4: EDA + Saga + API Gateway
- Агрегация данных через эндпоинт /dashboard
- Компенсирующие транзакции (Saga)
- Correlation ID для трейсинга

## Бизнес-логика

1. Клиент подаёт заявку на кредит (POST /apply)
2. Система проверяет скоринг
3. Если скоринг > 800 - одобрение и создание договора
4. Если скоринг < 800 - ручная проверка

## Технологии

- FastAPI
- Redis
- SQLite / PostgreSQL
- Docker
- Locust

## Запуск

```bash
# Запуск Redis
docker-compose up

# Запуск монолита
python stage1_monolith/main.py

# Запуск синхронных микросервисов
python stage2_sync_microservices/gateway/main.py
python stage2_sync_microservices/scoring_service/main.py
python stage2_sync_microservices/deal_service/main.py

# Нагрузочное тестирование
locust -f locustfile.py --host=http://localhost:8000