"""Support chatbot implementation."""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage

from src.chat_support.prompt import SUPPORT_CHATBOT_PROMPT
from langchain.messages import AnyMessage


class SupportChatbot:
    """Support chatbot for handling user queries."""

    def __init__(self, model: BaseChatModel):
        """
        Initialize the support chatbot.

        Args:
            model: LangChain chat model for generating responses
        """
        self.model = model
        self.system_message = SystemMessage(content=SUPPORT_CHATBOT_PROMPT)

    def generate_response(self, messages: list[AnyMessage]) -> str:
        """
        Generate a response to the user's message.

        Args:
            messages: Conversation history

        Returns:
            Assistant's response text
        """
        # Convert to LangChain message format
        response = self.model.invoke([self.system_message] + messages)
        return response.content
