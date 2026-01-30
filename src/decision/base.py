"""Base class for escalation decision classifiers."""

from abc import ABC, abstractmethod

from src.decision.llm.schema import EscalationDecisionBase
from src.decision.llm.state import ConversationState

from langchain.messages import AnyMessage


class BaseEscalationClassifier(ABC):
    """Base class for escalation decision classifiers."""

    @abstractmethod
    def decide(
        self, messages: list[AnyMessage], state: ConversationState, **kwargs
    ) -> EscalationDecisionBase:
        """
        Decide whether to escalate based on recent messages and state.

        Args:
            messages: Recent conversation messages (rolling window)
            state: Current conversation state with counters

        Returns:
            EscalationDecision with escalate_now flag and reason codes
        """
        pass
