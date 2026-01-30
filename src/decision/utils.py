import json
from langchain.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage

# TODO: replace with proper role handlig in the code itself
def get_role_from_message(message: AnyMessage) -> str:
    """Get the role of a message."""
    if isinstance(message, HumanMessage):
        return "user"
    elif isinstance(message, AIMessage):
        return "assistant"
    elif isinstance(message, SystemMessage):
        return "system"
    else:
        return "unknown"

def format_conversation(messages: list[AnyMessage]) -> str:
    """Format messages for the prompt."""
    return json.dumps(
        [{get_role_from_message(msg).upper(): msg.content} for msg in messages],
        ensure_ascii=False,
        # NOTE: indentation drastically increases token count
        # but for some reason improves scores, so I keep it for now
        # TODO: think about yaml or test different formats with less indentation
        indent=4,
    )
