#!/usr/bin/env python3
"""
Check toll-free number compliance and A2P registration status
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


def check_phone_number_type():
    """Check if number is toll-free, local, or mobile"""
    # Toll-free prefixes in US: 800, 888, 877, 866, 855, 844, 833
    toll_free_prefixes = ['800', '888', '877', '866', '855', '844', '833']

    # Extract area code from TWILIO_PHONE
    area_code = TWILIO_PHONE[2:5]  # Skip +1, get next 3 digits

    is_toll_free = area_code in toll_free_prefixes

    return {
        "phone_number": TWILIO_PHONE,
        "area_code": area_code,
        "is_toll_free": is_toll_free,
        "type": "toll-free" if is_toll_free else "local/mobile"
    }


def check_a2p_registration():
    """Check A2P 10DLC or toll-free registration status"""
    try:
        # Check for messaging service with A2P registration
        services = client.messaging.v1.services.list()

        if services:
            return {
                "has_messaging_service": True,
                "services": [
                    {
                        "sid": svc.sid,
                        "name": svc.friendly_name,
                        "status": svc.status
                    }
                    for svc in services
                ]
            }
        else:
            return {
                "has_messaging_service": False,
                "note": "No messaging service configured"
            }
    except Exception as e:
        return {"error": str(e)}


def check_regulatory_compliance():
    """Check regulatory bundles (for A2P compliance)"""
    try:
        # Try to get regulatory bundles
        bundles = client.numbers.v2.regulatory_compliance.bundles.list(limit=10)

        return {
            "has_bundles": len(bundles) > 0,
            "bundles": [
                {
                    "sid": bundle.sid,
                    "friendly_name": bundle.friendly_name,
                    "status": bundle.status
                }
                for bundle in bundles
            ]
        }
    except Exception as e:
        return {"error": str(e), "has_bundles": False}


def check_trust_products():
    """Check trust products (for toll-free verification)"""
    try:
        trust_products = client.trusthub.v1.trust_products.list(limit=10)

        return {
            "has_trust_products": len(trust_products) > 0,
            "products": [
                {
                    "sid": tp.sid,
                    "friendly_name": tp.friendly_name,
                    "status": tp.status
                }
                for tp in trust_products
            ]
        }
    except Exception as e:
        return {"error": str(e), "has_trust_products": False}


def main():
    print("TOLL-FREE & A2P COMPLIANCE CHECK")
    print("=" * 70)

    # Check number type
    print("\n1. Phone Number Type:")
    number_info = check_phone_number_type()
    print(json.dumps(number_info, indent=2))

    is_toll_free = number_info.get("is_toll_free", False)

    # Check A2P registration
    print("\n2. A2P/Messaging Service Registration:")
    a2p_status = check_a2p_registration()
    print(json.dumps(a2p_status, indent=2))

    # Check regulatory compliance
    print("\n3. Regulatory Bundles:")
    bundles = check_regulatory_compliance()
    print(json.dumps(bundles, indent=2))

    # Check trust products (for toll-free)
    print("\n4. Trust Products (Toll-Free Verification):")
    trust_products = check_trust_products()
    print(json.dumps(trust_products, indent=2))

    # Analysis
    print("\n" + "=" * 70)
    print("ANALYSIS & RECOMMENDATIONS")
    print("=" * 70)

    if is_toll_free:
        print("\nYour number is TOLL-FREE (866).")
        print("\nToll-free numbers require VERIFICATION before they can send SMS.")
        print("This is likely why you're getting error 30032 (account suspended).")
        print("\nError 30032 for toll-free numbers typically means:")
        print("  - Toll-free verification is NOT complete")
        print("  - Your toll-free number is not yet approved for SMS")
        print("  - Messaging is suspended until verification completes")

        has_trust = trust_products.get("has_trust_products", False)

        if not has_trust:
            print("\nNO TRUST PRODUCTS FOUND - Toll-free verification is REQUIRED!")
            print("\nREQUIRED ACTIONS:")
            print("  1. Go to Twilio Console > Phone Numbers > Manage > Regulatory Compliance")
            print("  2. Complete toll-free verification form:")
            print("     - Business/organization name: Jules AI")
            print("     - Business type: Technology/Software")
            print("     - Use case: Meal planning assistant via SMS")
            print("     - Sample messages: 'Hi! I'm Jules...' (friendly opt-in messages)")
            print("     - Opt-in method: Web signup, SMS keyword")
            print("     - Opt-out method: STOP keyword")
            print("     - Customer care contact: Your email/phone")
            print("\n  3. Wait for approval (can take 1-3 business days)")
            print("\n  4. Alternative QUICK FIX (works immediately):")
            print("     - Buy a local 10DLC number instead of toll-free")
            print("     - Local numbers have higher daily limits and work immediately")
            print("     - Then register for A2P 10DLC (required for volume)")
        else:
            print("\nTrust products found - checking status...")
            for tp in trust_products.get("products", []):
                status = tp.get("status")
                print(f"  - {tp.get('friendly_name')}: {status}")
                if status not in ["twilio-approved", "compliant"]:
                    print(f"    WARNING: Status is '{status}' - may need approval")

    else:
        print("\nYour number is LOCAL/10DLC.")
        print("\nFor production use, you need A2P 10DLC registration.")
        print("However, you should still be able to send limited messages.")
        print("\nError 30032 for local numbers might indicate:")
        print("  - Daily sending limits exceeded")
        print("  - Account needs verification")
        print("  - Check Twilio Console for account status")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
