import os
import sys
from auth_db import (
    create_user,
    verify_user,
    save_prediction,
    get_prediction_history
)

def run_tests():
    print("=== Testing User Registration ===")
    test_user = "test_fraud_analyst"
    test_email = "analyst@example.com"
    test_pass = "SecurePass123!"

    # 1. Create User
    success, msg = create_user(test_user, test_email, test_pass)
    print(f"User registration result: success={success}, msg={msg}")
    assert success or "already exists" in msg, f"Failed: {msg}"

    # 2. Duplicate Check
    success_dup, msg_dup = create_user(test_user, "different@example.com", test_pass)
    print(f"Duplicate registration check: success={success_dup}, msg={msg_dup}")
    assert not success_dup, "Duplicate user was mistakenly allowed!"

    # 3. Verify Valid Password
    print("\n=== Testing User Login ===")
    valid_login, login_msg = verify_user(test_user, test_pass)
    print(f"Valid login result: {valid_login} ({login_msg})")
    assert valid_login, "Valid login failed!"

    # 4. Verify Invalid Password
    wrong_login, wrong_msg = verify_user(test_user, "WrongPassword!")
    print(f"Invalid login result: {wrong_login} ({wrong_msg})")
    assert not wrong_login, "Invalid login incorrectly passed!"

    # 5. Prediction save and retrieve
    print("\n=== Testing Prediction Logging & History ===")
    tx = {
        "type": "TRANSFER",
        "amount": 50000.0,
        "oldbalanceOrg": 50000.0,
        "newbalanceOrig": 0.0,
        "oldbalanceDest": 0.0,
        "newbalanceDest": 0.0
    }
    saved = save_prediction(test_user, tx, 1)
    print(f"Save prediction result: {saved}")
    assert saved, "Save prediction failed!"

    history = get_prediction_history(test_user)
    print(f"History retrieved: {len(history)} records found.")
    assert len(history) > 0, "No history records found!"
    print(f"Latest record: {history[0]}")

    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_tests()
