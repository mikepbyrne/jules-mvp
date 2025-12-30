#!/usr/bin/env python3
"""
Check if toll-free number is linked to approved trust product
"""
import os
from twilio.rest import Client
from dotenv import load_dotenv
import json

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(ACCOUNT_SID, AUTH_TOKEN)


def get_phone_number_compliance():
    """Get toll-free number's compliance/verification status"""
    try:
        # Get the phone number details
        numbers = client.incoming_phone_numbers.list(phone_number=TWILIO_PHONE)

        if not numbers:
            return {"error": "Phone number not found"}

        phone_number = numbers[0]

        # Try to get toll-free verification status
        try:
            # Check if there's a bundle associated
            bundle_sid = phone_number.bundle_sid

            return {
                "phone_number": phone_number.phone_number,
                "friendly_name": phone_number.friendly_name,
                "status": phone_number.status,
                "bundle_sid": bundle_sid,
                "has_bundle": bundle_sid is not None,
                "sms_capable": phone_number.capabilities.get('sms'),
                "emergency_status": phone_number.emergency_status,
                "emergency_address_sid": phone_number.emergency_address_sid
            }
        except Exception as e:
            return {
                "phone_number": phone_number.phone_number,
                "bundle_check_error": str(e),
                "has_bundle": False
            }

    except Exception as e:
        return {"error": str(e)}


def check_tollfree_verification_status():
    """Check toll-free verification submissions"""
    try:
        # Try to list toll-free verifications
        verifications = client.messaging.v1.tollfree_verifications.list(
            limit=20
        )

        return {
            "has_verifications": len(verifications) > 0,
            "verifications": [
                {
                    "sid": v.sid,
                    "status": v.status,
                    "phone_number": v.business_phone_number,
                    "created": v.date_created.isoformat() if v.date_created else None,
                    "updated": v.date_updated.isoformat() if v.date_updated else None
                }
                for v in verifications
            ]
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    print("PHONE NUMBER COMPLIANCE LINKAGE CHECK")
    print("=" * 70)

    print("\n1. Phone Number Compliance Details:")
    compliance = get_phone_number_compliance()
    print(json.dumps(compliance, indent=2))

    print("\n2. Toll-Free Verification Submissions:")
    verifications = check_tollfree_verification_status()
    print(json.dumps(verifications, indent=2))

    print("\n" + "=" * 70)
    print("ROOT CAUSE ANALYSIS")
    print("=" * 70)

    has_bundle = compliance.get("has_bundle", False)
    bundle_sid = compliance.get("bundle_sid")

    verif_list = verifications.get("verifications", [])
    has_verification = len(verif_list) > 0

    print(f"\nPhone Number: {TWILIO_PHONE}")
    print(f"Has Bundle Linked: {has_bundle}")
    if bundle_sid:
        print(f"Bundle SID: {bundle_sid}")

    print(f"\nHas Toll-Free Verifications: {has_verification}")

    if has_verification:
        print("\nVerification Status Details:")
        for v in verif_list:
            print(f"  - SID: {v['sid']}")
            print(f"    Status: {v['status']}")
            print(f"    Created: {v['created']}")
            print(f"    Updated: {v['updated']}")

    print("\n" + "=" * 70)
    print("DIAGNOSIS:")
    print("=" * 70)

    if not has_verification:
        print("\nPROBLEM FOUND: NO TOLL-FREE VERIFICATION SUBMITTED!")
        print("\nEven though you have a trust product, toll-free numbers require")
        print("a SEPARATE toll-free verification process.")
        print("\nFIX:")
        print("  1. Go to: https://console.twilio.com/us1/develop/sms/settings/toll-free-verifications")
        print("  2. Click 'Create new Toll-Free Verification'")
        print("  3. Fill out the form:")
        print("     - Phone Number: Select your toll-free number")
        print("     - Business Name: Jules AI")
        print("     - Business Website: Your website or GitHub")
        print("     - Use Case: Meal planning SMS assistant")
        print("     - Message Volume: Low (estimated daily volume)")
        print("     - Message Samples: Provide 2-3 example messages")
        print("     - Opt-in method: Web signup, user initiated")
        print("     - Opt-out method: STOP keyword")
        print("  4. Submit and wait for approval (1-3 business days)")
        print("\nALTERNATIVE IMMEDIATE FIX:")
        print("  - Purchase a local 10DLC number (works immediately for testing)")
        print("  - 10DLC numbers have higher initial limits")
        print("  - Then complete A2P 10DLC registration for production")

    else:
        print("\nToll-free verification found. Checking status...")
        pending_verifications = [v for v in verif_list if v['status'] != 'approved']

        if pending_verifications:
            print("\nPROBLEM: Verification is PENDING or INCOMPLETE")
            for v in pending_verifications:
                print(f"  - Verification {v['sid']}: {v['status']}")
            print("\nACTION: Wait for Twilio to approve your toll-free verification")
            print("This typically takes 1-3 business days")
            print("\nYou can check status at:")
            print("https://console.twilio.com/us1/develop/sms/settings/toll-free-verifications")
        else:
            print("\nVerifications appear approved. Error 30032 might be caused by:")
            print("  - Account billing issue")
            print("  - Daily rate limit exceeded")
            print("  - Recent account suspension (check console)")
            print("  - Verification not properly linked to phone number")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
