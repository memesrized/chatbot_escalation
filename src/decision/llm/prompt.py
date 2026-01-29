"""Prompt template for escalation decision."""

ESCALATION_DECISION_PROMPT = """You are an escalation decision classifier for a customer support chat system.

Your task is to analyze the recent conversation and determine whether it should be escalated to a human agent.

## Current State
- Failed attempts (assistant failures): {failed_attempts_total}
- Unresolved turns (consecutive): {unresolved_turns}

## Recent Conversation
{conversation}

## Your Analysis Task
Based on the conversation above, determine:

1. **escalate_now**: Should this conversation be escalated to a human now?

2. **reason_codes**: Which reason codes apply? Select one or more:
   
   ESCALATION REASONS (use when escalation is needed):
   - USER_REQUESTED_HUMAN: User explicitly asks for human assistance
   - CHURN_RISK: User shows strong frustration or threatens to leave
   - REPEATED_FAILURE: Assistant keeps failing or conversation is stuck
   - ASSISTANT_IRRELEVANT_OR_INCOMPLETE: Response is irrelevant or incomplete
   - INSTRUCTIONS_DID_NOT_WORK: User followed steps but problem persists
   - URGENT_OR_HIGH_STAKES: Urgent/high-stakes issue remains unresolved
   - CAPABILITY_OR_POLICY_BLOCK: Assistant cannot perform required action
   
   NON-ESCALATION REASONS (use when escalation is not needed):
   - HOW_TO_SOLVABLE: Straightforward how-to request, assistant can help
   - RESOLVED_CONFIRMED: User confirms problem is solved
   - SMALL_TALK_OR_GREETING: No support request, only greeting/small talk
   - TROUBLESHOOTING_IN_PROGRESS: Troubleshooting progressing without frustration
   - NEED_MORE_INFO: Assistant asks clarifying questions, user cooperating

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

Provide your analysis in the structured format."""


def format_conversation(messages: list) -> str:
    """Format messages for the prompt."""
    lines = []
    for msg in messages:
        role = msg.role.upper()
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)


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
