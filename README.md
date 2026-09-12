# 🛡️ StreamSentinel — Real-Time Financial Fraud Detection & Security Platform

StreamSentinel is an end-to-end, production-grade real-time financial fraud and anomaly detection platform. It unifies high-speed streaming data processing (Kafka, Redis), behavioral machine learning (XGBoost), deterministic rule-based fraud detection, explainable AI (SHAP), MongoDB persistence, automated fraud alerting & OTP verification, a full FastAPI REST platform API, Prometheus metrics & Grafana monitoring dashboards, Docker multi-service containerization, AWS EC2 deployment readiness, Locust load testing, and an interactive React operations dashboard.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/palasanivishnu/StreamSentinal-main)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fpalasanivishnu%2FStreamSentinal-main&root-directory=frontend)
[![GitHub Pages](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-brightgreen?logo=github)](https://palasanivishnu.github.io/StreamSentinal-main/)

---

## 🏗️ End-to-End System Architecture

```text
Transaction Simulator (Person A)
        ↓
Kafka Producer (Partitioned by user_id)
        ↓
Kafka Topic: transactions
        ↓
Kafka Consumer → Redis Stateful Processing (Rolling Behavior & Features)
        ↓
Feature Vector
        ↓
Detection Engine (Person B)
   ├── Deterministic Rule Engine (4 Active Rules)
   ├── XGBoost ML Classifier (Model v2.0)
   ├── Hybrid Decision Engine (ALLOW / OTP / REVIEW / BLOCK)
   └── SHAP TreeExplainer (Feature Attribution)
        ↓
Scoring Output
        ↓
Platform Subsystem (Person C)
   ├── MongoDB Storage (Transactions, Alerts, OTP Records)
   ├── Fraud Alerting & Automated 6-Digit OTP Generator
   ├── External Webhook Dispatcher (HTTP POST + HMAC Signatures)
   ├── Prometheus Metrics Instrumentation (/metrics)
   └── FastAPI REST Platform Server (18 Endpoints)
        ↓
Operations & Monitoring Console
   ├── React Operations Dashboard (7 Production Views on Port 5173)
   └── Grafana Observability Dashboard (10 Panels)
```

---

## 🚀 Key Features by Subsystem

### Person A — Data Ingestion & Stateful Processing
- **Transaction Simulator**: Real-time event replay with configurable fraud injection rates.
- **Kafka Event Stream**: High-throughput message broker partitioned by `user_id` to guarantee ordering.
- **Redis State Manager**: Calculates rolling behavioral metrics (amount-vs-average ratio, 5-minute velocity, haversine travel distance, time deltas, new merchant categories).

### Person B — Fraud Detection Engine (LOCKED Subsystem)
- **Deterministic Rule Engine**: Evaluates `HIGH_AMOUNT`, `HIGH_VELOCITY`, `IMPOSSIBLE_TRAVEL`, and `NEW_MERCHANT_CATEGORY`.
- **XGBoost ML Scoring**: Pre-trained XGBoost Classifier producing calibrated `ml_fraud_score` probabilities.
- **Hybrid Decision Engine**: Integrates ML score and rule violations into calibrated decision outcomes (`ALLOW`, `OTP`, `REVIEW`, `BLOCK`).
- **Explainable AI (SHAP)**: Generates human-readable feature impact attributions for every decision.

### Person C — Platform & Security Layer
- **FastAPI REST API**: 18 endpoints for transactions, alerts, user search, review approval/blocking, OTP verification, analytics, and metrics.
- **Prometheus Observability**: 13 metric counters, histograms, and gauges exposing application telemetry at `GET /metrics`.
- **Grafana Dashboards**: 10-panel dashboard tracking TPS, latency percentiles (P50/P95/P99), decision distribution, and alert severity.
- **Automated Alerts & Webhook**: Auto-dispatches security alerts (`CRITICAL`, `HIGH`, `WARNING`) and HMAC-signed webhook HTTP POST notifications.
- **Automated OTP & Review Workflow**: Auto-triggers 5-minute 6-digit OTP challenges for `REVIEW`/`OTP` decisions and updates transaction state on verification.
- **React Operations Console**: Production 7-page dashboard (`http://localhost:5173`) featuring Command Center, Live Transactions explorer, Alert Center, Review Queue, OTP portal, Analytics, and Detection Engine guide.
- **Docker Containerization**: Multi-service `docker-compose.yml` stack (FastAPI, MongoDB, Prometheus, Grafana, Redis, Kafka, Zookeeper).
- **AWS EC2 Deployment Support**: Automated setup and zero-downtime deployment scripts (`deploy/setup.sh`, `deploy/deploy.sh`).
- **Locust Load Testing**: Benchmark performance testing scripts (`load_testing/locustfile.py`).

---

## 📁 Repository Structure

```text
StreamSentinel-main/
├── frontend/                     # Official React + TypeScript + Tailwind CSS Dashboard
├── run_demo.py                   # Person A streaming demo launcher
├── run_integrated_demo.py        # Integrated live pipeline demonstrator
├── Dockerfile                    # Container definition for FastAPI backend
├── docker-compose.yml            # Full production microservices stack
├── requirements.txt              # Unified Python dependencies
├── .env.example                  # Environment variable configuration template
├── src/                          # System core & Person C platform
│   ├── api.py                    # FastAPI REST Platform endpoints
│   ├── config.py                 # Centralized configuration loader
│   ├── metrics.py                # Prometheus metric definitions
│   ├── webhook_service.py        # External HTTP POST webhook dispatcher
│   ├── alert_service.py          # Fraud alerts & auto-OTP manager
│   ├── otp_service.py            # OTP lifecycle & verification
│   ├── db.py                     # MongoDB persistence layer
│   ├── schemas.py                # Person A Pydantic data schemas
│   ├── simulator.py              # Person A transaction simulator
│   ├── producer.py               # Person A Kafka producer
│   ├── consumer.py               # Person A Kafka consumer
│   └── state_manager.py          # Person A Redis state manager
├── fraud_detection/              # Person B detection subsystem (LOCKED)
│   ├── detection_service.py      # Transaction scoring orchestrator
│   ├── decision_engine.py        # Risk score calculation & thresholds
│   ├── rule_engine.py            # Deterministic fraud rules
│   ├── ml_service.py             # ML inference wrapper
│   ├── ml_inference.py           # XGBoost prediction pipeline
│   ├── shap_explainer.py         # SHAP TreeExplainer integration
│   └── feature_contract.py       # Feature schema definitions
├── models/                       # Pre-trained XGBoost models & engine configs
├── integration/                  # Integration handlers & glue logic
│   ├── handler.py
│   └── config.py
├── prometheus/                   # Prometheus scraping configuration
│   └── prometheus.yml
├── grafana/                      # Grafana datasources & dashboard JSON
├── deploy/                       # AWS EC2 deployment scripts & docs
├── load_testing/                 # Locust load testing scripts & docs
└── tests/                        # Automated Pytest suite
```

---

## 🛠️ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
cd frontend && npm install
```

### 2. Run Automated Pytest Suite
```bash
python -m pytest tests/ tests_integration/ -v
```

### 3. Run Integrated Live Streaming Demo
```bash
python run_integrated_demo.py --limit 20
```

### 4. Launch FastAPI REST Platform
```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```
- Swagger API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Prometheus Metrics: [http://localhost:8000/metrics](http://localhost:8000/metrics)

### 5. Launch React Operations Console
```bash
cd frontend && npm run dev
```
Open browser at [http://localhost:5173](http://localhost:5173).

---

## 🐳 Docker Stack Deployment

Launch the multi-service stack (FastAPI, MongoDB, Prometheus, Grafana, Redis, Kafka, Zookeeper):

```bash
docker compose up -d --build
```

### Service Access Matrix
- **Official React Dashboard**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Grafana Dashboard**: [http://localhost:3000](http://localhost:3000) (User/Pass: `admin`/`streamsentinel`)
- **Prometheus Scraper**: [http://localhost:9090](http://localhost:9090)


---

## ⚡ Load Testing

```bash
locust -f load_testing/locustfile.py --host http://localhost:8000
```
