"""
StreamSentinel — Locust Load Testing Benchmark Suite.

Simulates concurrent user traffic across platform REST API endpoints.
"""
import random
from locust import HttpUser, task, between


class StreamSentinelUser(HttpUser):
    wait_time = between(1, 3)

    @task(1)
    def health_check(self):
        self.client.get("/health", name="GET /health")

    @task(3)
    def list_transactions(self):
        limit = random.choice([10, 20, 50])
        self.client.get(f"/transactions?limit={limit}", name="GET /transactions")

    @task(2)
    def list_filtered_transactions(self):
        decision = random.choice(["allow", "otp", "review", "block"])
        self.client.get(f"/transactions?decision={decision}", name="GET /transactions?decision={decision}")

    @task(2)
    def list_alerts(self):
        self.client.get("/alerts", name="GET /alerts")

    @task(2)
    def analytics_summary(self):
        self.client.get("/analytics/summary", name="GET /analytics/summary")

    @task(1)
    def analytics_decisions(self):
        self.client.get("/analytics/decisions", name="GET /analytics/decisions")

    @task(1)
    def analytics_latency(self):
        self.client.get("/analytics/latency", name="GET /analytics/latency")

    @task(1)
    def list_reviews(self):
        self.client.get("/reviews", name="GET /reviews")

    @task(1)
    def metrics_scrape(self):
        self.client.get("/metrics", name="GET /metrics")
