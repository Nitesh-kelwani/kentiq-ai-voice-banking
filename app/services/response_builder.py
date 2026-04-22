from __future__ import annotations

from app.banking.dummy_bank import TransferReceipt
from app.config import UNKNOWN_COMMAND_MESSAGE, WELCOME_MESSAGE
from app.models.intent_models import StructuredIntent, TransferDetails


class ResponseBuilder:
    def welcome(self) -> str:
        return WELCOME_MESSAGE

    def help(self) -> str:
        return (
            "I can help you check your balance, transfer money, verify a cheque, "
            "or start KYC. What would you like to do?"
        )

    def unknown(self, clarification_question: str = "") -> str:
        return clarification_question or UNKNOWN_COMMAND_MESSAGE

    def transfer_intro(self, intent: StructuredIntent) -> str:
        if intent.assistant_reply:
            return intent.assistant_reply
        return "Of course. I can help you with a money transfer."

    def ask_for_beneficiary(self) -> str:
        return "Who would you like to send money to?"

    def ask_for_bank(self, beneficiary_name: str | None) -> str:
        if beneficiary_name:
            return f"Which bank is {beneficiary_name} using?"
        return "Which bank should I use for the transfer?"

    def ask_for_account_number(self, beneficiary_name: str | None) -> str:
        if beneficiary_name:
            return f"Please tell me {beneficiary_name}'s account number."
        return "Please share the beneficiary account number."

    def ask_for_amount(self, beneficiary_name: str | None) -> str:
        if beneficiary_name:
            return f"How much would you like to send to {beneficiary_name}?"
        return "How much would you like to transfer?"

    def transfer_confirmation(self, details: TransferDetails) -> str:
        return (
            f"Please confirm. Should I transfer AED {details.amount:,.2f} "
            f"to {details.beneficiary_name} at {details.bank_name}, "
            f"account number ending with {details.account_number[-4:]}? "
            "Please say yes to continue or no to cancel."
        )

    def transfer_success(self, receipt: TransferReceipt) -> str:
        return (
            f"Your transfer is complete. AED {receipt.amount:,.2f} has been sent to "
            f"{receipt.beneficiary_name}. Your reference number is {receipt.reference_number}."
        )

    def transfer_cancelled(self) -> str:
        return "No problem. I have cancelled the transfer."

    def transfer_failed(self) -> str:
        return "I could not collect the transfer details, so I am taking you back to the main menu."

    def cheque_prompt(self) -> str:
        return "Please upload or select a cheque image so I can verify it."

    def kyc_intro(self) -> str:
        return "Let's begin your KYC process. I will record audio first and then video."

    def ask_continue(self) -> str:
        return "Do you want anything else?"

    def goodbye(self) -> str:
        return "Thank you, goodbye."
