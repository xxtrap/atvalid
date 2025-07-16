# Microsoft Email Validator

A tool to validate Microsoft accounts (Office 365/Azure AD) by checking if emails exist.

## Features
- Checks both Microsoft Account (MSA) and Azure AD/Office365 accounts
- Randomized delays between requests to avoid detection
- Automatic browser restart every N requests or after time limit
- Headless Chrome browser operation
- Saves valid emails to separate file

## Requirements
- Python 3.7+
- Chrome/Chromium browser installed
- Required packages (install with `pip install -r requirements.txt`)

## Installation
1. Clone this repository or download the script
2. Install requirements:
   ```bash
   pip install -r requirements.txt
