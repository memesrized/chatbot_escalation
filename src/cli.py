"""CLI interface for escalation decision system."""

from typing import Literal

import fire
from dotenv import load_dotenv
from langchain.messages import AIMessage, HumanMessage

from src.chat_support import SupportChatbot
from src.config import Config
from src.decision.base import ConversationState
from src.decision.llm.engine import LLMEscalationClassifier
from src.decision.llm.state import update_state
from src.evaluation.logger import EvaluationLogger
from src.evaluation.output import OutputFormatter
from src.evaluation.runner import DatasetEvaluator
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
        self.output = OutputFormatter()

    def _get_model_name(self, model: str | None = None) -> str:
        """Get the model name to use (from arg or config)."""
        return model or self.config.active_model

    def _load_classifier(self, model: str | None = None) -> LLMEscalationClassifier:
        """Load the LLM-based escalation classifier."""
        escalation_model = create_chat_model(self.config, model)
        return LLMEscalationClassifier(escalation_model)

    def chat(self, model: str | None = None) -> None:
        """
        Run interactive chat session with escalation monitoring.

        Args:
            model: Optional model name to override config active_model
        """
        model_name = self._get_model_name(model)
        self.output.print_chat_header(model_name)

        # Initialize models
        if self.classifier is None:
            self.classifier = self._load_classifier(model)

        chatbot_model = create_chat_model(self.config, self.config.chatbot.model)
        chatbot = SupportChatbot(chatbot_model)

        # Run chat loop
        self._run_chat_loop(chatbot)

    def _run_chat_loop(self, chatbot: SupportChatbot) -> None:
        """
        Run the main chat loop.

        Args:
            chatbot: Initialized support chatbot
        """
        messages = []
        state = ConversationState()
        turn_n = 0
        turn: Literal["user", "assistant"] = "user"

        while True:
            if turn == "user":
                if not self._handle_user_turn(messages):
                    break
                turn_n += 1
                turn = "assistant"
            else:
                self._handle_assistant_turn(messages, chatbot)
                turn = "user"

            # Evaluate escalation
            if self._should_escalate(messages, state, turn, turn_n):
                self.output.print_escalation_alert()
                break

    def _handle_user_turn(self, messages: list) -> bool:
        """
        Handle user input turn.

        Args:
            messages: Current message history

        Returns:
            True to continue, False to exit
        """
        user_input = input("You: ").strip()

        if user_input.lower() in ["quit", "exit"]:
            print("\nEnding conversation. Goodbye!")
            return False

        if not user_input:
            return True

        messages.append(HumanMessage(content=user_input))
        return True

    def _handle_assistant_turn(
        self, messages: list, chatbot: SupportChatbot
    ) -> None:
        """
        Handle assistant response turn.

        Args:
            messages: Current message history
            chatbot: Support chatbot instance
        """
        response = chatbot.generate_response(messages)
        messages.append(AIMessage(content=response))
        print(f"\nAssistant: {response}\n")

    def _should_escalate(
        self,
        messages: list,
        state: ConversationState,
        turn: Literal["user", "assistant"],
        turn_n: int,
    ) -> bool:
        """
        Check if conversation should escalate.

        Args:
            messages: Current message history
            state: Current conversation state
            turn: Current turn
            turn_n: Turn number

        Returns:
            True if escalation needed
        """
        window_size = self.config.context_window_size
        recent_messages = messages[-window_size:]
        decision = self.classifier.decide(recent_messages, state, turn=turn)
        state = update_state(state, decision)

        self.output.print_escalation_analysis(turn_n, decision, state)
        return decision.escalate_now

    def run_dataset(
        self,
        dataset_path: str = "data/escalation_dataset.json",
        model: str | None = None,
        log_dir: str = "./logs/",
    ) -> None:
        """
        Run escalation analysis on dataset examples turn-by-turn.

        Simulates chat behavior by evaluating escalation after each message,
        stopping if escalation is triggered.

        Args:
            dataset_path: Path to JSON dataset file
            model: Optional model name to override config active_model
            log_dir: Directory to save log files (default: current directory)
        """
        model_name = self._get_model_name(model)
        
        # Setup logging
        logger = EvaluationLogger(log_dir, "turn_by_turn_eval")
        output = OutputFormatter(logger)
        
        output.print_header(
            "ESCALATION DECISION SYSTEM - Turn-by-Turn Dataset Analysis",
            model_name,
            f"Dataset: {dataset_path}",
        )

        # Initialize classifier and evaluator
        if self.classifier is None:
            self.classifier = self._load_classifier(model)

        evaluator = DatasetEvaluator(self.classifier, self.config.context_window_size, output)
        
        log_path = evaluator.run_turn_by_turn(dataset_path)
        
        if log_path:
            print(f"\nEvaluation log saved to: {log_path}")

    def run_dataset_whole_conversation(
        self,
        dataset_path: str = "data/escalation_dataset.json",
        model: str | None = None,
        log_dir: str = "./logs/",
    ) -> None:
        """
        Run escalation analysis on complete dataset conversations.

        Evaluates escalation only at the end of the full conversation.

        Args:
            dataset_path: Path to JSON dataset file
            model: Optional model name to override config active_model
            log_dir: Directory to save log files (default: current directory)
        """
        model_name = self._get_model_name(model)
        
        # Setup logging
        logger = EvaluationLogger(log_dir, "whole_conversation_eval")
        output = OutputFormatter(logger)
        
        output.print_header(
            "ESCALATION DECISION SYSTEM - Whole Conversation Dataset Analysis",
            model_name,
            f"Dataset: {dataset_path}",
        )

        # Initialize classifier and evaluator
        if self.classifier is None:
            self.classifier = self._load_classifier(model)

        evaluator = DatasetEvaluator(self.classifier, self.config.context_window_size, output)
        
        log_path = evaluator.run_whole_conversation(dataset_path)
        
        if log_path:
            print(f"\nEvaluation log saved to: {log_path}")


def main() -> None:
    """Main entry point for CLI."""
    fire.Fire(CLI)


if __name__ == "__main__":
    main()
