"""Schema definitions for escalation decision output."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class EscalationReason(str, Enum):
    """Reason codes indicating escalation is needed."""

    USER_REQUESTED_HUMAN = "USER_REQUESTED_HUMAN"
    CHURN_RISK = "CHURN_RISK"
    REPEATED_FAILURE = "REPEATED_FAILURE"
    ASSISTANT_IRRELEVANT_OR_INCOMPLETE = "ASSISTANT_IRRELEVANT_OR_INCOMPLETE"
    INSTRUCTIONS_DID_NOT_WORK = "INSTRUCTIONS_DID_NOT_WORK"
    URGENT_OR_HIGH_STAKES = "URGENT_OR_HIGH_STAKES"
    CAPABILITY_OR_POLICY_BLOCK = "CAPABILITY_OR_POLICY_BLOCK"


class NonEscalationReason(str, Enum):
    """Reason codes indicating escalation is not needed."""

    HOW_TO_SOLVABLE = "HOW_TO_SOLVABLE"
    RESOLVED_CONFIRMED = "RESOLVED_CONFIRMED"
    SMALL_TALK_OR_GREETING = "SMALL_TALK_OR_GREETING"
    TROUBLESHOOTING_IN_PROGRESS = "TROUBLESHOOTING_IN_PROGRESS"
    NEED_MORE_INFO = "NEED_MORE_INFO"


FrustrationLevel = Literal["none", "mild", "high"]


class EscalationDecision(BaseModel):
    """
    Structured output from escalation decision model.

    This schema defines the exact format expected from the LLM when
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

    reason_codes: list[EscalationReason | NonEscalationReason] = Field(
        description=(
            "One or more reason codes explaining the escalation decision. "
            "Use escalation codes (USER_REQUESTED_HUMAN, CHURN_RISK, "
            "REPEATED_FAILURE, ASSISTANT_IRRELEVANT_OR_INCOMPLETE, "
            "INSTRUCTIONS_DID_NOT_WORK, URGENT_OR_HIGH_STAKES, "
            "CAPABILITY_OR_POLICY_BLOCK) when escalation is needed. "
            "Use non-escalation codes (HOW_TO_SOLVABLE, RESOLVED_CONFIRMED, "
            "SMALL_TALK_OR_GREETING, TROUBLESHOOTING_IN_PROGRESS, "
            "NEED_MORE_INFO) when escalation is not needed."
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

    unresolved: bool = Field(
        description=(
            "Whether the user's issue is still unresolved after the latest "
            "exchange. Examples: user indicates problem persists ('still not "
            "working', 'same issue'), user repeats request/complaint, or "
            "troubleshooting continues without confirmed resolution."
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
