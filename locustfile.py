from locust import HttpUser, task, between
import random

class FinTechUser(HttpUser):
    wait_time = between(0.5, 2)
    
    @task
    def apply_credit(self):
        score = random.choice([850, 750, 650, 350])
        amount = random.randint(10000, 200000)
        
        self.client.post("/apply", json={
            "client_name": f"User_{random.randint(1, 1000)}",
            "amount": amount,
            "client_score": score
        })