#!/usr/bin/env python3
"""
Twilio Helper - Access Twilio account for monitoring and troubleshooting
"""
import os
from twilio.rest import Client
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

# Load credentials
load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(ACCOUNT_SID, AUTH_TOKEN)


def get_recent_messages(limit=10):
    """Get recent SMS messages"""
    messages = client.messages.list(limit=limit)

    results = []
    for msg in messages:
        results.append({
            'sid': msg.sid,
            'from': msg.from_,
            'to': msg.to,
            'body': msg.body[:100] + '...' if len(msg.body) > 100 else msg.body,
            'status': msg.status,
            'direction': msg.direction,
            'date': msg.date_sent.isoformat() if msg.date_sent else None,
            'error_code': msg.error_code,
            'error_message': msg.error_message
        })

    return results


def get_account_balance():
    """Get account balance"""
    balance = client.api.v2010.balance.fetch()
    return {
        'balance': balance.balance,
        'currency': balance.currency
    }


def get_phone_number_info(phone_number=None):
    """Get phone number configuration"""
    if not phone_number:
        phone_number = TWILIO_PHONE

    # Get all phone numbers
    numbers = client.incoming_phone_numbers.list()

    for number in numbers:
        if number.phone_number == phone_number:
            return {
                'phone_number': number.phone_number,
                'friendly_name': number.friendly_name,
                'sms_url': number.sms_url,
                'sms_method': number.sms_method,
                'status_callback': number.status_callback,
                'capabilities': {
                    'sms': number.capabilities.get('sms'),
                    'mms': number.capabilities.get('mms'),
                    'voice': number.capabilities.get('voice')
                }
            }

    return None


def check_webhook_logs(hours=1):
    """Check recent webhook events"""
    # Get messages from last N hours
    date_sent_after = datetime.utcnow() - timedelta(hours=hours)

    messages = client.messages.list(
        date_sent_after=date_sent_after,
        limit=20
    )

    webhook_events = []
    for msg in messages:
        # Get feedback for this message (if available)
        webhook_events.append({
            'sid': msg.sid,
            'from': msg.from_,
            'to': msg.to,
            'direction': msg.direction,
            'status': msg.status,
            'body': msg.body[:50] + '...' if len(msg.body) > 50 else msg.body,
            'error': msg.error_message if msg.error_code else None,
            'time': msg.date_sent.isoformat() if msg.date_sent else None
        })

    return webhook_events


def send_test_message(to_number, body="Test message from Jules helper"):
    """Send a test SMS"""
    try:
        message = client.messages.create(
            body=body,
            from_=TWILIO_PHONE,
            to=to_number
        )
        return {
            'success': True,
            'sid': message.sid,
            'status': message.status,
            'message': f"Message sent with SID: {message.sid}"
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def verify_webhook_config():
    """Verify webhook is configured correctly"""
    phone_info = get_phone_number_info()

    if not phone_info:
        return {
            'configured': False,
            'error': 'Phone number not found'
        }

    sms_url = phone_info.get('sms_url')
    sms_method = phone_info.get('sms_method')

    issues = []
    if not sms_url:
        issues.append('No SMS webhook URL configured')
    elif not sms_url.endswith('/sms/webhook'):
        issues.append(f'Webhook URL may be incorrect: {sms_url}')

    if sms_method != 'POST':
        issues.append(f'HTTP method should be POST, is: {sms_method}')

    return {
        'configured': len(issues) == 0,
        'webhook_url': sms_url,
        'method': sms_method,
        'issues': issues
    }


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python twilio_helper.py [command]")
        print("\nCommands:")
        print("  messages       - Show recent messages")
        print("  balance        - Show account balance")
        print("  phone          - Show phone number config")
        print("  webhook        - Verify webhook configuration")
        print("  logs [hours]   - Show webhook logs (default: 1 hour)")
        print("  test [phone]   - Send test message")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'messages':
        messages = get_recent_messages(limit=20)
        print(json.dumps(messages, indent=2))

    elif command == 'balance':
        balance = get_account_balance()
        print(json.dumps(balance, indent=2))

    elif command == 'phone':
        info = get_phone_number_info()
        print(json.dumps(info, indent=2))

    elif command == 'webhook':
        result = verify_webhook_config()
        print(json.dumps(result, indent=2))

    elif command == 'logs':
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        logs = check_webhook_logs(hours=hours)
        print(json.dumps(logs, indent=2))

    elif command == 'test':
        if len(sys.argv) < 3:
            print("Usage: python twilio_helper.py test [phone_number]")
            sys.exit(1)
        result = send_test_message(sys.argv[2])
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
