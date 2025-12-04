# SMS-Prompt

A simple command-line interface (CLI) tool for sending SMS messages using Twilio.

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/kbornfas/SMS-Prompt.git
cd SMS-Prompt
pip install -r requirements.txt

# 2. Configure Twilio
cp .env.example .env
# Edit .env with your Twilio credentials from https://console.twilio.com/

# 3. Run
python cli/main.py
```

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

### Common Issues and Solutions

#### "Error: Twilio credentials not found!"
- Make sure you've created a `.env` file and added your Twilio credentials
- Check that the variable names match exactly: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`

#### "Unable to create record: Permission to send an SMS has not been enabled" (Error 21610)
- **For trial accounts**: You need to verify phone numbers before sending to them
- Verify phone numbers at: https://console.twilio.com/us1/develop/phone-numbers/manage/verified
- **Solution**: Add the recipient's phone number to your verified list, or upgrade to a paid account

#### "The 'From' number ... is not a valid phone number" (Error 21608)
- Make sure your `TWILIO_PHONE_NUMBER` includes the country code (e.g., +1234567890)
- Verify the number is active and matches exactly what's shown in your Twilio account
- Check that you've selected a phone number in your Twilio console

#### "Authentication failed" (Error 20003)
- Double-check your `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` in the .env file
- Make sure there are no extra spaces or quotes around the values
- Verify credentials at: https://console.twilio.com/

#### Message not sending / Keeps retrying
- The tool will automatically retry up to 3 times with increasing delays
- Check the specific error code and message for guidance
- Visit Twilio's error documentation: https://www.twilio.com/docs/api/errors
- Ensure you have sufficient balance in your Twilio account

### Features

- ✅ **Automatic retry logic**: Failed sends are retried up to 3 times with exponential backoff
- ✅ **Detailed error messages**: Specific error codes with helpful troubleshooting tips
- ✅ **Input validation**: Warns about missing country codes and long messages
- ✅ **Progress feedback**: Shows attempt number, recipient, and message preview
- ✅ **Cost tracking**: Displays message price after successful delivery

## License

MIT License
