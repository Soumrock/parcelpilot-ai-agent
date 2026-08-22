# ParcelPilot AI Support & Operations Agent

Internal support/operations AI agent built for the CalQuity AI Engineer assessment.

## Stack
- Python
- Streamlit
- Hugging Face Inference Providers
- Pandas / OpenPyXL
- Local TF-IDF document retrieval with source metadata
- Local mocked escalation/action store

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt

# Create .env from .env.example and add your HF token.
streamlit run streamlit_app.py
```

## Environment variables / Streamlit secrets

Local `.env`:

```env
HF_TOKEN=...
HF_MODEL=Qwen/Qwen2.5-72B-Instruct
HF_PROVIDER=auto
```

For Streamlit Community Cloud, add the same values under **App settings → Secrets**. The app reads either environment variables or Streamlit secrets. Never commit `.env` or expose the token.

## Assessment requirements covered
- Natural-language chatbot
- Document retrieval
- Structured-data lookup/calculation
- State-changing action tool
- Explicit confirmation before action execution
- Multi-step tool workflows
- Data-layer authorization checks
- Source precedence / deprecated-source handling
- Escalation for uncertainty and unsupported actions
- Simple chat interface with visible tool trace

## Source reliability
The agent follows the supplied source precedence: signed customer agreements take priority over general/current support rules; current operational documentation is preferred over deprecated material; historical ticket guidance is treated as context only.

## Current implementation choice
An internal support/operations agent was selected rather than a customer-facing agent so the assessment MVP can focus on investigation, authorization, multi-step reasoning, and safe actions while keeping scope manageable.

## Deploy to Streamlit Community Cloud

1. Push this repository to a public GitHub repository.
2. Sign in at https://share.streamlit.io/ with GitHub.
3. Create an app and select the repository, branch, and `streamlit_app.py` entrypoint.
4. Add `HF_TOKEN`, `HF_MODEL`, and `HF_PROVIDER` in the app's Secrets settings.
5. Deploy and verify the same assessment scenarios used locally.

## Project notes
See:
- `docs/architecture.md`
- `docs/product_note.md`
- `docs/ai_tool_usage.md`
- `docs/demo_script.md`
