## 🚀 Setting Up the Grafana MCP Server

### 1. Clone the Repository

```bash
git clone https://github.com/DrDroidLab/grafana-mcp-server.git
cd grafana-mcp-server
```

---

### 2A. Run with `uv` (Recommended for Local Development)

#### a. Install `uv` (if not already installed)

```bash
pip install uv
```

#### b. Create and activate a virtual environment

```bash
uv venv .venv
source .venv/bin/activate
```

#### c. Install dependencies

```bash
uv sync
```

#### d. Configure your Grafana details

Edit (or create) `src/grafana_mcp_server/config.yaml`:

```yaml
grafana:
  host: "https://your-grafana-instance.com"
  api_key: "your-grafana-api-key-here"
  ssl_verify: "true"
server:
  port: 8000
  debug: true
```

Alternatively, you can set these as environment variables:

```bash
export GRAFANA_HOST="https://your-grafana-instance.com"
export GRAFANA_API_KEY="your-grafana-api-key-here"
export GRAFANA_SSL_VERIFY="true"
export MCP_SERVER_PORT=8000
```

#### e. Start the MCP server

```bash
uv run src/grafana_mcp_server/mcp_server.py
```

---

### 2B. Run with Docker Compose (Recommended for Production)

#### a. Edit the configuration

Edit `src/grafana_mcp_server/config.yaml` as above, or set environment variables.

#### b. Start the server

```bash
docker compose up -d
```

By default, the server will be available at `http://localhost:8000/mcp`.

---

### 3. Expose the MCP Server via ngrok

If you want to access the MCP server remotely (e.g., from a cloud service or remote client), you can use [ngrok](https://ngrok.com/) to expose your local server.

#### a. Install ngrok

Download from [ngrok.com](https://ngrok.com/download) and follow the setup instructions.

#### b. Start ngrok to tunnel port 8000

```bash
ngrok http 8000
```

#### c. Copy the HTTPS forwarding URL from ngrok's output, e.g.:

```
Forwarding     https://abc12345.ngrok.io -> http://localhost:8000
```

Your MCP server endpoint is now:  
```
https://abc12345.ngrok.io/mcp
```

Use this URL as the MCP endpoint in your client or script configuration.

---

### 4. Health Check

You can verify the server is running by visiting:

```
http://localhost:8000/health
```
or (if using ngrok):
```
https://abc12345.ngrok.io/health
```

---

### 5. Reference

- [Grafana MCP Server GitHub](https://github.com/DrDroidLab/grafana-mcp-server)

---

**Tip:**  
- Make sure your Grafana API key has sufficient permissions (Admin recommended).
- For production, secure your ngrok tunnel or use a reverse proxy with authentication.

Let me know if you need a sample client script or further help!