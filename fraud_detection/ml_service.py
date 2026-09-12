"""ML service entry point."""

from .ml_inference import predict_transaction

def get_ml_score(transaction):
    if not isinstance(transaction, dict):
        raise TypeError(
            "Transaction must be a dictionary."
        )

    return predict_transaction(
        transaction
    )
