## 🚀 Quick Start

### 1 · Prerequisites

* [Docker ≥ 24](https://docs.docker.com/) & Docker Compose
* At least one LLM provider key (e.g. `OPENAI_API_KEY`) or AWS creds for Bedrock.

### 2 · Clone & Run

```bash
git clone https://github.com/your-org/mcp-playground.git
cd mcp-playground
docker compose up --build
```

| Service | URL | Default Port |
| ------- | --- | ------------ |
| Streamlit Client | <http://localhost:8501> | `8501` |
| Weather MCP | <http://localhost:8000> | `8000` |
| Currency MCP | <http://localhost:8001> | `8001` |
---

## ⚙️ Configuration

All runtime settings are concentrated in **`client/config.py`** and environment variables.

| Variable | Purpose |
| -------- | ------- |
| `MODEL_ID` | Provider selector (`OpenAI`, `Bedrock`, `Anthropic`, `Google`, `Groq`).
| `TEMPERATURE` | Sampling temperature (sidebar slider). |
| `MAX_TOKENS` | Token limit (sidebar). |
```python
MODEL_OPTIONS = {
    'OpenAI': 'gpt-4o',
    'Antropic': 'claude-3-5-sonnet-20240620',
    'Google': 'gemini-2.0-flash-001',
    'Bedrock': 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
    'Groq': 'meta-llama/llama-4-scout-17b-16e-instruct'
}
```
MCP endpoints live in **`servers_config.json`** – edit to add/remove servers without code changes.

