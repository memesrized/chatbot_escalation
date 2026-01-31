# Escalation Decision System (Time-boxed Prototype)

## Goal

Build a turn-by-turn system that decides **when to escalate a conversation to a human agent** during an ongoing chat. The focus is escalation behavior (right timing), not crafting perfect chatbot replies.

This is intentionally scoped as a one-day prototype: the design is meant to be production-reasonable in terms of logic/data flow/interfaces, while keeping implementation simple and reviewable.

---

## High-level approach

At each conversation step, we compute an escalation decision using:

1) **Rolling context window**: the last **N** messages (e.g., `N=8`)  
2) **Minimal deterministic state** tracked in code across turns (counters)

This avoids unbounded context growth and supports long dialogues where the issue persists.

---

## Inputs per step

### Context window
We pass the model the **last N messages** in chronological order.

### Deterministic state (maintained in code)
We track only escalation-relevant counters:

- `failed_attempts_total: int`  
  Counts how many times the assistant produced an unhelpful / non-actionable response.

- `unresolved_turns: int`  
  Counts how many consecutive turns the issue remained unresolved from the user’s perspective.

These two signals capture different escalation dynamics:
- repeated assistant failures should escalate quickly (poor UX / low trust)
- unresolved issues can legitimately require multiple troubleshooting turns if progress is happening

---

## Model output schema (per step)

The model acts as a structured classifier and returns:

- `escalate_now: bool`  
  Whether the conversation should be escalated to a human at this step.

- `reason_codes: List[str]`  
  Enum list describing *why* escalation is needed or why it is not.

- `failed_attempt: bool`  
  **Assistant-quality signal**: whether the assistant’s last response failed to provide a meaningful, actionable answer.
  Examples:
  - generic apology with no next steps
  - refusal without actionable alternative
  - irrelevant answer that does not address the user’s question
  - “something went wrong” type response

- `unresolved: bool`  
  **User-outcome signal**: whether the user’s issue is still unresolved after the latest exchange.
  Examples:
  - user indicates the problem persists (“still not working”, “same issue”)
  - user repeats the request or complaint
  - troubleshooting continues and resolution is not confirmed

- `frustration: "none" | "mild" | "high"` (telemetry only)  
  Coarse estimate of user frustration level. This is logged for monitoring and analysis, but **not used as a decision field** in this version.

Notes:
- Evidence turn IDs are intentionally not required in this time-boxed version. Adding evidence references is listed as future work.

---

## Reason codes (rubric expressed as enums)

The escalation rubric is implemented as a closed set of `reason_codes`. In other words:
- the "when to escalate" rubric is exactly the set of escalation reason codes
- the "when not to escalate" rubric is exactly the set of non-escalation reason codes

The model should select **one or more** reason codes that best explain the decision at the current turn.

### Escalate reasons (rubric)
Use these codes when escalation is needed:

- `USER_REQUESTED_HUMAN`  
  User explicitly asks to escalate or speak to a human representative.

- `CHURN_RISK`  
  User shows strong frustration or threatens to leave the service.

- `REPEATED_FAILURE`  
  The assistant keeps failing to make progress, repeating itself, or the conversation is stuck.

- `ASSISTANT_IRRELEVANT_OR_INCOMPLETE`  
  The assistant’s response is irrelevant, lacks needed info, or does not answer the user’s actual question.

- `INSTRUCTIONS_DID_NOT_WORK`  
  The user followed the provided steps, but the problem still persists.

- `URGENT_OR_HIGH_STAKES`  
  The case is urgent or high-stakes (especially money-related issues like missing funds) and remains unresolved.

- `CAPABILITY_OR_POLICY_BLOCK`  
  The assistant cannot perform the required action due to capability or policy constraints, and human intervention is needed.

### Do-not-escalate reasons (rubric)
Use these codes when escalation is not needed:

- `HOW_TO_SOLVABLE`  
  The request is a straightforward how-to and the assistant can provide clear, actionable instructions.

- `RESOLVED_CONFIRMED`  
  The user confirms the problem is solved or says they do not need more help.

- `SMALL_TALK_OR_GREETING`  
  There is no support request (only greeting / small talk).

- `TROUBLESHOOTING_IN_PROGRESS`  
  Troubleshooting is ongoing and progressing, without explicit escalation request or strong frustration.

- `NEED_MORE_INFO`  
  The assistant asks reasonable clarifying questions to proceed, and the user is cooperating.

---

## Deterministic aggregation and state updates (in code)

After each step, counters are updated deterministically:

- If `failed_attempt == true`:  
  `failed_attempts_total += 1`

- If `unresolved == true`:  
  `unresolved_turns += 1`  
  else:  
  `unresolved_turns = 0`

- If the issue becomes resolved (`unresolved == false`):  
  `failed_attempts_total = 0`  
  (issue is considered closed)

This design reduces reliance on the model remembering long history and makes behavior more stable: a single misclassification should not dominate the final outcome.

---

## Decision policy and thresholds

In this prototype, the model returns `escalate_now` directly, guided by the reason codes above.

Additionally, the deterministic counters (`failed_attempts_total`, `unresolved_turns`) enable configurable policy tightening later, for example:
- escalate if `failed_attempts_total >= 2` (assistant repeatedly fails)
- escalate if `unresolved_turns >= 4` (issue persists over multiple turns)

These thresholds are considered policy knobs and can be tuned as requirements evolve.

---

## Dataset note (small sample size)

The provided dataset contains a small number of examples (around ~20). This is not sufficient for robust offline evaluation or meaningful model selection. In this prototype:
- the dataset is used primarily to infer escalation reason codes and validate behavior on representative scenarios
- comprehensive evaluation would require a larger labeled set and clearer policy definitions

---

## CLI simulation

A simple CLI is provided to simulate a conversation turn-by-turn and print:
- `escalate_now`
- `reason_codes`
- `failed_attempt`, `unresolved`
- `frustration`
- updated counters (`failed_attempts_total`, `unresolved_turns`)

This allows quick manual testing and demonstration of escalation timing.

So there should be another model that emulates a support chatbot and tries to answer user question from cli stdin.
And for each turn (each chatbot and each user message) there is an escalation check with printed results.

---

## Future improvements

- Add evidence turn IDs for each reason code (traceability)
- Calibrate and validate deterministic threshold policies against a larger labeled dataset
- Add deterministic overrides for specific reason codes (e.g., explicit request for human)
- Improve handling of multiple simultaneous issues within one conversation
- Add richer emotion/sentiment signals (anger/frustration/etc.) beyond coarse `frustration` telemetry
