#!/usr/bin/env bash
# ============================================================
# StreamSentinel — AWS EC2 Instance Setup Script
# ============================================================
set -euo pipefail

echo "============================================================"
echo "🚀 Preparing AWS EC2 Instance for StreamSentinel"
echo "============================================================"

# Step 1: Update packages
echo "📦 Updating system packages..."
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg git

# Step 2: Install Docker Engine
echo "🐳 Installing Docker Engine..."
if ! command -v docker &> /dev/null; then
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# Step 3: Add user to docker group
echo "👤 Adding current user to docker group..."
sudo usermod -aG docker "$USER" || true

# Step 4: Environment template setup
if [ ! -f .env ]; then
    echo "📄 Creating .env configuration from template..."
    cp .env.example .env
fi

echo "============================================================"
echo "✅ EC2 Setup Complete! Please log out and back in to apply group changes."
echo "Then run: ./deploy/deploy.sh to launch the platform stack."
echo "============================================================"
