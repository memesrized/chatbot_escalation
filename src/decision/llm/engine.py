"""LLM-based escalation decision engine."""

from typing_extensions import Literal
from langchain_core.language_models.chat_models import BaseChatModel

from src.decision.base import BaseEscalationClassifier
from src.decision.llm.prompt import (
    ESCALATION_DECISION_PROMPT_AFTER_USER,
    ESCALATION_DECISION_PROMPT_AFTER_ASSISTANT,
)
from src.decision.llm.schema import (
    EscalationDecisionAfterUser,
    EscalationDecisionAfterAssistant,
)
from src.decision.llm.state import ConversationState
from src.decision.utils import format_conversation
from langchain.messages import AnyMessage


class LLMEscalationClassifier(BaseEscalationClassifier):
    """LLM-based escalation decision classifier."""

    def __init__(self, model: BaseChatModel):
        """
        Initialize the classifier with a LangChain chat model.

        Args:
            model: LangChain chat model for structured output
        """
        self.model = model
        self.model_after_user = model.with_structured_output(
            EscalationDecisionAfterUser
        )
        self.model_after_assistant = model.with_structured_output(
            EscalationDecisionAfterAssistant
        )

    def decide(
        self,
        messages: list[AnyMessage],
        state: ConversationState,
        turn: Literal["user", "assistant"],
    ) -> EscalationDecisionAfterAssistant | EscalationDecisionAfterUser:
        """
        Decide whether to escalate based on recent messages and state.

        Args:
            messages: Recent conversation messages (rolling window)
            state: Current conversation state with counters
            turn: Whose turn it is ("user" or "assistant")
        Returns:
            EscalationDecision with escalate_now flag and reason codes
        """
        if not messages:
            # No messages, nothing to escalate
            return EscalationDecisionAfterUser(
                escalate_now=False,
                reason_codes=["SMALL_TALK_OR_GREETING"],
                unresolved=False,
                frustration="none",
            )

        prompt = self.build_prompt(
            messages,
            state,
            turn,
        )

        try:
            # Use appropriate model based on whose turn it is
            if turn == "user":
                decision = self.model_after_user.invoke(prompt)
            else:
                decision = self.model_after_assistant.invoke(prompt)
            return decision
        except Exception as e:
            # Safe fallback on error - return appropriate schema based on turn
            print(f"Error during escalation decision: {e}")
            if turn == "user":
                return EscalationDecisionAfterUser(
                    escalate_now=False,
                    reason_codes=["NEED_MORE_INFO"],
                    unresolved=True,
                    frustration="none",
                )
            else:
                return EscalationDecisionAfterAssistant(
                    escalate_now=False,
                    reason_codes=["NEED_MORE_INFO"],
                    failed_attempt=False,
                )

    def build_prompt(
        self,
        messages: list[AnyMessage],
        state: ConversationState,
        turn: Literal["user", "assistant"],
    ) -> str:
        """Build the complete prompt for escalation decision."""
        conversation = format_conversation(messages)

        # Use appropriate prompt based on whose turn it is
        prompt_template = (
            ESCALATION_DECISION_PROMPT_AFTER_USER
            if turn == "user"
            else ESCALATION_DECISION_PROMPT_AFTER_ASSISTANT
        )

        return prompt_template.format(
            failed_attempts_total=state.failed_attempts_total,
            unresolved_turns=state.unresolved_turns,
            conversation=conversation,
        )
