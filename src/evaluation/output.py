"""Output formatting for escalation analysis and metrics."""

from typing import Literal

from langchain.messages import AnyMessage

from src.decision.base import ConversationState
from src.decision.llm.schema import (
    EscalationDecisionAfterAssistant,
    EscalationDecisionAfterUser,
    EscalationDecisionBase,
)
from src.decision.utils import get_role_from_message
from src.evaluation.metrics import ClassificationMetrics, EarlyEscalationMetrics


class OutputFormatter:
    """Format and print escalation analysis and evaluation results."""

    def __init__(self, logger=None):
        """
        Initialize output formatter.

        Args:
            logger: Optional EvaluationLogger for file logging
        """
        self.logger = logger

    def _output(self, message: str, also_print: bool = True) -> None:
        """
        Output message to logger and/or console.

        Args:
            message: Message to output
            also_print: Whether to also print (only if logger exists)
        """
        if self.logger:
            self.logger.log(message, also_print=also_print)
        else:
            print(message)

    def print_header(
        self, title: str, model_name: str, additional_info: str | None = None
    ) -> None:
        """
        Print formatted section header.

        Args:
            title: Main title text
            model_name: Model being used
            additional_info: Optional additional information
        """
        self._output("=" * 70)
        self._output(title)
        self._output("=" * 70)
        self._output(f"Using model: {model_name}")
        if additional_info:
            self._output(additional_info)
        self._output("=" * 70)
        self._output("")

    def print_chat_header(self, model_name: str) -> None:
        """Print header for interactive chat session."""
        self.print_header("ESCALATION DECISION SYSTEM - Interactive Chat", model_name)
        self._output("Type 'quit' or 'exit' to end the conversation")
        self._output("=" * 70)
        self._output("")

    def print_example_header(
        self, example_num: int, total: int, conversation_id: str
    ) -> None:
        """
        Print header for dataset example.

        Args:
            example_num: Current example number
            total: Total number of examples
            conversation_id: ID of the conversation
        """
        self._output(f"{'=' * 70}", also_print=True)
        self._output(f"Example {example_num}/{total}", also_print=True)
        self._output(f"Example ID: {conversation_id}", also_print=True)

    def print_escalation_analysis(
        self,
        turn_id: int,
        decision: EscalationDecisionBase,
        state: ConversationState,
    ) -> None:
        """
        Print escalation decision analysis.

        Args:
            turn_id: Turn or example identifier
            decision: Escalation decision to display
            state: Current conversation state
        """
        self._output(f"\n--- Escalation Analysis (ID {turn_id}) ---")
        self._output(f"Escalate Now: {decision.escalate_now}")
        self._output(f"Reason Codes: {', '.join(decision.reason_codes)}")

        # Print conditional fields based on schema type
        if isinstance(decision, EscalationDecisionAfterAssistant):
            self._output(f"Failed Attempt: {decision.failed_attempt}")
        elif isinstance(decision, EscalationDecisionAfterUser):
            self._output(f"Unresolved: {decision.unresolved}")
            self._output(f"Frustration: {decision.frustration}")

        self._output(f"\nState Counters:")
        self._output(f"  Failed Attempts Total: {state.failed_attempts_total}")
        self._output(f"  Unresolved Turns: {state.unresolved_turns}")
        self._output("-" * 50)

    def print_turn_message(
        self, turn_num: int, role: Literal["user", "assistant"], message: AnyMessage
    ) -> None:
        """
        Print a conversation turn message.

        Args:
            turn_num: Turn number
            role: Role of the message sender
            message: Message to display
        """
        content_preview = (
            message.content[:100] + "..."
            if len(message.content) > 100
            else message.content
        )
        self._output(f"\nTurn {turn_num} - {role.upper()}: {content_preview}")

    def print_conversation_snippet(
        self, messages: list[AnyMessage], max_messages: int = 4
    ) -> None:
        """
        Print snippet of recent conversation messages.

        Args:
            messages: List of messages
            max_messages: Maximum number of recent messages to show
        """
        self._output("\nConversation:")
        for msg in messages[-max_messages:]:
            role = get_role_from_message(msg)
            content_preview = (
                msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            )
            self._output(f"{role}: {content_preview}")

    def print_escalation_triggered(self, turn_num: int) -> None:
        """Print escalation triggered message."""
        self._output(f"\n🚨 Escalation triggered at turn {turn_num}", also_print=True)

    def print_escalation_alert(self) -> None:
        """Print final escalation alert."""
        self._output("\n" + "=" * 70)
        self._output("🚨 ESCALATION TRIGGERED 🚨")
        self._output("This conversation should be transferred to a human.")
        self._output("=" * 70)
        self._output("")

    def print_no_escalation(self) -> None:
        """Print message when conversation completes without escalation."""
        self._output("\n✓ Conversation completed without escalation")

    def print_prediction_comparison(self, expected: bool, predicted: bool) -> None:
        """
        Print comparison of expected vs predicted escalation.

        Args:
            expected: Expected escalation value
            predicted: Predicted escalation value
        """
        match = "✓" if predicted == expected else "✗"
        self._output(
            f"\nExpected: {expected} | Predicted: {predicted} {match}", also_print=True
        )
        self._output(f"{'=' * 70}", also_print=True)

    def print_classification_metrics(self, metrics: ClassificationMetrics) -> None:
        """
        Print classification evaluation metrics.

        Args:
            metrics: Classification metrics to display
        """
        self._output("\n" + "=" * 70, also_print=True)
        self._output("EVALUATION METRICS", also_print=True)
        self._output("=" * 70, also_print=True)

        cm = metrics.confusion_matrix

        self._output(f"\nTotal examples: {cm.total}", also_print=True)
        self._output(f"Correct predictions: {cm.correct}", also_print=True)
        self._output(f"Incorrect predictions: {cm.total - cm.correct}", also_print=True)
        self._output("", also_print=True)
        self._output(f"Confusion Matrix:", also_print=True)
        self._output(f"  True Positives (TP):  {cm.true_positives}", also_print=True)
        self._output(f"  True Negatives (TN):  {cm.true_negatives}", also_print=True)
        self._output(f"  False Positives (FP): {cm.false_positives}", also_print=True)
        self._output(f"  False Negatives (FN): {cm.false_negatives}", also_print=True)
        self._output("", also_print=True)
        self._output(
            f"Accuracy:  {metrics.accuracy:.3f} ({metrics.accuracy * 100:.1f}%)",
            also_print=True,
        )
        self._output(f"Precision: {metrics.precision:.3f}", also_print=True)
        self._output(f"Recall:    {metrics.recall:.3f}", also_print=True)
        self._output(f"F1 Score:  {metrics.f1_score:.3f}", also_print=True)
        self._output("=" * 70, also_print=True)
        self._output("", also_print=True)

    def print_early_escalation_metrics(self, metrics: EarlyEscalationMetrics) -> None:
        """
        Print early escalation timing metrics.

        Args:
            metrics: Early escalation metrics to display
        """
        self._output("\n" + "=" * 70, also_print=True)
        self._output("EARLY ESCALATION METRICS", also_print=True)
        self._output("=" * 70, also_print=True)

        if metrics.true_positive_count > 0:
            self._output(
                f"\nWhen escalation WAS needed (True Positives):", also_print=True
            )
            self._output(f"  Count: {metrics.true_positive_count}", also_print=True)
            self._output(
                f"  Average turns before end: {metrics.true_positive_avg_turns_early:.1f}",
                also_print=True,
            )
            self._output(
                f"  Median turns before end: {metrics.true_positive_median_turns_early:.1f}",
                also_print=True,
            )
            self._output(f"  (how many turns early we escalated)", also_print=True)
        else:
            self._output(
                f"\nWhen escalation WAS needed (True Positives): No cases",
                also_print=True,
            )

        if metrics.false_positive_count > 0:
            self._output(
                f"\nWhen escalation was NOT needed (False Positives):", also_print=True
            )
            self._output(f"  Count: {metrics.false_positive_count}", also_print=True)
            self._output(
                f"  Average turns before end: {metrics.false_positive_avg_turns_early:.1f}",
                also_print=True,
            )
            self._output(
                f"  Median turns before end: {metrics.false_positive_median_turns_early:.1f}",
                also_print=True,
            )
            self._output(
                f"  (at what point in conversation we incorrectly escalated)",
                also_print=True,
            )
        else:
            self._output(
                f"\nWhen escalation was NOT needed (False Positives): No cases",
                also_print=True,
            )

        self._output("=" * 70, also_print=True)
        self._output("", also_print=True)
