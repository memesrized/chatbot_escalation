"""Base class for escalation decision classifiers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.decision.llm.schema import EscalationDecision


@dataclass
class Message:
    """A single message in the conversation."""

    role: str  # "user" or "assistant"
    content: str


@dataclass
class ConversationState:
    """State tracked across conversation turns."""

    failed_attempts_total: int = 0
    unresolved_turns: int = 0


class BaseEscalationClassifier(ABC):
    """Base class for escalation decision classifiers."""

    @abstractmethod
    def decide(
        self, messages: list[Message], state: ConversationState, **kwargs
    ) -> EscalationDecision:
        """
        Decide whether to escalate based on recent messages and state.

        Args:
            messages: Recent conversation messages (rolling window)
            state: Current conversation state with counters

        Returns:
            EscalationDecision with escalate_now flag and reason codes
        """
        pass
