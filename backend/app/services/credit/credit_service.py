from sqlalchemy.orm import Session
from app.models.user import User
from app.models.credit_ledger import CreditLedger
import uuid

def has_sufficient_credits(db: Session, user_id: uuid.UUID, amount: int) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    return user.credits >= amount

def reserve_credits(db: Session, user_id: uuid.UUID, amount: int, feature: str, job_id: str) -> CreditLedger:
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.credits < amount:
        raise ValueError("Insufficient credits")

    ledger = CreditLedger(
        user_id=user.id,
        feature=feature,
        credits_before=user.credits,
        credits_deducted=amount,
        credits_after=user.credits - amount,
        job_id=job_id,
        status="Reserved"
    )

    # Deduct right away logically, but it's "reserved"
    user.credits -= amount

    db.add(ledger)
    db.commit()
    db.refresh(ledger)
    return ledger

def finalize_deduction(db: Session, ledger_id: uuid.UUID) -> None:
    ledger = db.query(CreditLedger).filter(CreditLedger.id == ledger_id).first()
    if ledger and ledger.status == "Reserved":
        ledger.status = "Completed"
        db.commit()

def refund_credits(db: Session, ledger_id: uuid.UUID) -> None:
    ledger = db.query(CreditLedger).filter(CreditLedger.id == ledger_id).first()
    if ledger and ledger.status == "Reserved":
        user = db.query(User).filter(User.id == ledger.user_id).first()
        if user:
            user.credits += ledger.credits_deducted
            ledger.status = "Refunded"
            ledger.credits_after = user.credits
            db.commit()

def refund_credits_by_job_id(db: Session, job_id: str) -> None:
    ledger = db.query(CreditLedger).filter(CreditLedger.job_id == job_id, CreditLedger.status == "Reserved").first()
    if ledger:
        user = db.query(User).filter(User.id == ledger.user_id).first()
        if user:
            user.credits += ledger.credits_deducted
            ledger.status = "Refunded"
            ledger.credits_after = user.credits
            db.commit()

def finalize_deduction_by_job_id(db: Session, job_id: str) -> None:
    ledger = db.query(CreditLedger).filter(CreditLedger.job_id == job_id, CreditLedger.status == "Reserved").first()
    if ledger:
        ledger.status = "Completed"
        db.commit()
