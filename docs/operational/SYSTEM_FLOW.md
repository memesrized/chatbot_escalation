# System Flow Diagrams

This document contains visual representations of the Chatbot Escalation Decision System architecture and flow.

## 1. Main Conversation Flow

This diagram shows the turn-by-turn flow from user input through escalation decision and chatbot response.

```mermaid
flowchart TD
    Start([User Starts Conversation]) --> UserMsg[User Sends Message]
    
    UserMsg --> PrepareContext1[Prepare Context:<br/>Last N messages + State counters]
    PrepareContext1 --> Classifier1{Escalation Classifier<br/>After User Turn}
    
    Classifier1 --> |"Schema Output:<br/>escalate_now, reason_codes,<br/>unresolved, frustration"| CheckEscalate1{escalate_now<br/>== True?}
    
    CheckEscalate1 --> |Yes| Escalate[🚨 ESCALATE TO HUMAN]
    Escalate --> End([End Conversation])
    
    CheckEscalate1 --> |No| UpdateState1[Update State:<br/>- unresolved_turns<br/>- Track frustration level]
    
    UpdateState1 --> ChatBot[Chatbot Generates Response]
    
    ChatBot --> PrepareContext2[Prepare Context:<br/>Last N messages + State counters]
    PrepareContext2 --> Classifier2{Escalation Classifier<br/>After Assistant Turn}
    
    Classifier2 --> |"Schema Output:<br/>escalate_now, reason_codes,<br/>failed_attempt, unresolved"| CheckEscalate2{escalate_now<br/>== True?}
    
    CheckEscalate2 --> |Yes| Escalate
    
    CheckEscalate2 --> |No| UpdateState2[Update State:<br/>- failed_attempts_total<br/>- unresolved_turns<br/>- Reset counters if resolved]
    
    UpdateState2 --> Display[Display Chatbot Response<br/>to User]
    
    Display --> UserMsg
    
    style Escalate fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style Classifier1 fill:#4dabf7,stroke:#1971c2,color:#fff
    style Classifier2 fill:#4dabf7,stroke:#1971c2,color:#fff
    style ChatBot fill:#51cf66,stroke:#2f9e44,color:#fff
    style UpdateState1 fill:#ffd43b,stroke:#fab005
    style UpdateState2 fill:#ffd43b,stroke:#fab005
```

**Key Points:**
- **Dual Classification**: Escalation is checked after BOTH user and assistant turns
- **Rolling Context**: Only last N messages (default: 8) are passed to classifier
- **State Tracking**: Deterministic counters maintained across turns
- **Decision Schema**: Structured output with specific fields for each turn type

---

## 2. State Management Logic

This diagram details how deterministic state counters are updated based on classifier output.

```mermaid
flowchart TD
    Start([Classifier Returns Decision]) --> CheckTurn{Which Turn?}
    
    CheckTurn --> |User Turn| UserOutput["Output Fields:<br/>- unresolved<br/>- frustration"]
    CheckTurn --> |Assistant Turn| AssistOutput["Output Fields:<br/>- failed_attempt<br/>- unresolved"]
    
    UserOutput --> UpdateUnresolved1{unresolved<br/>== True?}
    UpdateUnresolved1 --> |Yes| IncrUnresolved1[unresolved_turns += 1]
    UpdateUnresolved1 --> |No| ResetUnresolved1[unresolved_turns = 0]
    
    IncrUnresolved1 --> LogFrustration[Log frustration level<br/>for monitoring]
    ResetUnresolved1 --> LogFrustration
    LogFrustration --> EndUser([Continue])
    
    AssistOutput --> CheckFailed{failed_attempt<br/>== True?}
    CheckFailed --> |Yes| IncrFailed[failed_attempts_total += 1]
    CheckFailed --> |No| SkipFailed[Keep failed_attempts_total]
    
    IncrFailed --> UpdateUnresolved2{unresolved<br/>== True?}
    SkipFailed --> UpdateUnresolved2
    
    UpdateUnresolved2 --> |Yes| IncrUnresolved2[unresolved_turns += 1]
    UpdateUnresolved2 --> |No| ResetAll[unresolved_turns = 0<br/>failed_attempts_total = 0]
    
    IncrUnresolved2 --> EndAssist([Continue])
    ResetAll --> EndAssist
    
    style CheckFailed fill:#ffd43b,stroke:#fab005
    style IncrFailed fill:#ff8787,stroke:#fa5252
    style ResetAll fill:#51cf66,stroke:#2f9e44,color:#fff
    style UpdateUnresolved1 fill:#ffd43b,stroke:#fab005
    style UpdateUnresolved2 fill:#ffd43b,stroke:#fab005
```

**State Counter Rules:**
- `failed_attempts_total`: Increments when assistant provides unhelpful response
- `unresolved_turns`: Consecutive turns where issue remains unresolved
- **Reset Condition**: Both counters reset to 0 when issue is resolved (unresolved = false)

---

## 3. System Architecture

This diagram shows the modular component structure and data flow.

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[CLI Interface<br/>src/cli.py]
        UI[Streamlit UI<br/>Optional Demo]
    end
    
    subgraph "Configuration"
        Config[Config Loader<br/>src/config/load.py]
        YAML[config.yaml<br/>Multi-model settings]
        ENV[.env<br/>API Keys]
    end
    
    subgraph "Core Logic"
        ChatBot[Support Chatbot<br/>src/chat_support/core.py]
        Orchestrator[Conversation<br/>Orchestrator]
    end
    
    subgraph "Decision Engine"
        Base[BaseEscalationClassifier<br/>Interface]
        LLMClassifier[LLM Classifier<br/>src/decision/llm/engine.py]
        State[State Manager<br/>src/decision/llm/state.py]
        Schema[Output Schema<br/>src/decision/llm/schema.py]
    end
    
    subgraph "LLM Integration"
        Factory[LLM Factory<br/>src/llm/factory.py]
        LangChain[LangChain<br/>Chat Models]
    end
    
    subgraph "Evaluation"
        Metrics[Metrics Calculator<br/>src/evaluation/metrics.py]
        Runner[Dataset Runner<br/>src/evaluation/runner.py]
    end
    
    CLI --> Orchestrator
    UI --> Orchestrator
    
    Config --> YAML
    Config --> ENV
    
    Orchestrator --> ChatBot
    Orchestrator --> LLMClassifier
    
    LLMClassifier --> Base
    LLMClassifier --> State
    LLMClassifier --> Schema
    LLMClassifier --> Factory
    
    ChatBot --> Factory
    
    Factory --> Config
    Factory --> LangChain
    
    Runner --> LLMClassifier
    Runner --> Metrics
    
    style LLMClassifier fill:#4dabf7,stroke:#1971c2,color:#fff
    style State fill:#ffd43b,stroke:#fab005
    style Factory fill:#51cf66,stroke:#2f9e44,color:#fff
    style Base fill:#e599f7,stroke:#9c36b5,color:#fff
```

**Modularity Benefits:**
- **Swappable Classifiers**: Any classifier inheriting from `BaseEscalationClassifier` can replace LLM version
- **Multi-Model Support**: Factory pattern with config-based model selection
- **Clean Interfaces**: Separation between state, schema, and decision logic

---

## 4. Context Window Management

This diagram illustrates how the rolling context window is maintained.

```mermaid
sequenceDiagram
    participant User
    participant System
    participant Context as Context Window<br/>(Last N=8 messages)
    participant Classifier
    participant State as State Counters
    
    User->>System: Message 1
    System->>Context: Add user message
    Context->>Classifier: [msg1] + state
    Classifier->>State: Update counters
    System->>User: Response 1
    System->>Context: Add assistant message
    
    User->>System: Message 2
    System->>Context: Add user message
    Context->>Classifier: [msg1, resp1, msg2] + state
    Classifier->>State: Update counters
    System->>User: Response 2
    System->>Context: Add assistant message
    
    Note over Context: ... conversation continues ...
    
    User->>System: Message 5
    System->>Context: Add user message
    Note over Context: Window now has 10 messages<br/>(exceeds limit of 8)
    Context->>Context: Trim to last 8 messages
    Context->>Classifier: [last 8 messages] + state
    Classifier->>State: Update counters
    System->>User: Response 5
    
    Note over Context,State: Context stays bounded<br/>State preserves history
```

**Context Strategy:**
- **Bounded Window**: Prevents unbounded context growth
- **Recency Bias**: Most recent exchanges are most relevant
- **State Persistence**: Counters carry historical information forward

---

## 5. Escalation Decision Schema

Visual representation of the structured output returned by the classifier.

```mermaid
classDiagram
    class EscalationDecision {
        +bool escalate_now
        +List[str] reason_codes
        +bool failed_attempt*
        +bool unresolved
        +str frustration
    }
    
    class ReasonCodes {
        <<enumeration>>
        ESCALATE_REASONS
        USER_REQUESTED_HUMAN
        CHURN_RISK
        REPEATED_FAILURE
        ASSISTANT_IRRELEVANT_OR_INCOMPLETE
        INSTRUCTIONS_DID_NOT_WORK
        URGENT_OR_HIGH_STAKES
        CAPABILITY_OR_POLICY_BLOCK
        ---
        DO_NOT_ESCALATE_REASONS
        HOW_TO_SOLVABLE
        RESOLVED_CONFIRMED
        SMALL_TALK_OR_GREETING
        TROUBLESHOOTING_IN_PROGRESS
        NEED_MORE_INFO
    }
    
    class FrustrationLevel {
        <<enumeration>>
        none
        mild
        high
    }
    
    class StateCounters {
        +int failed_attempts_total
        +int unresolved_turns
    }
    
    EscalationDecision --> ReasonCodes : uses
    EscalationDecision --> FrustrationLevel : uses
    EscalationDecision --> StateCounters : updates
    
    note for EscalationDecision "* failed_attempt only present<br/>after Assistant turn"
```

---

## Design Principles

### Why Dual Classification (User + Assistant Turns)?
- **Customer Satisfaction Priority**: Catch escalation signals immediately when user expresses frustration
- **No Waiting**: Don't force upset users to wait for chatbot response
- **Responsive**: Better handling of urgent situations and emotional states

### Why Rolling Context Window?
- **Scalability**: Prevents unbounded context growth in long conversations
- **Cost Efficiency**: Reduces tokens sent to LLM
- **Focus**: Recent messages are most relevant for escalation decisions

### Why Deterministic State Tracking?
- **Stability**: Single misclassification won't dominate outcome
- **Transparency**: Counter logic is explicit and auditable
- **Tunability**: Easy to adjust thresholds without retraining

### Why Structured Output?
- **Reliability**: Type-safe, validated responses
- **Explainability**: Reason codes provide clear decision rationale
- **Monitoring**: Structured data enables metrics and analysis
