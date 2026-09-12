# 🚀 AWS EC2 Deployment Guide — StreamSentinel

This guide details deploying the complete **StreamSentinel** fraud detection stack onto an AWS EC2 instance.

---

## 📋 Recommended EC2 Instance Specs

- **Instance Type**: `t3.medium` (2 vCPU, 4GB RAM) or larger
- **OS**: Ubuntu 22.04 LTS
- **Storage**: 30GB EBS (gp3)

---

## 🛡️ Security Group Port Rules

Configure inbound security group rules:

| Port | Protocol | Purpose | Access Level |
|------|----------|---------|--------------|
| 22 | TCP | SSH Management | Restricted to admin IP |
| 8000 | TCP | FastAPI REST API & `/metrics` | Public / Application |
| 5173 | TCP | React Operations Dashboard | Public / Application |
| 3000 | TCP | Grafana Observability Dashboard | Admin / Internal |
| 9090 | TCP | Prometheus Metrics Server | Internal |

---

## ⚡ Deployment Instructions

### 1. SSH into Instance & Clone Repository
```bash
ssh -i your-key.pem ubuntu@ec2-your-instance-ip.compute-1.amazonaws.com
git clone <your-repo-url> StreamSentinel-main
cd StreamSentinel-main
```

### 2. Run Setup Script
```bash
chmod +x deploy/setup.sh deploy/deploy.sh
./deploy/setup.sh
```

### 3. Configure Environment Variables
Edit `.env` if custom credentials or webhook endpoints are needed:
```bash
nano .env
```

### 4. Deploy Full Stack
```bash
./deploy/deploy.sh
```

---

## 🔍 Verification & Operation

- View active services: `docker compose ps`
- View live logs: `docker compose logs -f`
- Health status: `curl http://localhost:8000/health`
