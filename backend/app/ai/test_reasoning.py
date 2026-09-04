from app.ai.reasoning import analyze_recovery_decision


payment = {
    "amount": 1499,
    "payment_method": "UPI",
    "failure_reason": "Insufficient Funds",
    "previous_attempts": 0,
    "failed_attempts": 0,
}

result = analyze_recovery_decision(
    payment=payment,
    probability=0.9983,
    recommended_action="SMART_RETRY",
)

print("\n========== RECOVERAI AI REASONING ==========")

for key, value in result.items():
    print(f"{key}: {value}")

