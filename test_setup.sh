#!/bin/bash
# Test script to verify the CLI tool setup

echo "Testing SMS-Prompt CLI Tool"
echo "=============================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
echo "✅ Python 3 is installed"

# Check if required packages are installed
python3 -c "import twilio; import dotenv" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Required packages are installed"
else
    echo "❌ Required packages are not installed"
    echo "   Run: pip install -r requirements.txt"
    exit 1
fi

# Check if .env file exists
if [ -f .env ]; then
    echo "✅ .env file exists"
else
    echo "⚠️  .env file not found"
    echo "   Run: cp .env.example .env"
    echo "   Then edit .env with your Twilio credentials"
fi

# Check if cli/main.py exists
if [ -f cli/main.py ]; then
    echo "✅ cli/main.py exists"
else
    echo "❌ cli/main.py not found"
    exit 1
fi

# Test syntax
python3 -m py_compile cli/main.py
if [ $? -eq 0 ]; then
    echo "✅ Python syntax is valid"
else
    echo "❌ Python syntax errors found"
    exit 1
fi

echo ""
echo "=============================="
echo "✅ All checks passed!"
echo ""
echo "To run the CLI tool:"
echo "  python3 cli/main.py"
echo ""
echo "Or make it executable:"
echo "  chmod +x cli/main.py"
echo "  ./cli/main.py"
