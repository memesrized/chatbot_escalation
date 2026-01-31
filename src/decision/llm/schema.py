"""Schema definitions for escalation decision output."""

from typing import Literal

from pydantic import BaseModel, Field

# User-based reason codes (when last message is from user)
UserEscalationReason = Literal[
    "USER_REQUESTED_HUMAN",
    "CHURN_RISK",
    "INSTRUCTIONS_DID_NOT_WORK",
    "URGENT_OR_HIGH_STAKES",
]

UserNonEscalationReason = Literal[
    "HOW_TO_SOLVABLE",
    "RESOLVED_CONFIRMED",
    "SMALL_TALK_OR_GREETING",
    "TROUBLESHOOTING_IN_PROGRESS",
    "NEED_MORE_INFO",
]

# Assistant-based reason codes (when last message is from assistant)
AssistantEscalationReason = Literal[
    "REPEATED_FAILURE",
    "ASSISTANT_IRRELEVANT_OR_INCOMPLETE",
    "CAPABILITY_OR_POLICY_BLOCK",
]

AssistantNonEscalationReason = Literal[
    "TROUBLESHOOTING_IN_PROGRESS",
    "NEED_MORE_INFO",
]

FrustrationLevel = Literal["none", "mild", "high"]


# TODO: test if this lond descriptions here work with prompt caching
# not sure if this description goes in the beginning of the prompt
# so we may need to move it to the prompt template instead
# and acually the same goes for the other fields too
class EscalationDecisionBase(BaseModel):
    """
    Base structured output from escalation decision model.

    This schema defines the common fields expected from the LLM when
    determining whether to escalate a conversation to a human agent.
    """

    escalate_now: bool = Field(
        description=(
            "Whether the conversation should be escalated to a human "
            "at this step. Set to true if any escalation criterion is met: "
            "user explicitly requests human assistance, shows strong "
            "frustration or churn risk, assistant repeatedly fails to make "
            "progress, assistant response is irrelevant/incomplete, "
            "provided instructions didn't work, issue is urgent/high-stakes "
            "and unresolved, or assistant cannot perform required action "
            "due to capability/policy constraints. Set to false if the "
            "request is solvable via how-to instructions, issue is resolved "
            "and confirmed, conversation is small talk/greeting, "
            "troubleshooting is progressing without frustration, or more "
            "information is needed and user is cooperating."
        )
    )


class EscalationDecisionAfterUser(EscalationDecisionBase):
    """
    Escalation decision when last message is from user.

    Uses user-based reason codes and includes unresolved field.
    """

    reason_codes: list[UserEscalationReason | UserNonEscalationReason] = Field(
        description=(
            "One or more reason codes explaining the escalation decision. "
            "\n\n"
            "ESCALATION REASONS (use when escalation is needed):\n"
            "- USER_REQUESTED_HUMAN: User explicitly asks to escalate or speak to a human representative.\n"
            "- CHURN_RISK: User shows strong frustration or threatens to leave the service.\n"
            "- INSTRUCTIONS_DID_NOT_WORK: The user followed the provided steps, but the problem still persists.\n"
            "- URGENT_OR_HIGH_STAKES: The case is urgent or high-stakes (especially money-related issues like missing funds) and remains unresolved.\n"
            "\n"
            "NON-ESCALATION REASONS (use when escalation is not needed):\n"
            "- HOW_TO_SOLVABLE: The request is a straightforward how-to and the assistant can provide clear, actionable instructions.\n"
            "- RESOLVED_CONFIRMED: The user confirms the problem is solved or says they do not need more help.\n"
            "- SMALL_TALK_OR_GREETING: There is no support request (only greeting / small talk).\n"
            "- TROUBLESHOOTING_IN_PROGRESS: Troubleshooting is ongoing and progressing, without explicit escalation request or strong frustration.\n"
            "- NEED_MORE_INFO: The assistant asks reasonable clarifying questions to proceed, and the user is cooperating."
        )
    )

    frustration: FrustrationLevel = Field(
        description=(
            "Coarse estimate of user frustration level. 'none': user is "
            "calm and cooperative. 'mild': user shows some impatience or "
            "mild dissatisfaction. 'high': user shows strong frustration, "
            "anger, or threatens to leave the service."
        )
    )

    unresolved: bool = Field(
        description=(
            "Whether the user's issue is still unresolved after the latest "
            "exchange. Examples: user indicates problem persists ('still not "
            "working', 'same issue'), user repeats request/complaint, or "
            "troubleshooting continues without confirmed resolution."
        )
    )


class EscalationDecisionAfterAssistant(EscalationDecisionBase):
    """
    Escalation decision when last message is from assistant.

    Uses assistant-based reason codes and includes failed_attempt field.
    """

    reason_codes: list[AssistantEscalationReason | AssistantNonEscalationReason] = (
        Field(
            description=(
                "One or more reason codes explaining the escalation decision. "
                "\n\n"
                "ESCALATION REASONS (use when escalation is needed):\n"
                "- REPEATED_FAILURE: The assistant keeps failing to make progress, repeating itself, or the conversation is stuck.\n"
                "- ASSISTANT_IRRELEVANT_OR_INCOMPLETE: The assistant's response is irrelevant, lacks needed info, or does not answer the user's actual question.\n"
                "- CAPABILITY_OR_POLICY_BLOCK: The assistant cannot perform the required action due to capability or policy constraints, and human intervention is needed.\n"
                "\n"
                "NON-ESCALATION REASONS (use when escalation is not needed):\n"
                "- TROUBLESHOOTING_IN_PROGRESS: Troubleshooting is ongoing and progressing, without explicit escalation request or strong frustration.\n"
                "- NEED_MORE_INFO: The assistant asks reasonable clarifying questions to proceed, and the user is cooperating."
            )
        )
    )

    failed_attempt: bool = Field(
        description=(
            "Whether the assistant's last response failed to provide a "
            "meaningful, actionable answer. Examples: generic apology with "
            "no next steps, refusal without actionable alternative, "
            "irrelevant answer not addressing user's question, or "
            "'something went wrong' type response."
        )
    )
