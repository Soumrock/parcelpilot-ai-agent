# ParcelPilot AI Support & Operations Agent

Internal support/operations AI agent built for the CalQuity AI Engineer assessment.

The application helps authorised ParcelPilot support/operations users investigate orders and tickets, retrieve relevant support documents, reason across customer-specific agreements and current policies, and prepare safe state-changing actions that require explicit confirmation.

## Technology Stack

- **Python**
- **Streamlit** — chat interface and hosting target
- **Hugging Face Inference Providers** — LLM inference and tool-calling
- **Pandas / OpenPyXL** — structured operational data from the supplied Excel workbook
- **PyPDF** — PDF document loading
- **Local TF-IDF retrieval** — lightweight document search with source metadata
- **Local mocked action store** — simulated escalation/state-changing actions for the assessment

## Application Architecture

```text
User
  ↓
Streamlit Chat UI
  ↓
AI Agent / Orchestrator
  ├── Document Retrieval Tool
  ├── Structured Data Tool
  └── State-Changing Action Tool
          ↓
     Explicit Confirmation
          ↓
     Mocked Action Execution
```

The agent uses the supplied data pack as its information base. Source authority and customer-specific overrides are considered when forming answers, and access checks are enforced in the data/tool layer.

## Run Locally

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
```

**Windows**

```powershell
.venv\Scripts\activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Hugging Face

Create a local `.env` file from `.env.example` and add your Hugging Face token.

```env
HF_TOKEN=your_huggingface_token
HF_MODEL=openai/gpt-oss-120b:groq
HF_PROVIDER=auto
```

**Do not commit `.env` or expose your Hugging Face token.**

### 4. Start the application

```bash
streamlit run streamlit_app.py
```

The application will open locally in your browser.

## Streamlit Community Cloud Secrets

For Streamlit Community Cloud, add the following under the app's **Secrets** settings:

```toml
HF_TOKEN = "your_huggingface_token"
HF_MODEL = "openai/gpt-oss-120b:groq"
HF_PROVIDER = "auto"
```

The application reads configuration from environment variables locally and from Streamlit secrets when deployed.

## Assessment Requirements Covered

The implementation covers the minimum assessment requirements:

- Natural-language chatbot
- Document search / retrieval
- Structured-data lookup and calculation
- State-changing action tool
- Explicit confirmation before state-changing actions
- Multi-step workflows using multiple tools and sources
- Data/tool-layer access control
- Source authority, freshness, and conflict handling
- Escalation when a request requires human judgment or unsupported action
- Simple chat interface with visible tool trace

## Source Reliability and Conflict Handling

The supplied support policy defines the source precedence used by the agent:

1. Signed customer agreement
2. Current support policy
3. Current product documentation
4. Historical tickets / internal notes as context only

The deprecated support policy is retained as historical reference and is not used for current requests.

## Demonstrated Scenarios

The local application has been tested against scenarios including:

- Northstar cancellation override for `ORD-1001`
- Ambiguous service-credit questions where account context is missing
- LumenWorks service-credit calculation for `ORD-2002`
- SwiftShip webhook-delay known issue (`KI-211`)
- P1 security escalation for `TKT-505`
- Explicit confirmation before executing an escalation
- Role-scoped access denial for an unauthorised account

## Current Product Choice

The submission implements an **internal support/operations agent** rather than a customer-facing agent. This keeps the assessment scope focused on investigation, retrieval, structured-data reasoning, authorization, source reliability, and safe actions.

## Deploy to Streamlit Community Cloud

1. Push the repository to a public GitHub repository.
2. Sign in to Streamlit Community Cloud with GitHub.
3. Create a new app and select this repository and branch.
4. Set the main file to:

```text
streamlit_app.py
```

5. Add `HF_TOKEN`, `HF_MODEL`, and `HF_PROVIDER` under the app's **Secrets** settings.
6. Deploy the application.
7. Verify the same key assessment scenarios on the hosted URL before submission.

## Project Documentation

- `docs/architecture.md` — agent, tools, data handling, reliability, and technical trade-offs
- `docs/product_note.md` — additional client problem, future roadmap, deliberate omissions, and usefulness metric
- `docs/demo_script.md` — roughly five-minute demonstration flow
- `docs/ai_tool_usage.md` — AI coding tool usage statement

## Repository Structure

```text
.
├── app/
├── data/
├── docs/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── streamlit_app.py
└── tests.py
```
