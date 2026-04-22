from dataclasses import dataclass
from datetime import datetime
import random


@dataclass
class TransferReceipt:
    beneficiary_name: str
    bank_name: str
    account_number: str
    amount: float
    reference_number: str
    created_at: str


class DummyBankService:
    def __init__(self) -> None:
        self.customer_name = "Naman Roy"
        self.account_number = "8745123098"
        self.balance = 50000

    def get_balance(self) -> str:
        return (
            f"Hello {self.customer_name}, your available balance is "
            f"AED {self.balance:,.2f}."
        )

    def transfer_money(
        self,
        beneficiary_name: str,
        bank_name: str,
        account_number: str,
        amount: float,
    ) -> TransferReceipt:
        reference_number = f"TXN{random.randint(100000, 999999)}"
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Deduct the amount from the balance
        self.balance -= amount

        return TransferReceipt(
            beneficiary_name=beneficiary_name,
            bank_name=bank_name,
            account_number=account_number,
            amount=amount,
            reference_number=reference_number,
            created_at=created_at,
        )
