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

    @staticmethod
    def print_header(
        title: str, model_name: str, additional_info: str | None = None
    ) -> None:
        """
        Print formatted section header.

        Args:
            title: Main title text
            model_name: Model being used
            additional_info: Optional additional information
        """
        print("=" * 70)
        print(title)
        print("=" * 70)
        print(f"Using model: {model_name}")
        if additional_info:
            print(additional_info)
        print("=" * 70)
        print()

    @staticmethod
    def print_chat_header(model_name: str) -> None:
        """Print header for interactive chat session."""
        OutputFormatter.print_header(
            "ESCALATION DECISION SYSTEM - Interactive Chat", model_name
        )
        print("Type 'quit' or 'exit' to end the conversation")
        print("=" * 70)
        print()

    @staticmethod
    def print_example_header(
        example_num: int, total: int, conversation_id: str
    ) -> None:
        """
        Print header for dataset example.

        Args:
            example_num: Current example number
            total: Total number of examples
            conversation_id: ID of the conversation
        """
        print(f"\n{'=' * 70}")
        print(f"Example {example_num}/{total}")
        print(f"Example ID: {conversation_id}")
        print(f"{'=' * 70}")

    @staticmethod
    def print_escalation_analysis(
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
        print(f"\n--- Escalation Analysis (ID {turn_id}) ---")
        print(f"Escalate Now: {decision.escalate_now}")
        print(f"Reason Codes: {', '.join(decision.reason_codes)}")

        # Print conditional fields based on schema type
        if isinstance(decision, EscalationDecisionAfterAssistant):
            print(f"Failed Attempt: {decision.failed_attempt}")
        elif isinstance(decision, EscalationDecisionAfterUser):
            print(f"Unresolved: {decision.unresolved}")
            print(f"Frustration: {decision.frustration}")

        print(f"\nState Counters:")
        print(f"  Failed Attempts Total: {state.failed_attempts_total}")
        print(f"  Unresolved Turns: {state.unresolved_turns}")
        print("-" * 50)

    @staticmethod
    def print_turn_message(
        turn_num: int, role: Literal["user", "assistant"], message: AnyMessage
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
        print(f"\nTurn {turn_num} - {role.upper()}: {content_preview}")

    @staticmethod
    def print_conversation_snippet(messages: list[AnyMessage], max_messages: int = 4) -> None:
        """
        Print snippet of recent conversation messages.

        Args:
            messages: List of messages
            max_messages: Maximum number of recent messages to show
        """
        print("\nConversation:")
        for msg in messages[-max_messages:]:
            role = get_role_from_message(msg)
            content_preview = (
                msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            )
            print(f"{role}: {content_preview}")

    @staticmethod
    def print_escalation_triggered(turn_num: int) -> None:
        """Print escalation triggered message."""
        print(f"\n🚨 Escalation triggered at turn {turn_num}")

    @staticmethod
    def print_escalation_alert() -> None:
        """Print final escalation alert."""
        print("\n" + "=" * 70)
        print("🚨 ESCALATION TRIGGERED 🚨")
        print("This conversation should be transferred to a human.")
        print("=" * 70)
        print()

    @staticmethod
    def print_no_escalation() -> None:
        """Print message when conversation completes without escalation."""
        print("\n✓ Conversation completed without escalation")

    @staticmethod
    def print_prediction_comparison(expected: bool, predicted: bool) -> None:
        """
        Print comparison of expected vs predicted escalation.

        Args:
            expected: Expected escalation value
            predicted: Predicted escalation value
        """
        match = "✓" if predicted == expected else "✗"
        print(f"\nExpected: {expected} | Predicted: {predicted} {match}")

    @staticmethod
    def print_classification_metrics(metrics: ClassificationMetrics) -> None:
        """
        Print classification evaluation metrics.

        Args:
            metrics: Classification metrics to display
        """
        print("\n" + "=" * 70)
        print("EVALUATION METRICS")
        print("=" * 70)

        cm = metrics.confusion_matrix

        print(f"\nTotal examples: {cm.total}")
        print(f"Correct predictions: {cm.correct}")
        print(f"Incorrect predictions: {cm.total - cm.correct}")
        print()
        print(f"Confusion Matrix:")
        print(f"  True Positives (TP):  {cm.true_positives}")
        print(f"  True Negatives (TN):  {cm.true_negatives}")
        print(f"  False Positives (FP): {cm.false_positives}")
        print(f"  False Negatives (FN): {cm.false_negatives}")
        print()
        print(f"Accuracy:  {metrics.accuracy:.3f} ({metrics.accuracy * 100:.1f}%)")
        print(f"Precision: {metrics.precision:.3f}")
        print(f"Recall:    {metrics.recall:.3f}")
        print(f"F1 Score:  {metrics.f1_score:.3f}")
        print("=" * 70)
        print()

    @staticmethod
    def print_early_escalation_metrics(metrics: EarlyEscalationMetrics) -> None:
        """
        Print early escalation timing metrics.

        Args:
            metrics: Early escalation metrics to display
        """
        print("\n" + "=" * 70)
        print("EARLY ESCALATION METRICS")
        print("=" * 70)

        if metrics.true_positive_count > 0:
            print(f"\nWhen escalation WAS needed (True Positives):")
            print(f"  Count: {metrics.true_positive_count}")
            print(f"  Average turns before end: {metrics.true_positive_avg_turns_early:.1f}")
            print(f"  Median turns before end: {metrics.true_positive_median_turns_early:.1f}")
            print(f"  (how many turns early we escalated)")
        else:
            print(f"\nWhen escalation WAS needed (True Positives): No cases")

        if metrics.false_positive_count > 0:
            print(f"\nWhen escalation was NOT needed (False Positives):")
            print(f"  Count: {metrics.false_positive_count}")
            print(f"  Average turns before end: {metrics.false_positive_avg_turns_early:.1f}")
            print(f"  Median turns before end: {metrics.false_positive_median_turns_early:.1f}")
            print(f"  (at what point in conversation we incorrectly escalated)")
        else:
            print(f"\nWhen escalation was NOT needed (False Positives): No cases")

        print("=" * 70)
        print()
