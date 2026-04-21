from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TransferDetails:
    beneficiary_name: str | None = None
    bank_name: str | None = None
    account_number: str | None = None
    amount: float | None = None
    confirmation: bool | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "TransferDetails":
        payload = payload or {}
        amount = payload.get("amount")
        try:
            parsed_amount = float(amount) if amount not in (None, "") else None
        except (TypeError, ValueError):
            parsed_amount = None

        account_number = payload.get("account_number")
        if account_number is not None:
            account_number = "".join(character for character in str(account_number) if character.isdigit())

        return cls(
            beneficiary_name=payload.get("beneficiary_name") or None,
            bank_name=payload.get("bank_name") or None,
            account_number=account_number or None,
            amount=parsed_amount,
            confirmation=payload.get("confirmation"),
        )

    def merge(self, other: "TransferDetails") -> None:
        if other.beneficiary_name:
            self.beneficiary_name = other.beneficiary_name
        if other.bank_name:
            self.bank_name = other.bank_name
        if other.account_number:
            self.account_number = other.account_number
        if other.amount is not None:
            self.amount = other.amount
        if other.confirmation is not None:
            self.confirmation = other.confirmation


@dataclass
class StructuredIntent:
    name: str
    original_text: str
    confidence: float = 0.0
    needs_clarification: bool = False
    clarification_question: str = ""
    assistant_reply: str = ""
    transfer: TransferDetails = field(default_factory=TransferDetails)

    @classmethod
    def from_dict(cls, payload: dict[str, Any], original_text: str) -> "StructuredIntent":
        confidence = payload.get("confidence", 0.0)
        try:
            parsed_confidence = float(confidence)
        except (TypeError, ValueError):
            parsed_confidence = 0.0

        return cls(
            name=(payload.get("intent") or "unknown").strip().lower(),
            original_text=original_text,
            confidence=parsed_confidence,
            needs_clarification=bool(payload.get("needs_clarification", False)),
            clarification_question=(payload.get("clarification_question") or "").strip(),
            assistant_reply=(payload.get("assistant_reply") or "").strip(),
            transfer=TransferDetails.from_dict(payload.get("transfer_details")),
        )
