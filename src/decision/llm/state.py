"""State management for conversation tracking."""

from src.decision.base import ConversationState
from src.decision.llm.schema import EscalationDecision


def update_state(
    state: ConversationState, decision: EscalationDecision
) -> ConversationState:
    """
    Update conversation state based on escalation decision.

    Args:
        state: Current conversation state
        decision: Latest escalation decision

    Returns:
        Updated conversation state
    """
    new_state = ConversationState(
        failed_attempts_total=state.failed_attempts_total,
        unresolved_turns=state.unresolved_turns,
    )

    # Update failed attempts counter
    if decision.failed_attempt:
        new_state.failed_attempts_total += 1

    # Update unresolved turns counter
    if decision.unresolved:
        new_state.unresolved_turns += 1
    else:
        # Issue resolved, reset counters
        new_state.unresolved_turns = 0
        new_state.failed_attempts_total = 0

    return new_state
