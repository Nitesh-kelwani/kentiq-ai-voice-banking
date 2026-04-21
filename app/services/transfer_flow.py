from __future__ import annotations

from app.models.intent_models import TransferDetails


class TransferFlow:
    def __init__(self, details: TransferDetails | None = None) -> None:
        self.details = details or TransferDetails()

    def next_missing_field(self) -> str | None:
        if not self.details.beneficiary_name:
            return "beneficiary_name"
        if not self.details.bank_name:
            return "bank_name"
        if not self.details.account_number:
            return "account_number"
        if self.details.amount is None:
            return "amount"
        return None

    def is_complete(self) -> bool:
        return self.next_missing_field() is None
