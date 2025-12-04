# SMS-Prompt Quick Reference

## Setup (One-time)
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Twilio credentials
```

## Run
```bash
python cli/main.py
```

## Common Errors and Solutions

| Error Code | Problem | Solution |
|------------|---------|----------|
| 21610 | Unverified recipient (trial account) | Verify phone at: https://console.twilio.com/us1/develop/phone-numbers/manage/verified |
| 21608 | Invalid 'from' number | Check TWILIO_PHONE_NUMBER in .env matches your Twilio number |
| 20003 | Authentication failed | Verify TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env |
| 21211 | Invalid phone format | Use international format: +1234567890 |

## Tips

✅ **Always include country code** (e.g., +1 for US)  
✅ **Press Enter twice** to finish message  
✅ **Tool auto-retries** up to 3 times with delays  
✅ **Check message length** - Over 160 chars costs more  
✅ **Trial accounts** require verified recipients  

## Get Help

- Twilio Console: https://console.twilio.com/
- Twilio Errors: https://www.twilio.com/docs/api/errors
- Verify Numbers: https://console.twilio.com/us1/develop/phone-numbers/manage/verified
