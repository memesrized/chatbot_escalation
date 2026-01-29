"""Support chatbot implementation."""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.chat_support.prompt import SUPPORT_CHATBOT_PROMPT
from src.decision.base import Message


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

    def generate_response(self, messages: list[Message]) -> str:
        """
        Generate a response to the user's message.

        Args:
            messages: Conversation history

        Returns:
            Assistant's response text
        """
        # Convert to LangChain message format
        langchain_messages = [self.system_message]

        for msg in messages:
            if msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))

        response = self.model.invoke(langchain_messages)
        return response.content
