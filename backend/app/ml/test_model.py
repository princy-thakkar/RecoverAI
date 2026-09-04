from app.ml.predict import predict_recovery_probability


payments = [
    {
        "amount": 500,
        "payment_method": "UPI",
        "previous_attempts": 0,
        "failed_attempts": 0,
    },
    {
        "amount": 2500,
        "payment_method": "UPI",
        "previous_attempts": 1,
        "failed_attempts": 0,
    },
    {
        "amount": 5000,
        "payment_method": "CARD",
        "previous_attempts": 5,
        "failed_attempts": 5,
    },
]


for payment in payments:
    probability = predict_recovery_probability(payment)

    print("\nPayment:")
    print(payment)

    print(
        f"Recovery probability: {probability:.2%}"
    )