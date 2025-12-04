#!/usr/bin/env python3
"""
SMS-Prompt CLI Tool
A command-line interface for sending SMS messages using Twilio
"""

import os
import sys
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_twilio_client():
    """Initialize and return Twilio client"""
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    if not account_sid or not auth_token:
        print("Error: Twilio credentials not found!")
        print("Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in your .env file")
        sys.exit(1)
    
    return Client(account_sid, auth_token)

def send_sms(to_number, from_number, message):
    """Send SMS message using Twilio"""
    try:
        client = get_twilio_client()
        
        message_obj = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        
        print(f"\n✓ Message sent successfully!")
        print(f"  Message SID: {message_obj.sid}")
        print(f"  Status: {message_obj.status}")
        return True
        
    except Exception as e:
        print(f"\n✗ Error sending message: {str(e)}")
        return False

def main():
    """Main CLI function"""
    print("=" * 50)
    print("SMS-Prompt - Send SMS via Twilio")
    print("=" * 50)
    
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    if not from_number:
        print("Error: TWILIO_PHONE_NUMBER not set in .env file")
        sys.exit(1)
    
    print(f"\nFrom: {from_number}")
    
    # Get recipient number
    to_number = input("\nEnter recipient phone number (with country code, e.g., +1234567890): ").strip()
    
    if not to_number:
        print("Error: Phone number cannot be empty")
        sys.exit(1)
    
    # Get message content
    print("\nEnter your message (press Enter twice to send):")
    lines = []
    while True:
        line = input()
        if line == "" and len(lines) > 0:
            break
        lines.append(line)
    
    message = "\n".join(lines)
    
    if not message:
        print("Error: Message cannot be empty")
        sys.exit(1)
    
    # Send the message
    print(f"\nSending message to {to_number}...")
    send_sms(to_number, from_number, message)

if __name__ == "__main__":
    main()
