"""CLI interface for escalation decision system."""

import os
from pathlib import Path

import fire
from dotenv import load_dotenv

from src.chat_support.core import SupportChatbot
from src.config.load_config import Config
from src.decision.base import ConversationState, Message
from src.decision.llm.engine import LLMEscalationClassifier
from src.decision.llm.state import update_state
from src.llm.factory import create_chat_model


class CLI:
    """Command-line interface for the escalation decision system."""

    def __init__(self, config_path: str = "configs/config.yaml"):
        """
        Initialize CLI with configuration.

        Args:
            config_path: Path to YAML configuration file
        """
        load_dotenv()
        self.config = Config.load(config_path)

    def chat(self, model: str | None = None) -> None:
        """
        Run interactive chat session with escalation monitoring.

        Args:
            model: Optional model name to override config active_model
        """
        print("=" * 70)
        print("ESCALATION DECISION SYSTEM - Interactive Chat")
        print("=" * 70)
        print(f"Using model: {model or self.config.active_model}")
        print("Type 'quit' or 'exit' to end the conversation")
        print("=" * 70)
        print()

        # Initialize models
        escalation_model = create_chat_model(self.config, model)
        classifier = LLMEscalationClassifier(escalation_model)

        # Initialize support chatbot with separate model
        chatbot_config = self.config.get_model_config(
            self.config.chatbot.model
        )
        chatbot_model = create_chat_model(
            self.config, self.config.chatbot.model
        )
        chatbot = SupportChatbot(chatbot_model)

        # Initialize state
        messages: list[Message] = []
        state = ConversationState()

        turn = 0

        while True:
            # Get user input
            user_input = input("You: ").strip()

            if user_input.lower() in ["quit", "exit"]:
                print("\nEnding conversation. Goodbye!")
                break

            if not user_input:
                continue

            turn += 1

            # Add user message
            messages.append(Message(role="user", content=user_input))

            # Generate chatbot response
            response = chatbot.generate_response(messages)
            messages.append(Message(role="assistant", content=response))

            print(f"\nAssistant: {response}\n")

            # Get rolling window for escalation decision
            window_size = self.config.context_window_size
            recent_messages = messages[-window_size:]

            # Make escalation decision
            decision = classifier.decide(recent_messages, state)

            # Update state
            state = update_state(state, decision)

            # Print escalation analysis
            self._print_escalation_analysis(turn, decision, state)

            # Check for escalation
            if decision.escalate_now:
                print("\n" + "=" * 70)
                print("🚨 ESCALATION TRIGGERED 🚨")
                print("This conversation should be transferred to a human.")
                print("=" * 70)
                print()
                break

    def run_dataset(
        self, dataset_path: str = "data/escalation_dataset.json", 
        model: str | None = None
    ) -> None:
        """
        Run escalation analysis on dataset examples.

        Args:
            dataset_path: Path to JSON dataset file
            model: Optional model name to override config active_model
        """
        import json

        print("=" * 70)
        print("ESCALATION DECISION SYSTEM - Dataset Analysis")
        print("=" * 70)
        print(f"Using model: {model or self.config.active_model}")
        print(f"Dataset: {dataset_path}")
        print("=" * 70)
        print()

        # Load dataset
        with open(dataset_path) as f:
            dataset = json.load(f)

        # Initialize classifier
        escalation_model = create_chat_model(self.config, model)
        classifier = LLMEscalationClassifier(escalation_model)

        # Track predictions for metrics
        y_true = []
        y_pred = []

        # Process each example
        for idx, example in enumerate(dataset, 1):
            print(f"\n{'=' * 70}")
            print(f"Example {idx}/{len(dataset)}")
            print(f"{'=' * 70}")

            # Convert to Message objects
            # Handle both "messages" and "conversation_history" formats
            conv_history = example.get("messages") or example.get(
                "conversation_history", []
            )
            messages = []
            for msg in conv_history:
                # Handle both "content"/"message" and "role"/"bot" formats
                role = msg.get("role", "user")
                if role == "bot":
                    role = "assistant"
                content = msg.get("content") or msg.get("message", "")
                messages.append(Message(role=role, content=content))

            # Use state from example or default
            state = ConversationState(
                failed_attempts_total=example.get("failed_attempts_total", 0),
                unresolved_turns=example.get("unresolved_turns", 0),
            )

            # Make decision
            decision = classifier.decide(messages, state)

            # Print conversation
            print("\nConversation:")
            for msg in messages[-4:]:  # Show last 4 messages
                role = msg.role.upper()
                content_preview = (
                    msg.content[:100] + "..."
                    if len(msg.content) > 100
                    else msg.content
                )
                print(f"{role}: {content_preview}")

            # Print decision
            self._print_escalation_analysis(idx, decision, state)

            # Track expected vs predicted
            expected = example.get("expected_escalation") or example.get(
                "is_escalation_needed"
            )
            if expected is not None:
                y_true.append(expected)
                y_pred.append(decision.escalate_now)
                match = "✓" if decision.escalate_now == expected else "✗"
                print(
                    f"\nExpected: {expected} | "
                    f"Predicted: {decision.escalate_now} {match}"
                )

        # Calculate and print metrics
        if y_true:
            self._print_metrics(y_true, y_pred)

    def _print_escalation_analysis(
        self, turn: int, decision, state: ConversationState
    ) -> None:
        """Print escalation decision analysis."""
        print(f"\n--- Escalation Analysis (Turn {turn}) ---")
        print(f"Escalate Now: {decision.escalate_now}")
        print(f"Reason Codes: {', '.join(decision.reason_codes)}")
        print(f"Failed Attempt: {decision.failed_attempt}")
        print(f"Unresolved: {decision.unresolved}")
        print(f"Frustration: {decision.frustration}")
        print(f"\nState Counters:")
        print(f"  Failed Attempts Total: {state.failed_attempts_total}")
        print(f"  Unresolved Turns: {state.unresolved_turns}")
        print("-" * 50)

    def _print_metrics(
        self, y_true: list[bool], y_pred: list[bool]
    ) -> None:
        """
        Calculate and print evaluation metrics.

        Args:
            y_true: List of expected escalation decisions
            y_pred: List of predicted escalation decisions
        """
        print("\n" + "=" * 70)
        print("EVALUATION METRICS")
        print("=" * 70)

        # Calculate confusion matrix components
        tp = sum(1 for t, p in zip(y_true, y_pred) if t and p)
        tn = sum(1 for t, p in zip(y_true, y_pred) if not t and not p)
        fp = sum(1 for t, p in zip(y_true, y_pred) if not t and p)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t and not p)

        total = len(y_true)
        correct = tp + tn

        # Calculate accuracy
        accuracy = correct / total if total > 0 else 0.0

        # Calculate precision, recall, and F1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        print(f"\nTotal examples: {total}")
        print(f"Correct predictions: {correct}")
        print(f"Incorrect predictions: {total - correct}")
        print()
        print(f"Confusion Matrix:")
        print(f"  True Positives (TP):  {tp}")
        print(f"  True Negatives (TN):  {tn}")
        print(f"  False Positives (FP): {fp}")
        print(f"  False Negatives (FN): {fn}")
        print()
        print(f"Accuracy:  {accuracy:.3f} ({accuracy * 100:.1f}%)")
        print(f"Precision: {precision:.3f}")
        print(f"Recall:    {recall:.3f}")
        print(f"F1 Score:  {f1:.3f}")
        print("=" * 70)
        print()


def main() -> None:
    """Main entry point for CLI."""
    fire.Fire(CLI)


if __name__ == "__main__":
    main()
