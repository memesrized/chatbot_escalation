"""Prompt template for escalation decision."""

import json

ESCALATION_DECISION_PROMPT = """You are an escalation decision classifier for a customer support chat system.

Your task is to analyze the recent conversation and determine whether it should be escalated to a human agent.

## Your Analysis Task
Based on the conversation above, determine:

1. **escalate_now**: Should this conversation be escalated to a human now?

2. **reason_codes**: Which reason code to apply?

3. **failed_attempt**: Did the assistant's LAST response fail to provide meaningful, actionable help?
   - Generic apology with no next steps
   - Refusal without actionable alternative
   - Irrelevant answer
   - "Something went wrong" type response

4. **unresolved**: Is the user's issue STILL unresolved after this exchange?
   - User says problem persists
   - User repeats request or complaint
   - Troubleshooting continues without confirmation

5. **frustration**: User's frustration level (none, mild, or high)

Provide your analysis in the structured format.

## Current State
- Failed attempts (assistant failures): {failed_attempts_total}
- Unresolved turns (consecutive): {unresolved_turns}

## Recent Conversation
{conversation}
"""


def format_conversation(messages: list) -> str:
    """Format messages for the prompt."""
    return json.dumps(
        [{msg.role.upper(): msg.content} for msg in messages],
        ensure_ascii=False,
        indent=4,
    )


def build_prompt(
    messages: list,
    failed_attempts_total: int,
    unresolved_turns: int,
) -> str:
    """Build the complete prompt for escalation decision."""
    conversation = format_conversation(messages)
    return ESCALATION_DECISION_PROMPT.format(
        failed_attempts_total=failed_attempts_total,
        unresolved_turns=unresolved_turns,
        conversation=conversation,
    )
