# Chatbot Escalation Decision System

A turn-by-turn system that intelligently decides when to escalate a customer support conversation to a human agent. The system uses LLM-based classification with deterministic state tracking to monitor conversation quality and user satisfaction.

## Features

- **LLM-Based Decision Engine**: Uses structured output from language models to classify escalation needs
- **Deterministic State Tracking**: Maintains counters for failed attempts and unresolved turns
- **Rolling Context Window**: Analyzes recent conversation history to make informed decisions
- **Multi-Model Support**: Easy switching between OpenAI, Anthropic, Google, and custom endpoints
- **Interactive CLI**: Chat interface with real-time escalation monitoring
- **Streamlit UI**: Web-based demo with visual escalation analytics
- **Modular Architecture**: Clean interfaces for swapping classifiers (LLM, ML, rules-based)

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/memesrized/chatbot_escalation.git
cd chatbot_escalation
```

2. Install dependencies (Python 3.12+ required):
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Running the System

#### Interactive Chat (CLI)

Run an interactive chat session with escalation monitoring:

```bash
python -m src.cli chat
```

Use a specific model:

```bash
python -m src.cli chat --model=gpt_oss
```

#### Dataset Analysis

Run escalation analysis on the provided dataset:

```bash
python -m src.cli run_dataset
```

#### Streamlit UI

Launch the web interface:

```bash
streamlit run src/ui_streamlit.py
```

## Configuration

### Models

The system supports multiple LLM providers. Configure them in [configs/config.yaml](configs/config.yaml):

```yaml
active_model: openai_gpt4o

models:
  openai_gpt4o:
    provider: openai
    model: gpt-4o
    temperature: 0.0
    env_var: OPENAI_API_KEY
    
  anthropic_sonnet:
    provider: anthropic
    model: claude-sonnet-4-20250514
    temperature: 0.0
    env_var: ANTHROPIC_API_KEY
```

### Context Window

Adjust the number of recent messages to include in escalation decisions:

```yaml
context_window_size: 8
```

## Architecture

### Project Structure

```
src/
├── config/
│   └── load_config.py        # Configuration loader
├── llm/
│   └── factory.py             # LLM factory for model creation
├── decision/
│   ├── base.py                # Base classifier interface
│   └── llm/
│       ├── schema.py          # Structured output schema
│       ├── engine.py          # LLM-based classifier
│       ├── state.py           # State management
│       └── prompt.py          # Prompt templates
├── chat_support/
│   ├── core.py                # Support chatbot
│   └── prompt.py              # Chatbot prompts
├── cli.py                     # CLI interface
└── ui_streamlit.py            # Streamlit UI
```

### Decision Schema

The escalation classifier returns a structured decision with:

- `escalate_now` (bool): Whether to escalate immediately
- `reason_codes` (list): Explanation codes (see below)
- `failed_attempt` (bool): Whether assistant response was inadequate
- `unresolved` (bool): Whether user's issue remains unresolved
- `frustration` (enum): User frustration level (none/mild/high)

### Escalation Reason Codes

**When to Escalate:**
- `USER_REQUESTED_HUMAN`: User explicitly asks for human assistance
- `CHURN_RISK`: User shows strong frustration or threatens to leave
- `REPEATED_FAILURE`: Assistant keeps failing or conversation is stuck
- `ASSISTANT_IRRELEVANT_OR_INCOMPLETE`: Response is irrelevant or incomplete
- `INSTRUCTIONS_DID_NOT_WORK`: User followed steps but problem persists
- `URGENT_OR_HIGH_STAKES`: Urgent/high-stakes issue remains unresolved
- `CAPABILITY_OR_POLICY_BLOCK`: Assistant cannot perform required action

**When NOT to Escalate:**
- `HOW_TO_SOLVABLE`: Straightforward how-to request
- `RESOLVED_CONFIRMED`: User confirms problem is solved
- `SMALL_TALK_OR_GREETING`: No support request
- `TROUBLESHOOTING_IN_PROGRESS`: Troubleshooting progressing normally
- `NEED_MORE_INFO`: Assistant asks clarifying questions

### State Tracking

The system maintains deterministic counters:

- **Failed Attempts Total**: Increments when assistant provides unhelpful response
- **Unresolved Turns**: Consecutive turns where issue remains unresolved

Counters reset when the issue is resolved.

## Design Principles

- **Simplicity**: Straightforward code, minimal abstractions
- **Modularity**: Easy to swap components (LLM → ML → rules)
- **Configurability**: All settings in YAML, secrets in environment
- **Observability**: Clear logging of decisions and state changes
- **Type Safety**: Full type hints and Pydantic validation

## Extending the System

### Adding a New Classifier

Implement the `BaseEscalationClassifier` interface:

```python
from src.decision.base import BaseEscalationClassifier

class MyClassifier(BaseEscalationClassifier):
    def decide(self, messages, state):
        # Your logic here
        return EscalationDecision(...)
```

### Adding a New Model Provider

Add configuration in `config.yaml`:

```yaml
models:
  my_model:
    provider: my-provider
    model: model-name
    temperature: 0.0
    env_var: MY_API_KEY
```

## Future Improvements

- [ ] Add evidence turn IDs for traceability
- [ ] Calibrate threshold policies with larger dataset
- [ ] Add deterministic overrides for specific reason codes
- [ ] Improve multi-issue handling
- [ ] Enhanced emotion/sentiment signals
- [ ] Batch evaluation metrics

## License

See [LICENSE](LICENSE) file for details.

## Documentation

- [Project Overview](md/PROJECT.md)
- [Technical Requirements](md/TECH_REQUIREMENTS.md)
- [Development Rules](md/AGENTS.md)
