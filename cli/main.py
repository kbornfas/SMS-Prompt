#!/usr/bin/env python3
"""
SMS-Prompt CLI Tool
A command-line interface for sending SMS messages using Twilio
"""

import os
import sys
import time
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
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

def send_sms(to_number, from_number, message, max_retries=3):
    """Send SMS message using Twilio with retry logic"""
    
    for attempt in range(max_retries):
        try:
            client = get_twilio_client()
            
            print(f"\n🔄 Attempt {attempt + 1} of {max_retries}...")
            print(f"📤 Sending to: {to_number}")
            print(f"📤 From: {from_number}")
            print(f"📝 Message: {message[:50]}{'...' if len(message) > 50 else ''}")
            
            message_obj = client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            print(f"\n✅ Message sent successfully!")
            print(f"  📧 Message SID: {message_obj.sid}")
            print(f"  📊 Status: {message_obj.status}")
            if message_obj.price:
                print(f"  💰 Price: {message_obj.price} {message_obj.price_unit}")
            else:
                print(f"  💰 Price: N/A (pricing info not available yet)")
            return True
            
        except TwilioRestException as e:
            print(f"\n❌ Twilio Error (Code {e.code}): {e.msg}")
            
            # Handle specific error cases
            if e.code == 21211:
                print("   ⚠️  Invalid phone number. Please check the format (e.g., +1234567890)")
                return False
            elif e.code == 21608:
                print("   ⚠️  The 'from' number is not verified or not a valid Twilio number")
                print("   💡 Check your TWILIO_PHONE_NUMBER in .env file")
                return False
            elif e.code == 21610:
                print("   ⚠️  Cannot send to this number (not verified for trial account)")
                print("   💡 Verify phone numbers at: https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
                return False
            elif e.code == 20003:
                print("   ⚠️  Authentication failed. Check your credentials.")
                print("   💡 Verify TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env file")
                return False
            
            # For other errors, retry
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"   ⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"\n❌ Failed after {max_retries} attempts")
                print(f"   💡 For more help, visit: https://www.twilio.com/docs/api/errors/{e.code}")
                return False
                
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"   ⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"\n❌ Failed after {max_retries} attempts")
                return False
    
    return False

def main():
    """Main CLI function"""
    print("=" * 60)
    print("📱 SMS-Prompt - Send SMS via Twilio")
    print("=" * 60)
    
    # Check for Twilio configuration
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    if not from_number:
        print("\n❌ Error: TWILIO_PHONE_NUMBER not set in .env file")
        print("\n💡 Setup instructions:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your Twilio credentials to .env")
        print("   3. Get credentials from: https://console.twilio.com/")
        sys.exit(1)
    
    print(f"\n📤 Sending from: {from_number}")
    print("\n" + "-" * 60)
    
    # Get recipient number
    to_number = input("\n📞 Enter recipient phone number (e.g., +1234567890): ").strip()
    
    if not to_number:
        print("❌ Error: Phone number cannot be empty")
        sys.exit(1)
    
    if not to_number.startswith('+'):
        print("⚠️  Warning: Phone number should include country code (e.g., +1 for US)")
        confirm = input("   Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            sys.exit(0)
    
    # Get message content
    print("\n📝 Enter your message (press Enter twice when done):")
    print("-" * 60)
    lines = []
    empty_line_count = 0
    
    while True:
        line = input()
        if line == "":
            empty_line_count += 1
            if empty_line_count >= 2:
                break
        else:
            empty_line_count = 0
            lines.append(line)
    
    message = "\n".join(lines).strip()
    
    if not message:
        print("❌ Error: Message cannot be empty")
        sys.exit(1)
    
    if len(message) > 1600:
        print(f"⚠️  Warning: Message is {len(message)} characters (standard SMS is 160 chars)")
        print("   This will be sent as multiple segments and may cost more.")
        confirm = input("   Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            sys.exit(0)
    
    # Send the message
    print("\n" + "=" * 60)
    print("🚀 Sending message...")
    print("=" * 60)
    
    success = send_sms(to_number, from_number, message)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Message delivered successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Failed to send message")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
