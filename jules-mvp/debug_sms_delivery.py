#!/usr/bin/env python3
"""
SMS Delivery Debugger - Diagnose Twilio delivery issues
"""
import os
from twilio.rest import Client
from dotenv import load_dotenv
import json

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")
YOUR_PHONE = os.getenv("YOUR_PHONE")

client = Client(ACCOUNT_SID, AUTH_TOKEN)


def check_account_type():
    """Check if account is trial or paid"""
    account = client.api.accounts(ACCOUNT_SID).fetch()
    return {
        "status": account.status,
        "type": account.type,
        "friendly_name": account.friendly_name
    }


def check_verified_numbers():
    """Get list of verified phone numbers (trial accounts only)"""
    try:
        # Outgoing caller IDs are the verified numbers in trial accounts
        verified = client.outgoing_caller_ids.list()
        return [
            {
                "phone_number": caller_id.phone_number,
                "friendly_name": caller_id.friendly_name
            }
            for caller_id in verified
        ]
    except Exception as e:
        return {"error": str(e)}


def analyze_delivery_failures():
    """Analyze recent delivery failures"""
    messages = client.messages.list(limit=20)

    failures = []
    for msg in messages:
        if msg.status in ['undelivered', 'failed']:
            failures.append({
                'sid': msg.sid,
                'to': msg.to,
                'from': msg.from_,
                'status': msg.status,
                'error_code': msg.error_code,
                'error_message': msg.error_message,
                'date': msg.date_sent.isoformat() if msg.date_sent else None,
                'body_preview': msg.body[:50] + '...' if len(msg.body) > 50 else msg.body
            })

    return failures


def get_error_30032_details():
    """Get details about error 30032"""
    return {
        "error_code": 30032,
        "name": "Account Suspended",
        "description": "Your Twilio account is suspended. Common causes include:",
        "causes": [
            "Trial account sending to unverified phone numbers",
            "Account has outstanding balance or billing issues",
            "Account flagged for suspicious activity",
            "Regulatory compliance issues"
        ],
        "solution_trial": [
            "Verify the destination phone number at https://console.twilio.com/us1/develop/phone-numbers/manage/verified",
            "Upgrade to a paid account to send to any number",
            "Check account status at https://console.twilio.com/"
        ]
    }


def main():
    print("=" * 70)
    print("TWILIO SMS DELIVERY DIAGNOSTIC REPORT")
    print("=" * 70)
    print()

    # Account type
    print("1. ACCOUNT STATUS")
    print("-" * 70)
    account_info = check_account_type()
    print(json.dumps(account_info, indent=2))
    print()

    # Verified numbers
    print("2. VERIFIED PHONE NUMBERS (Trial Account Only)")
    print("-" * 70)
    verified = check_verified_numbers()
    print(json.dumps(verified, indent=2))
    print()

    # Recent failures
    print("3. RECENT DELIVERY FAILURES")
    print("-" * 70)
    failures = analyze_delivery_failures()
    print(json.dumps(failures, indent=2))
    print()

    # Error 30032 explanation
    print("4. ERROR 30032 DETAILS")
    print("-" * 70)
    error_info = get_error_30032_details()
    print(json.dumps(error_info, indent=2))
    print()

    # Analysis
    print("5. ROOT CAUSE ANALYSIS")
    print("-" * 70)

    is_trial = account_info.get("type") == "Trial"
    has_failures = len(failures) > 0
    target_phone = YOUR_PHONE

    verified_numbers = [v['phone_number'] for v in verified] if isinstance(verified, list) else []
    is_verified = target_phone in verified_numbers

    print(f"Account Type: {'TRIAL' if is_trial else 'PAID'}")
    print(f"Target Phone: {target_phone}")
    print(f"Is Verified: {'YES' if is_verified else 'NO'}")
    print(f"Error 30032 Present: {'YES' if has_failures else 'NO'}")
    print()

    if is_trial and not is_verified:
        print("ROOT CAUSE IDENTIFIED:")
        print("  Your Twilio account is a TRIAL account and the destination phone")
        print(f"  number ({target_phone}) is NOT VERIFIED.")
        print()
        print("SOLUTION:")
        print("  Option 1 (Quick Fix - Free):")
        print("    1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
        print(f"    2. Click 'Add a new caller ID' and verify {target_phone}")
        print("    3. Enter the verification code sent to your phone")
        print()
        print("  Option 2 (Permanent Fix - Requires Upgrade):")
        print("    1. Go to: https://console.twilio.com/billing")
        print("    2. Upgrade to a paid account ($20 minimum)")
        print("    3. Send SMS to any number without verification")
        print()
    elif is_trial and is_verified:
        print("Phone number IS verified but still failing. Check:")
        print("  - Account balance/billing status")
        print("  - Account suspension status")
        print("  - Visit: https://console.twilio.com/")
    else:
        print("Paid account detected. Check:")
        print("  - Account balance")
        print("  - Billing status")
        print("  - Account compliance status")

    print()
    print("=" * 70)


if __name__ == '__main__':
    main()
