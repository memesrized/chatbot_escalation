"""Streamlit UI for escalation decision system."""

import streamlit as st
from dotenv import load_dotenv

from src.chat_support.core import SupportChatbot
from src.config.load import Config
from src.decision.base import ConversationState, Message
from src.decision.llm.engine import LLMEscalationClassifier
from src.decision.llm.state import update_state
from src.llm.factory import create_chat_model


def init_session_state() -> None:
    """Initialize Streamlit session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "state" not in st.session_state:
        st.session_state.state = ConversationState()
    if "escalated" not in st.session_state:
        st.session_state.escalated = False
    if "turn" not in st.session_state:
        st.session_state.turn = 0


def main() -> None:
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Escalation Decision System",
        page_icon="🎯",
        layout="wide",
    )

    st.title("🎯 Escalation Decision System")
    st.markdown("**Interactive chat with real-time escalation monitoring**")

    # Load environment and config
    load_dotenv()
    config = Config.load("configs/config.yaml")

    # Initialize session state
    init_session_state()

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Model selection
        model_name = st.selectbox(
            "Escalation Model",
            options=list(config.models.keys()),
            index=list(config.models.keys()).index(config.active_model),
        )

        st.divider()

        # Display current state
        st.header("📊 State Counters")
        st.metric(
            "Failed Attempts",
            st.session_state.state.failed_attempts_total,
        )
        st.metric("Unresolved Turns", st.session_state.state.unresolved_turns)

        st.divider()

        # Reset button
        if st.button("🔄 Reset Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.state = ConversationState()
            st.session_state.escalated = False
            st.session_state.turn = 0
            st.rerun()

    # Initialize models (cached)
    @st.cache_resource
    def get_models(model_name: str):
        escalation_model = create_chat_model(config, model_name)
        classifier = LLMEscalationClassifier(escalation_model)

        chatbot_model = create_chat_model(config, config.chatbot.model)
        chatbot = SupportChatbot(chatbot_model)

        return classifier, chatbot

    classifier, chatbot = get_models(model_name)

    # Main chat area
    chat_container = st.container()

    # Display chat history
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Show escalation alert if escalated
    if st.session_state.escalated:
        st.error(
            "🚨 **ESCALATION TRIGGERED** - "
            "This conversation should be transferred to a human agent.",
            icon="🚨",
        )

    # Chat input
    if not st.session_state.escalated:
        if prompt := st.chat_input("Type your message..."):
            # Add user message
            st.session_state.messages.append(
                {"role": "user", "content": prompt}
            )
            st.session_state.turn += 1

            # Display user message
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            # Convert to Message objects
            message_objs = [
                Message(role=msg["role"], content=msg["content"])
                for msg in st.session_state.messages
            ]

            # Generate chatbot response
            with st.spinner("Assistant is thinking..."):
                response = chatbot.generate_response(message_objs)

            # Add assistant message
            st.session_state.messages.append(
                {"role": "assistant", "content": response}
            )
            message_objs.append(Message(role="assistant", content=response))

            # Display assistant message
            with chat_container:
                with st.chat_message("assistant"):
                    st.markdown(response)

            # Make escalation decision
            window_size = config.context_window_size
            recent_messages = message_objs[-window_size:]

            with st.spinner("Analyzing escalation..."):
                decision = classifier.decide(
                    recent_messages, st.session_state.state
                )

            # Update state
            st.session_state.state = update_state(
                st.session_state.state, decision
            )

            # Display escalation panel
            with st.expander(
                f"🔍 Escalation Analysis - Turn {st.session_state.turn}",
                expanded=decision.escalate_now,
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Decision**")
                    if decision.escalate_now:
                        st.error("⚠️ Escalate Now: YES")
                    else:
                        st.success("✓ Escalate Now: NO")

                    st.markdown("**Signals**")
                    st.write(f"Failed Attempt: {decision.failed_attempt}")
                    st.write(f"Unresolved: {decision.unresolved}")
                    st.write(f"Frustration: {decision.frustration}")

                with col2:
                    st.markdown("**Reason Codes**")
                    for code in decision.reason_codes:
                        st.write(f"• {code}")

            # Check for escalation
            if decision.escalate_now:
                st.session_state.escalated = True
                st.rerun()
    else:
        st.info(
            "💡 Use the **Reset Conversation** button in the sidebar "
            "to start a new session."
        )


if __name__ == "__main__":
    main()
