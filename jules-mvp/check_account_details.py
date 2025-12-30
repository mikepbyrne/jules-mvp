#!/usr/bin/env python3
"""
Check detailed Twilio account status
"""
import os
from twilio.rest import Client
from dotenv import load_dotenv
import json

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

client = Client(ACCOUNT_SID, AUTH_TOKEN)


def check_full_account_status():
    """Get complete account details"""
    account = client.api.accounts(ACCOUNT_SID).fetch()

    return {
        "sid": account.sid,
        "friendly_name": account.friendly_name,
        "status": account.status,
        "type": account.type,
        "date_created": account.date_created.isoformat() if account.date_created else None,
        "date_updated": account.date_updated.isoformat() if account.date_updated else None
    }


def check_balance():
    """Check account balance"""
    try:
        balance = client.api.v2010.balance.fetch()
        return {
            "balance": balance.balance,
            "currency": balance.currency
        }
    except Exception as e:
        return {"error": str(e)}


def check_messaging_service():
    """Check if using a messaging service"""
    try:
        services = client.messaging.v1.services.list(limit=10)
        return [
            {
                "sid": svc.sid,
                "friendly_name": svc.friendly_name,
                "status": svc.status
            }
            for svc in services
        ]
    except Exception as e:
        return {"error": str(e)}


def get_specific_message_details(message_sid):
    """Get detailed info about a specific failed message"""
    try:
        message = client.messages(message_sid).fetch()
        return {
            "sid": message.sid,
            "status": message.status,
            "error_code": message.error_code,
            "error_message": message.error_message,
            "from": message.from_,
            "to": message.to,
            "body": message.body,
            "num_segments": message.num_segments,
            "price": message.price,
            "price_unit": message.price_unit,
            "date_sent": message.date_sent.isoformat() if message.date_sent else None,
            "date_created": message.date_created.isoformat() if message.date_created else None,
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    print("DETAILED ACCOUNT STATUS")
    print("=" * 70)

    print("\n1. Account Details:")
    print(json.dumps(check_full_account_status(), indent=2))

    print("\n2. Account Balance:")
    print(json.dumps(check_balance(), indent=2))

    print("\n3. Messaging Services:")
    print(json.dumps(check_messaging_service(), indent=2))

    # Get details on most recent failed message
    print("\n4. Most Recent Failed Message Details:")
    failed_sid = "SMd1b666369ea3924f258e2e81e1e1a9ca"
    print(json.dumps(get_specific_message_details(failed_sid), indent=2))

    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
