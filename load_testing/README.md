# ⚡ Locust Load Testing — StreamSentinel

This directory contains benchmark load test scripts for measuring FastAPI platform throughput, latency percentiles, and stability under load.

---

## 🚀 Quick Start

### 1. Install Locust
```bash
pip install locust
```

### 2. Interactive Web UI Mode
```bash
locust -f load_testing/locustfile.py --host http://localhost:8000
```
Open browser at `http://localhost:8089` to specify user count and spawn rate.

### 3. Headless Mode
```bash
locust -f load_testing/locustfile.py --host http://localhost:8000 --headless -u 10 -r 2 -t 60s
```
