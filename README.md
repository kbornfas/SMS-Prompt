# SMS-Prompt

A simple command-line interface (CLI) tool for sending SMS messages using Twilio.

## Features

- 📱 Send SMS messages directly from your terminal
- 🔐 Secure credential management using environment variables
- ✅ Clear success/error feedback
- 🚀 Easy to set up and use

## Prerequisites

- Python 3.7 or higher
- A Twilio account with:
  - Account SID
  - Auth Token
  - A Twilio phone number

## Installation

1. Clone this repository:
```bash
git clone https://github.com/kbornfas/SMS-Prompt.git
cd SMS-Prompt
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
```bash
cp .env.example .env
```

4. Edit `.env` and add your Twilio credentials:
```
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here
```

## Usage

Run the CLI tool:
```bash
python cli/main.py
```

Or make it executable:
```bash
chmod +x cli/main.py
./cli/main.py
```

Follow the prompts to:
1. Enter the recipient's phone number (with country code, e.g., +1234567890)
2. Type your message (press Enter twice to send)

## Getting Twilio Credentials

1. Sign up for a free Twilio account at [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Go to your [Twilio Console](https://console.twilio.com/)
3. Find your Account SID and Auth Token
4. Get a phone number from the [Phone Numbers section](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming)

## Troubleshooting

### "Error: Twilio credentials not found!"
- Make sure you've created a `.env` file and added your Twilio credentials
- Check that the variable names match exactly: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`

### "Unable to create record: Permission to send an SMS has not been enabled"
- For trial accounts, you need to verify phone numbers before sending to them
- Verify phone numbers at: https://console.twilio.com/us1/develop/phone-numbers/manage/verified

### "The 'From' number ... is not a valid phone number"
- Make sure your `TWILIO_PHONE_NUMBER` includes the country code (e.g., +1234567890)
- Verify the number is active in your Twilio account

## License

MIT License
