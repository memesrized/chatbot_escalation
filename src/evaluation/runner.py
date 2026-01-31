"""Dataset evaluation runner for escalation decision system."""

import json
from dataclasses import dataclass
from typing import Literal

from langchain.messages import AIMessage, AnyMessage, HumanMessage

from src.decision.base import ConversationState
from src.decision.llm.engine import LLMEscalationClassifier
from src.decision.llm.schema import EscalationDecisionBase
from src.decision.llm.state import update_state
from src.evaluation.metrics import EscalationMetrics
from src.evaluation.output import OutputFormatter


@dataclass
class EvaluationResult:
    """Result of a single conversation evaluation."""

    conversation_id: str
    expected: bool | None
    predicted: bool
    escalated: bool
    escalation_turn: int | None
    conversation_length: int


class DatasetEvaluator:
    """Evaluate escalation decisions on dataset."""

    def __init__(
        self,
        classifier: LLMEscalationClassifier,
        context_window_size: int,
        output: OutputFormatter | None = None,
    ):
        """
        Initialize dataset evaluator.

        Args:
            classifier: LLM escalation classifier to use
            context_window_size: Size of rolling context window
            output: Optional OutputFormatter instance (creates default if not provided)
        """
        self.classifier = classifier
        self.context_window_size = context_window_size
        self.output = output or OutputFormatter()

    def _load_dataset(self, dataset_path: str) -> list[dict]:
        """
        Load dataset from JSON file.

        Args:
            dataset_path: Path to dataset JSON file

        Returns:
            List of dataset examples
        """
        with open(dataset_path) as f:
            return json.load(f)

    def _convert_to_messages(
        self, conversation_history: list[dict]
    ) -> list[AnyMessage]:
        """
        Convert conversation history to Message objects.

        Args:
            conversation_history: List of message dicts with role and message

        Returns:
            List of Message objects
        """
        return [
            (
                HumanMessage(content=msg["message"])
                if msg["role"] == "user"
                else AIMessage(content=msg["message"])
            )
            for msg in conversation_history
        ]

    def _get_expected_escalation(self, example: dict) -> bool | None:
        """
        Extract expected escalation value from example.

        Args:
            example: Dataset example

        Returns:
            Expected escalation value or None if not present
        """
        return example.get("expected_escalation") or example.get("is_escalation_needed")

    def _classify_with_window(
        self,
        messages: list[AnyMessage],
        state: ConversationState,
        turn: Literal["user", "assistant"],
    ) -> tuple[EscalationDecisionBase, ConversationState]:
        """
        Classify escalation decision using rolling window.

        Args:
            messages: All messages so far
            state: Current conversation state
            turn: Current turn (user or assistant)

        Returns:
            Tuple of (decision, updated_state)
        """
        # Get rolling window for escalation decision
        recent_messages = messages[-self.context_window_size :]
        decision = self.classifier.decide(recent_messages, state, turn=turn)
        updated_state = update_state(state, decision)
        return decision, updated_state

    def run_turn_by_turn(self, dataset_path: str) -> str:
        """
        Evaluate dataset turn-by-turn, stopping on escalation.

        Args:
            dataset_path: Path to dataset JSON file

        Returns:
            Path to log file if logger is configured, empty string otherwise
        """
        dataset = self._load_dataset(dataset_path)

        # Track predictions
        y_true = []
        y_pred = []
        early_escalations_when_needed = []
        false_escalations = []

        # Process each example
        for idx, example in enumerate(dataset, 1):
            self.output.print_example_header(
                idx, len(dataset), example["conversation_id"]
            )

            result = self._evaluate_turn_by_turn(example, idx)

            # Track metrics
            if result.expected is not None:
                y_true.append(result.expected)
                y_pred.append(result.predicted)
                # Print expected vs predicted escalation turn
                if result.expected:
                    expected_turn = result.conversation_length
                else:
                    expected_turn = f"no (length {result.conversation_length})"
                predicted_turn = result.escalation_turn if result.predicted else None
                self.output._output(
                    f"Expected escalation turn: {expected_turn} | Predicted turn: {predicted_turn}",
                    also_print=True,
                )
                self.output.print_prediction_comparison(
                    result.expected, result.predicted
                )

                # Track early escalation
                if result.escalation_turn is not None:
                    turns_early = result.conversation_length - result.escalation_turn
                    if result.expected:
                        early_escalations_when_needed.append(turns_early)
                    else:
                        false_escalations.append(turns_early)

        # Print metrics
        if y_true:
            metrics = EscalationMetrics.calculate_metrics(y_true, y_pred)
            self.output.print_classification_metrics(metrics)

            early_metrics = EscalationMetrics.calculate_early_escalation_metrics(
                early_escalations_when_needed, false_escalations
            )
            self.output.print_early_escalation_metrics(early_metrics)

        # Return log file path if logger exists
        if hasattr(self.output, "logger") and self.output.logger:
            return self.output.logger.get_log_path()
        return ""

    def _evaluate_turn_by_turn(
        self, example: dict, example_idx: int
    ) -> EvaluationResult:
        """
        Evaluate single example turn-by-turn.

        Args:
            example: Dataset example
            example_idx: Index of example for display

        Returns:
            EvaluationResult with evaluation details
        """
        conversation_length = len(example["conversation_history"])
        state = ConversationState()
        messages_so_far = []
        escalated = False
        escalation_turn = None
        final_decision = None

        # Process turn by turn
        for turn_idx, msg_dict in enumerate(example["conversation_history"], 1):
            turn = msg_dict["role"]
            message = (
                HumanMessage(content=msg_dict["message"])
                if turn == "user"
                else AIMessage(content=msg_dict["message"])
            )
            messages_so_far.append(message)

            # Make decision after each message
            decision, state = self._classify_with_window(messages_so_far, state, turn)

            # Don't display turn and decision details
            # self.output.print_turn_message(turn_idx, turn, message)
            # self.output.print_escalation_analysis(turn_idx, decision, state)

            final_decision = decision

            # Stop if escalation triggered
            if decision.escalate_now:
                # self.output.print_escalation_triggered(turn_idx)
                escalated = True
                escalation_turn = turn_idx
                break

        # Don't print no escalation message
        # if not escalated:
        #     self.output.print_no_escalation()

        expected = self._get_expected_escalation(example)
        predicted = final_decision.escalate_now if final_decision else False

        return EvaluationResult(
            conversation_id=example["conversation_id"],
            expected=expected,
            predicted=predicted,
            escalated=escalated,
            escalation_turn=escalation_turn,
            conversation_length=conversation_length,
        )

    def run_whole_conversation(self, dataset_path: str) -> str:
        """
        Evaluate dataset on complete conversations.

        Args:
            dataset_path: Path to dataset JSON file

        Returns:
            Path to log file if logger is configured, empty string otherwise
        """
        dataset = self._load_dataset(dataset_path)

        # Track predictions
        y_true = []
        y_pred = []

        # Process each example
        for idx, example in enumerate(dataset, 1):
            self.output.print_example_header(
                idx, len(dataset), example["conversation_id"]
            )

            result = self._evaluate_whole_conversation(example, idx)

            # Track metrics
            if result.expected is not None:
                y_true.append(result.expected)
                y_pred.append(result.predicted)
                self.output.print_prediction_comparison(
                    result.expected, result.predicted
                )

        # Print metrics
        if y_true:
            metrics = EscalationMetrics.calculate_metrics(y_true, y_pred)
            self.output.print_classification_metrics(metrics)

        # Return log file path if logger exists
        if hasattr(self.output, "logger") and self.output.logger:
            return self.output.logger.get_log_path()
        return ""

    def _evaluate_whole_conversation(
        self, example: dict, example_idx: int
    ) -> EvaluationResult:
        """
        Evaluate single example on complete conversation.

        Args:
            example: Dataset example
            example_idx: Index of example for display

        Returns:
            EvaluationResult with evaluation details
        """
        # Convert to messages
        messages = self._convert_to_messages(example["conversation_history"])

        # Initialize state from example or use defaults
        state = ConversationState(
            failed_attempts_total=example.get("failed_attempts_total", 0),
            unresolved_turns=example.get("unresolved_turns", 0),
        )

        # Determine turn based on last message
        turn = example["conversation_history"][-1]["role"]

        # Make decision
        decision = self.classifier.decide(messages, state, turn)

        # Don't display conversation and decision details
        # self.output.print_conversation_snippet(messages)
        # self.output.print_escalation_analysis(example_idx, decision, state)

        expected = self._get_expected_escalation(example)

        return EvaluationResult(
            conversation_id=example["conversation_id"],
            expected=expected,
            predicted=decision.escalate_now,
            escalated=decision.escalate_now,
            escalation_turn=(
                len(example["conversation_history"]) if decision.escalate_now else None
            ),
            conversation_length=len(example["conversation_history"]),
        )
