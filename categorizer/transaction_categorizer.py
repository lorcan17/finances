#!/usr/bin/env python3
"""
Transaction Categorizer

This module automates the categorization of financial transactions using LLM.
It loads transaction data from Google Sheets and categorizes each transaction
using either OpenAI's GPT or Anthropic's Claude model.
"""

import os
import logging
from pathlib import Path
from typing import Literal

import pandas as pd
from dotenv import load_dotenv

from config import settings
from utils.google_utils import GoogleSheetsClient
from utils.prompts import OpenAITransactionCategorizer, AnthropicTransactionCategorizer, build_categorization_prompt
from utils.data_prep import prepare_categorized_data_for_sheet

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers if they don't exist already
if not logger.handlers:
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "transaction_categorizer.log",
        maxBytes=1024*1024*5,  # 5MB
        backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def main(llm_provider: Literal["openai", "anthropic"] = "openai"):
    """
    Main execution function.
    
    Args:
        llm_provider: Which LLM provider to use ('openai' or 'anthropic')
    """
    # Load environment variables
    load_dotenv()
    logger.info(f"Starting transaction categorization process using {llm_provider}")
    
    try:
        # Initialize Google Sheets client
        logger.debug("Initializing Google Sheets client")
        google_client = GoogleSheetsClient(
            credentials_path=settings.GOOGLE_CREDENTIALS_PATH
        )
        
        # Load categories
        logger.info("Loading categories from Google Sheets")
        categories_df = google_client.export_sheet_range(
            spreadsheet_id=settings.SPREADSHEET_ID,
            range_name=f"{settings.CATEGORIES_SHEET_NAME}!{settings.CATEGORIES_RANGE}"
        )
        
        logger.debug("Loaded %d categories", len(categories_df))
        
        # Load config
        logger.info('Loading config information')
        config_df = google_client.export_sheet_range(
            spreadsheet_id=settings.SPREADSHEET_ID,
            range_name=f"{settings.CONFIG_SHEET_NAME}!{settings.CONFIG_RANGE}"
        )
        logger.debug("Loaded %d config items", len(config_df))

        # Initialize the appropriate categorizer
        if llm_provider == "openai":
            categorizer = OpenAITransactionCategorizer(
                api_key=os.getenv("OPENAI_API_KEY")
            )
        else:  # anthropic
            categorizer = AnthropicTransactionCategorizer(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )

        config_json = config_df.to_dict(orient='records')
        for i, item in enumerate(config_json):
            sheet = item.get('Sheet')
            sheet_range = f"'{sheet}'!{item.get('Range')}"
            description_column = item.get("Description Column")

            # Load transactions
            logger.info(f"Loading transactions from sheet in row {i}")
            transactions_df = google_client.export_sheet_range(
                spreadsheet_id=settings.SPREADSHEET_ID,
                range_name=sheet_range
            )
            logger.debug("Loaded %d transactions", len(transactions_df))

            system_prompt = build_categorization_prompt(categories_df.to_dict(orient='records'))

            transactions_data = (
                transactions_df[[description_column]]
                .drop_duplicates()
                .rename(columns={description_column: '_Description'})
                .to_dict(orient='records'))

            # Categorize transactions
            categorized_transactions = categorizer.categorize_transactions(system_prompt,
                transactions_data
            )

            # Output results
            if categorized_transactions:
                # Prepare data for updating Google Sheets
                updated_df = prepare_categorized_data_for_sheet(
                    transactions_df, 
                    description_column,
                    categorized_transactions
                )

                # Define the output range - assuming we're updating the same sheet
                # but potentially adding new columns
                output_range = f"{sheet}!A1"

                # Update Google Sheets with the categorized data
                logger.info("Updating Google Sheets with categorized data")
                google_client.update_sheet_range(
                    spreadsheet_id=settings.SPREADSHEET_ID,
                    range_name=output_range,
                    df=updated_df
                )

                logger.info(f"Successfully updated Google Sheet row {i} with categorized transactions")
                print(f"Successfully categorized and saved {len(categorized_transactions)} transactions from Google Sheet row {i}")
            else:
                logger.warning("No transactions were categorized")
            
    except Exception as e:
        logger.exception("Error in transaction categorization pipeline: %s", str(e))
        

if __name__ == "__main__":
    # By default, use "openai", but can be changed to "anthropic" or 
    # Can be modified to accept command line arguments if desired
    main(llm_provider="openai")