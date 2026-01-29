"""LLM-based escalation decision engine."""

from langchain_core.language_models.chat_models import BaseChatModel

from src.decision.base import (
    BaseEscalationClassifier,
    ConversationState,
    Message,
)
from src.decision.llm.prompt import build_prompt
from src.decision.llm.schema import EscalationDecision


class LLMEscalationClassifier(BaseEscalationClassifier):
    """LLM-based escalation decision classifier."""

    def __init__(self, model: BaseChatModel):
        """
        Initialize the classifier with a LangChain chat model.

        Args:
            model: LangChain chat model for structured output
        """
        self.model = model.with_structured_output(EscalationDecision)

    def decide(
        self,
        messages: list[Message],
        state: ConversationState,
    ) -> EscalationDecision:
        """
        Decide whether to escalate based on recent messages and state.

        Args:
            messages: Recent conversation messages (rolling window)
            state: Current conversation state with counters

        Returns:
            EscalationDecision with escalate_now flag and reason codes
        """
        if not messages:
            # No messages, nothing to escalate
            return EscalationDecision(
                escalate_now=False,
                reason_codes=["SMALL_TALK_OR_GREETING"],
                failed_attempt=False,
                unresolved=False,
                frustration="none",
            )

        prompt = build_prompt(
            messages,
            state.failed_attempts_total,
            state.unresolved_turns,
        )

        try:
            decision = self.model.invoke(prompt)
            return decision
        except Exception as e:
            # Safe fallback on error
            print(f"Error during escalation decision: {e}")
            return EscalationDecision(
                escalate_now=False,
                reason_codes=["NEED_MORE_INFO"],
                failed_attempt=False,
                unresolved=True,
                frustration="none",
            )
