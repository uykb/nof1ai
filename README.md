# NOF1.AI Alpha Arena - AI Trading Bot

![NOF1.AI Banner](assets/download.png)

An autonomous, AI-driven crypto trading bot designed for **Binance Futures**. It leverages advanced Large Language Models (LLMs) like Grok, Gemini, and GPT-4 to analyze market structure, while using **Hyperliquid** as an on-chain signal source for transparency and accuracy.

**🚀 Core Architecture:**
*   **Execution**: Binance Futures (USDT-M) via Official Connector.
*   **Signal Source**: Hyperliquid (On-chain Price, Funding, Open Interest).
*   **Analysis**: TAAPI.io (Technical Indicators) + LLM (Decision Making).
*   **Infrastructure**: Docker + PostgreSQL + Redis.

---

## 🛠 Prerequisites

Before you begin, ensure you have:

1.  **A Server (VPS)**: Ubuntu 22.04+ recommended (2GB RAM min).
2.  **Binance Account**:
    *   Create API Key & Secret.
    *   **Enable Futures Trading** permissions for the key.
    *   *(Optional)* Whitelist your server IP for security.
3.  **API Keys**:
    *   [OpenRouter](https://openrouter.ai/) (for LLM access).
    *   [TAAPI.io](https://taapi.io/) (for technical indicators).
4.  **Software**:
    *   [Docker](https://docs.docker.com/engine/install/) & [Docker Compose](https://docs.docker.com/compose/install/) installed.

---

## 📦 Installation & Deployment

### 1. Clone the Repository
Connect to your server via SSH and run:

```bash
git clone https://github.com/uykb/nof1ai.git
cd nof1ai
```

### 2. Configuration (Vital Step)
Create your environment file from the template:

```bash
cp .env.template .env
```

**Edit the `.env` file** (`nano .env`) and fill in your keys:

```ini
# --- Exchange Configuration (Binance) ---
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
# Set to 'true' only if using Binance Testnet
BINANCE_TESTNET=false

# --- AI Model Configuration ---
OPENROUTER_API_KEY=sk-or-v1-your_key_here
# Recommended Models:
# - x-ai/grok-4 (High reasoning)
# - google/gemini-2.0-flash-exp:free (Fast & Free)
# - anthropic/claude-3.5-sonnet (Balanced)
LLM_MODEL=google/gemini-2.0-flash-exp:free

# --- Data Source ---
TAAPI_API_KEY=your_taapi_key_here
# Leave Hyperliquid key empty (used for public read-only data)
HYPERLIQUID_PRIVATE_KEY=

# --- Trading Parameters ---
ASSETS=BTC,ETH
INTERVAL=5m
# 'auto' = Bot executes trades
# 'manual' = Bot only sends proposals for approval
TRADING_MODE=auto

# --- System (Default is fine) ---
APP_PORT=3000
```

### 3. Launch with Docker
Start the entire stack (Bot + Database + Redis) in the background:

```bash
# Pull the latest pre-built image
docker pull ghcr.io/uykb/nof1ai:latest

# Start services
docker-compose up -d
```

> **Note**: If you modified the code locally, use `docker-compose up -d --build` to rebuild from source.

### 4. Verify & Monitor
Check if the bot is running correctly:

```bash
docker-compose logs -f app
```
*You should see logs like "Bot started", "BinanceAPI initialized", and "Sync state success".*

---

## 🖥️ Dashboard Access

Open your browser and navigate to:
**http://<your-server-ip>:3000**

*   **Dashboard**: View real-time balance, positions, and AI reasoning.
*   **Manual Mode**: If `TRADING_MODE=manual`, go to the **Recommendations** tab to approve/reject AI trade proposals.

---

## 🛡️ Security Best Practices

1.  **Dedicated Wallet**: Use a sub-account or dedicated account for the bot with limited funds.
2.  **IP Whitelist**: In Binance API settings, restrict access to your VPS IP address only.
3.  **SSH Security**: Use SSH Key authentication and disable password login on your VPS.
4.  **Environment Variables**: Never share your `.env` file. It is excluded from Git by default.

---

## 🏗 Project Structure

*   `src/backend/bot_engine.py`: The brain. Coordinates data fetching, AI reasoning, and trade execution.
*   `src/backend/trading/binance_api.py`: Official Binance Connector wrapper.
*   `src/backend/trading/hyperliquid_api.py`: Read-only adapter for on-chain signals.
*   `src/backend/agent/decision_maker.py`: AI Agent logic (Prompt Engineering).
*   `src/gui/`: NiceGUI-based frontend (Obsidian/Glassmorphism design).

---

## 📄 License

[MIT](LICENSE)
