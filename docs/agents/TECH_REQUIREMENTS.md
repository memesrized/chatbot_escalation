# Technical Requirements and Implementation Notes

This document describes the technical requirements and implementation constraints for the escalation decision prototype. The goal is to keep the system **simple, runnable, and easy to modify**, while remaining modular enough to swap components later (LLM, prompt-based logic, classical ML, etc.).

---

## Language and runtime

- **Language**: Python
- **Version**: **Python 3.12+**
- Keep dependencies minimal and justified (this is a time-boxed prototype).

---

## Tech stack

### LLM orchestration: LangChain
Use LangChain primarily to:
- keep the LLM interface consistent
- make it easy to switch providers/models later
- support structured outputs (JSON) and model configuration via kwargs

Implementation guidance:
- load chat models via `init_chat_model(...)` with `model_kwargs` (or equivalent) so the code can accept any LangChain-supported chat model
- do not over-abstract, keep orchestration minimal and readable

### CLI: Fire (or similar)
Provide a CLI to:
- run an interactive conversation simulation
- print model outputs per turn (`escalate_now`, `reason_codes`, `failed_attempt`, `unresolved`, `frustration`, counters)
- optionally run a batch evaluation on the provided dataset (even if small)

Preferred:
- `fire` for quick, clean CLI
- alternatives acceptable: `typer` or `click`

CLI should expose at least:
- `chat` to run an interactive session in terminal
- `run_dataset` to run through included examples and print predictions

### UI: Streamlit (minimal)
Add a small Streamlit chat UI to demonstrate the turn-by-turn behavior:
- simple chat interface
- shows the escalation decision panel (current output + counters)
- keeps state across turns (session state)

Keep it minimal: this is a demo tool, not a product UI.

---

## Design constraints

### Keep logic simple
- avoid unnecessary abstractions
- keep modules small and easy to read
- prefer explicit data flow over “framework magic”
- only introduce abstractions if they reduce duplication or clearly improve extensibility

### Modular, but not over-engineered
The code should be modular enough to swap key parts later, for example:
- replace LLM-based classifier with a transformer classifier
- replace with classical ML (TF-IDF + logistic regression)
- replace with rules-only baseline

This implies:
- define clear interfaces around the decision component
- keep model/prompt configuration outside business logic
- separate “state update” logic from “model inference” logic

---

## Configuration and secrets

### YAML config (human readable)
All runtime settings should be configurable via **YAML** (human readable), e.g. `configs/config.yaml`.

Requirements:
- config supports **multiple model definitions**
- at application start, the user selects which model to use via a **model name** (string key)
- config holds only non-secret settings and the *names* of required environment variables for secrets

#### Multi-model config pattern
- `models:` section contains multiple named model entries
- `active_model:` selects one of them (or CLI flag overrides it)

Example (illustrative structure):
- `models.openai_gpt4o`
- `models.anthropic_sonnet`
- `models.gemini_flash`
- `models.local_compatible`

### Environment variables
All secrets and API keys must be sourced from environment variables:
- `.env` supported locally (optional)
- production usage assumes real environment variables

Config must not contain secrets directly. Instead:
- config references env var names (e.g. `OPENAI_API_KEY`)
- code resolves those at runtime

Provide `.env.example` listing required variables.

---

## Model initialization requirements

### Use `init_chat_model` and kwargs
Models should be created using a generic initialization pattern so switching providers is easy.

Requirements:
- pass configuration via kwargs
- avoid hardcoding provider-specific initialization in business logic
- keep model selection in config

Implementation expectations:
- an LLM factory takes `(config, model_name)` and returns a LangChain chat model
- the factory supports multiple providers via config entries

Provide several example model configs for convenience (within one YAML or multiple YAMLs):
- OpenAI-compatible provider
- Anthropic
- Google (Gemini)
- local/OpenAI-compatible endpoint (optional)

---

## Output handling and validation

### Structured output
Model output must be strict JSON and validated in code:
- required fields: `escalate_now`, `reason_codes`, `failed_attempt`, `unresolved`, `frustration`
- validate enums (reason codes and frustration levels)
- apply safe fallbacks if parsing/validation fails

### Minimal error handling
If model output is invalid:
- default to a safe, review-friendly behavior (for example: no escalation + ask for clarification, or "offer human" if you implement that)
- log the failure and the raw model output (for debugging)

---

## Repository structure (suggested)

A simple layout:

- `src/`
  - `config/`
    - `load_config.py` (Config as a class)
  - `llm/`
    - `factory.py` (load langchain model from config)
  - `decision/`
    - `base.py` (base class)
    - `llm`
      - `schema.py` (structured output schema, reasons with description)
      - `engine.py` (runs model and produces decision)
      - `state.py` (counter updates)
      - `prompt.py` (prompt template)
  - `chat_support` (chat bot simulation)
    - `prompt.py`
    - `core.py` (core chat functionality)
  - `cli.py`
  - `ui_streamlit.py`

- `configs/`
  - `config.yaml` (multi-model)
  - (optional) `config.examples.yaml` (extra presets)

- `.env.example`
- `README.md`

---

## Non-goals (explicit)

To keep scope aligned with a one-day assignment:
- no Kubernetes / deployment pipelines
- no advanced observability stack
- no heavy experiment tracking
- no complex multi-agent setup
- no heavy training pipeline (dataset is small)

The emphasis is runnable prototype + clean interfaces + clear configuration.

---

## Other notes:
- use `.with_structured_output` in langchain instead of manual parsing of the output
- LLMEscalationClassifier should be a single class (+ base class like BaseEscalationClassifier)
  - the class should be easily replaceable by the similar one inherited from base class
- config may have `active_model: name` for convenience, but it should be possible to set the model during the cli startup
- field in pydantic classes for structured output must have proper description, especially escalation and non-escalation criteria
