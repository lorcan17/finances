"""
Configuration settings for the transaction categorization application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"

# Google Sheets settings
ENCRYPT_KEY = os.environ['ENCRYPT_KEY']
SPREADSHEET_ID = os.getenv("GSHEET_SHEET_ID")
GOOGLE_CREDENTIALS_PATH =  "config/encrypt_google_cloud_credentials.json"

# Sheet names and ranges
CATEGORIES_SHEET_NAME = 'Categories'
CATEGORIES_RANGE = 'A:B'
CONFIG_SHEET_NAME = 'CONFIG'
CONFIG_RANGE = 'A:E'


# Simple logging configuration
LOG_LEVEL = 'DEBUG'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = BASE_DIR / 'logs' / 'transaction_categorizer.log'

# OpenAI API settings
OPENAI_MODEL = 'gpt-4o'
OPENAI_TEMPERATURE = 0

# Anthropic Settings
