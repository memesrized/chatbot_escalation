"""CLI interface for escalation decision system."""

import json
from typing import Literal

import fire
from dotenv import load_dotenv

from src.chat_support import SupportChatbot
from src.config import Config
from src.decision.base import ConversationState, Message
from src.decision.llm.engine import LLMEscalationClassifier
from src.decision.llm.schema import EscalationDecision
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
        self.classifier = None

    def _load_classifier(self, model: str | None = None) -> LLMEscalationClassifier:
        """Load the LLM-based escalation classifier."""
        escalation_model = create_chat_model(self.config, model)
        return LLMEscalationClassifier(escalation_model)
    
    def _classify_conversation(
        self,
        messages: list[Message],
        state: ConversationState,
    ) -> tuple[EscalationDecision, ConversationState]:
        """Classify escalation decision for a conversation."""
        # Get rolling window for escalation decision
        window_size = self.config.context_window_size
        recent_messages = messages[-window_size:]
        decision = self.classifier.decide(recent_messages, state)
        state = update_state(state, decision)
        return decision, state

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
        if self.classifier is None:
            self.classifier = self._load_classifier(model)

        # Initialize support chatbot with separate model
        chatbot_model = create_chat_model(self.config, self.config.chatbot.model)
        chatbot = SupportChatbot(chatbot_model)

        # Initialize state
        messages: list[Message] = []
        state = ConversationState()

        turn_n = 0

        turn: Literal["user", "assistant"] = "user"
        while True:
            if turn == "user":
                # Get user input
                user_input = input("You: ").strip()

                if user_input.lower() in ["quit", "exit"]:
                    print("\nEnding conversation. Goodbye!")
                    break

                if not user_input:
                    continue

                # Add user message
                messages.append(Message(role="user", content=user_input))

                turn_n += 1
                turn = "assistant"
            else:
                # Generate chatbot response
                response = chatbot.generate_response(messages)
                messages.append(Message(role="assistant", content=response))

                print(f"\nAssistant: {response}\n")
                turn = "user"

            # Make escalation decision
            decision, state = self._classify_conversation(messages, state)
            self._print_escalation_analysis(turn_n, decision, state)

            # Check for escalation
            if decision.escalate_now:
                print("\n" + "=" * 70)
                print("🚨 ESCALATION TRIGGERED 🚨")
                print("This conversation should be transferred to a human.")
                print("=" * 70)
                print()
                break

    def run_dataset(
        self,
        dataset_path: str = "data/escalation_dataset.json",
        model: str | None = None,
    ) -> None:
        """
        Run escalation analysis on dataset examples turn-by-turn.
        
        Simulates chat behavior by evaluating escalation after each message,
        stopping if escalation is triggered.

        Args:
            dataset_path: Path to JSON dataset file
            model: Optional model name to override config active_model
        """
        print("=" * 70)
        print("ESCALATION DECISION SYSTEM - Turn-by-Turn Dataset Analysis")
        print("=" * 70)
        print(f"Using model: {model or self.config.active_model}")
        print(f"Dataset: {dataset_path}")
        print("=" * 70)
        print()

        # Load dataset
        with open(dataset_path) as f:
            dataset = json.load(f)

        # Initialize classifier
        self.classifier = self._load_classifier(model)

        # Track predictions for metrics
        y_true = []
        y_pred = []
        
        # Track early escalation metrics
        early_escalations_when_needed = []  # length - escalation_turn when expected=true
        false_escalations = []  # length - escalation_turn when expected=false

        # Process each example
        for idx, example in enumerate(dataset, 1):
            print(f"\n{'=' * 70}")
            print(f"Example {idx}/{len(dataset)}")
            print(f"Example ID: {example['conversation_id']}")
            print(f"{'=' * 70}")

            # Convert to Message objects
            all_messages = [
                Message(role=msg["role"], content=msg["message"])
                for msg in example["conversation_history"]
            ]
            
            conversation_length = len(all_messages)

            # Initialize state
            state = ConversationState()
            messages_so_far = []
            escalated = False
            escalation_turn = None
            final_decision = None

            # Process turn by turn
            for turn_idx, message in enumerate(all_messages, 1):
                messages_so_far.append(message)
                
                # Make decision after each message
                decision, state = self._classify_conversation(messages_so_far, state)
                
                # Print message and decision
                role = message.role.upper()
                content_preview = (
                    message.content[:100] + "..." 
                    if len(message.content) > 100 
                    else message.content
                )
                print(f"\nTurn {turn_idx} - {role}: {content_preview}")
                self._print_escalation_analysis(turn_idx, decision, state)
                
                final_decision = decision
                
                # Stop if escalation triggered
                if decision.escalate_now:
                    print(f"\n🚨 Escalation triggered at turn {turn_idx}")
                    escalated = True
                    escalation_turn = turn_idx
                    break

            if not escalated:
                print("\n✓ Conversation completed without escalation")

            # Track expected vs predicted
            expected = example.get("expected_escalation") or example.get(
                "is_escalation_needed"
            )
            if expected is not None and final_decision is not None:
                y_true.append(expected)
                y_pred.append(final_decision.escalate_now)
                match = "✓" if final_decision.escalate_now == expected else "✗"
                print(
                    f"\nExpected: {expected} | "
                    f"Predicted: {final_decision.escalate_now} {match}"
                )
                
                # Track early escalation metrics
                if escalation_turn is not None:
                    turns_early = conversation_length - escalation_turn
                    if expected:  # True positive or early escalation
                        early_escalations_when_needed.append(turns_early)
                    else:  # False positive
                        false_escalations.append(turns_early)

        # Calculate and print metrics
        if y_true:
            self._print_metrics(y_true, y_pred)
            self._print_early_escalation_metrics(
                early_escalations_when_needed, 
                false_escalations
            )

    def run_dataset_whole_conversation(
        self,
        dataset_path: str = "data/escalation_dataset.json",
        model: str | None = None,
    ) -> None:
        """
        Run escalation analysis on complete dataset conversations.
        
        Evaluates escalation only at the end of the full conversation.

        Args:
            dataset_path: Path to JSON dataset file
            model: Optional model name to override config active_model
        """

        print("=" * 70)
        print("ESCALATION DECISION SYSTEM - Whole Conversation Dataset Analysis")
        print("=" * 70)
        print(f"Using model: {model or self.config.active_model}")
        print(f"Dataset: {dataset_path}")
        print("=" * 70)
        print()

        # Load dataset
        with open(dataset_path) as f:
            dataset = json.load(f)

        # Initialize classifier
        self.classifier = self._load_classifier(model)

        # Track predictions for metrics
        y_true = []
        y_pred = []

        # Process each example
        for idx, example in enumerate(dataset, 1):
            print(f"\n{'=' * 70}")
            print(f"Example {idx}/{len(dataset)}")
            print(f"Example ID: {example['conversation_id']}")
            print(f"{'=' * 70}")

            # Convert to Message objects
            messages = [
                Message(role=msg["role"], content=msg["message"])
                for msg in example["conversation_history"]
            ]

            # Use state from example or default
            state = ConversationState(
                failed_attempts_total=example.get("failed_attempts_total", 0),
                unresolved_turns=example.get("unresolved_turns", 0),
            )

            # Make decision
            decision = self.classifier.decide(messages, state)

            # Print conversation
            print("\nConversation:")
            for msg in messages[-4:]:  # Show last 4 messages
                role = msg.role.upper()
                content_preview = (
                    msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
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
        self, idx: int, decision, state: ConversationState
    ) -> None:
        """Print escalation decision analysis."""
        print(f"\n--- Escalation Analysis (ID {idx}) ---")
        print(f"Escalate Now: {decision.escalate_now}")
        print(f"Reason Codes: {', '.join(decision.reason_codes)}")
        print(f"Failed Attempt: {decision.failed_attempt}")
        print(f"Unresolved: {decision.unresolved}")
        print(f"Frustration: {decision.frustration}")
        print(f"\nState Counters:")
        print(f"  Failed Attempts Total: {state.failed_attempts_total}")
        print(f"  Unresolved Turns: {state.unresolved_turns}")
        print("-" * 50)

    # just for simplicity, not using sklearn or other libs
    def _print_metrics(self, y_true: list[bool], y_pred: list[bool]) -> None:
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

    def _print_early_escalation_metrics(
        self,
        early_escalations_when_needed: list[int],
        false_escalations: list[int],
    ) -> None:
        """
        Print metrics about early escalation timing.

        Args:
            early_escalations_when_needed: List of (length - escalation_turn) 
                when escalation was correctly needed
            false_escalations: List of (length - escalation_turn) 
                when escalation was incorrectly triggered
        """
        print("\n" + "=" * 70)
        print("EARLY ESCALATION METRICS")
        print("=" * 70)
        
        if early_escalations_when_needed:
            avg_early = sum(early_escalations_when_needed) / len(early_escalations_when_needed)
            sorted_early = sorted(early_escalations_when_needed)
            n = len(sorted_early)
            median_early = (
                sorted_early[n // 2] if n % 2 == 1
                else (sorted_early[n // 2 - 1] + sorted_early[n // 2]) / 2
            )
            print(f"\nWhen escalation WAS needed (True Positives):")
            print(f"  Count: {len(early_escalations_when_needed)}")
            print(f"  Average turns before end: {avg_early:.1f}")
            print(f"  Median turns before end: {median_early:.1f}")
            print(f"  (how many turns early we escalated)")
        else:
            print(f"\nWhen escalation WAS needed (True Positives): No cases")
        
        if false_escalations:
            avg_false = sum(false_escalations) / len(false_escalations)
            sorted_false = sorted(false_escalations)
            n = len(sorted_false)
            median_false = (
                sorted_false[n // 2] if n % 2 == 1
                else (sorted_false[n // 2 - 1] + sorted_false[n // 2]) / 2
            )
            print(f"\nWhen escalation was NOT needed (False Positives):")
            print(f"  Count: {len(false_escalations)}")
            print(f"  Average turns before end: {avg_false:.1f}")
            print(f"  Median turns before end: {median_false:.1f}")
            print(f"  (at what point in conversation we incorrectly escalated)")
        else:
            print(f"\nWhen escalation was NOT needed (False Positives): No cases")
        
        print("=" * 70)
        print()


def main() -> None:
    """Main entry point for CLI."""
    fire.Fire(CLI)


if __name__ == "__main__":
    main()
