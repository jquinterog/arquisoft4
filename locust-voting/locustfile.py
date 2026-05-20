import os
import random
import uuid

from locust import HttpUser, between, task


SEGMENTS = [item.strip() for item in os.getenv("LOCUST_SEGMENTS", "general,premium,frecuente").split(",") if item.strip()]
CHANNELS = [item.strip() for item in os.getenv("LOCUST_CHANNELS", "WEB,APP,CALL_CENTER").split(",") if item.strip()]
EVALUATE_PATH = os.getenv("LOCUST_EVALUATE_PATH", "/nba-nbo/evaluate")


class VotingEvaluateUser(HttpUser):
    wait_time = between(0.2, 1.0)

    @task
    def evaluate_request(self) -> None:
        payload = {
            "cliente_id": f"locust-{uuid.uuid4()}",
            "segmento": random.choice(SEGMENTS) if SEGMENTS else "general",
            "canal": random.choice(CHANNELS) if CHANNELS else "WEB",
        }

        with self.client.post(EVALUATE_PATH, json=payload, name="POST /nba-nbo/evaluate", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"status={response.status_code} body={response.text}")
                return

            try:
                data = response.json()
            except ValueError:
                response.failure("response is not valid JSON")
                return

            voting_meta = data.get("_voting") if isinstance(data, dict) else None
            if not isinstance(voting_meta, dict):
                response.failure("missing _voting metadata in response")
                return

            response.success()
