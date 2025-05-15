#!/usr/bin/env python3
"""
Transaction Categorizer

This module automates the categorization of financial transactions using LLM.
It loads transaction data from Google Sheets and categorizes each transaction
using OpenAI's GPT model.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from config import settings
from utils.google_utils import GoogleSheetsClient
from utils.prompts import build_categorization_prompt

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
        logs_dir / "prompts.log",
        maxBytes=1024*1024*5,  # 5MB
        backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


class TransactionCategorizer:
    """
    A class to categorize financial transactions using LLM.
    """

    def __init__(self, api_key: str, model_name: str = "gpt-4o", temperature: float = 0):
        """
        Initialize the TransactionCategorizer.

        Args:
            api_key: OpenAI API key
            model_name: Name of the OpenAI model to use
            temperature: Temperature parameter for LLM generation
        """
        logger.info("Initializing TransactionCategorizer with model: %s", model_name)
        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )

    def categorize_transactions(self, 
                               categories_data: List[Dict[str, Any]], 
                               transactions_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Categorize a list of transactions using LLM.

        Args:
            categories_data: List of available categories and subcategories
            transactions_data: List of transaction descriptions to categorize

        Returns:
            List of categorized transactions with additional metadata
        """
        logger.info("Categorizing %d transactions", len(transactions_data))
        logger.debug(("Transaction_data: %s", transactions_data[:200]))
        
        # Build prompt
        prompt = build_categorization_prompt(categories_data)
        logger.debug("Prompt: %s", prompt)
                
        
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=json.dumps(transactions_data))
        ]
        
        try:
            # Get response from model
            logger.debug("Sending request to LLM")
            response = self.llm.invoke(messages)
            raw_output = response.content.strip()
            
            try:
                # Parse JSON response
                categorized_transactions = json.loads(raw_output)
                logger.info("Successfully categorized transactions")
                return categorized_transactions
            except json.JSONDecodeError as e:
                logger.error("Failed to parse JSON response: %s", e)
                logger.debug("Raw output: %s", raw_output)
                return []
                
        except Exception as e:
            logger.exception("Error during transaction categorization: %s", str(e))
            return []

def prepare_categorized_data_for_sheet(transactions_df: pd.DataFrame, 
                                      categorized_transactions: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Prepare categorized transaction data for writing back to Google Sheets.
    
    Args:
        transactions_df: Original transactions DataFrame from Google Sheets
        categorized_transactions: List of categorized transactions from LLM
        
    Returns:
        DataFrame with original transactions and categorization results
    """
    logger.info("Preparing categorized data for sheet update")
    
    # Create a DataFrame from the categorized transactions
    categorized_df = pd.DataFrame(categorized_transactions)
    
    # Ensure columns are properly formatted (case-insensitive matching)
    if 'description' in categorized_df.columns:
        categorized_df.rename(columns={'description': 'Description'}, inplace=True)
    
    # Merge with the original transactions DataFrame
    logger.debug(f"Original transactions columns: {transactions_df.columns.tolist()}")
    logger.debug(f"Categorized transactions columns: {categorized_df.columns.tolist()}")
    
    # Perform a left join to keep all original transactions
    result_df = pd.merge(
        transactions_df,
        categorized_df,
        on='Description',
        how='left'
    )
    
    logger.info(f"Merged data shape: {result_df.shape}")
    logger.debug(f"Resulting columns: {result_df.columns.tolist()}")
    
    # Check if any transactions were not categorized
    uncategorized_count = result_df['Category'].isna().sum()
    if uncategorized_count > 0:
        logger.warning(f"{uncategorized_count} transactions could not be categorized")
    
    logger.debug("Prepared data for sheet update")
    return result_df


def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv()
    logger.info("Starting transaction categorization process")
    
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
        categories_data = categories_df.to_dict(orient='records')
        logger.debug("Loaded %d categories", len(categories_data))
        
        # Load transactions
        logger.info("Loading transactions from Google Sheets")
        transactions_df = google_client.export_sheet_range(
            spreadsheet_id=settings.SPREADSHEET_ID,
            range_name=f"{settings.TRANSACTIONS_SHEET_NAME}!{settings.TRANSACTIONS_RANGE}"
        )
        transactions_data = transactions_df.to_dict(orient='records')
        logger.debug("Loaded %d transactions", len(transactions_data))
        
        # Initialize categorizer
        categorizer = TransactionCategorizer(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Categorize transactions
        categorized_transactions = categorizer.categorize_transactions(
            categories_data, 
            transactions_data
        )
        
        # Output results
        if categorized_transactions:
            # Prepare data for updating Google Sheets
            updated_df = prepare_categorized_data_for_sheet(
                transactions_df, 
                categorized_transactions
            )
            
            # Define the output range - assuming we're updating the same sheet
            # but potentially adding new columns
            output_range = f"{settings.TRANSACTIONS_SHEET_NAME}!{settings.TRANSACTION_IMPORT_RANGE}"
            
            # Update Google Sheets with the categorized data
            logger.info("Updating Google Sheets with categorized data")
            google_client.update_sheet_range(
                spreadsheet_id=settings.SPREADSHEET_ID,
                range_name=output_range,
                df=updated_df
            )
            
            logger.info("Successfully updated Google Sheets with categorized transactions")
            print(f"Successfully categorized and saved {len(categorized_transactions)} transactions")
        else:
            logger.warning("No transactions were categorized")
            
    except Exception as e:
        logger.exception("Error in transaction categorization pipeline: %s", str(e))
        

if __name__ == "__main__":
    main()
