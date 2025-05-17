"""
Data preparation utilities for transaction categorization.
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)


def prepare_categorized_data_for_sheet(transactions_df: pd.DataFrame,
                                       description_column: str,
                                       categorized_transactions: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Prepare categorized transaction data for writing back to Google Sheets.
    
    Args:
        transactions_df: Original transactions DataFrame from Google Sheets
        description_column: Name of the column containing transaction descriptions
        categorized_transactions: List of categorized transactions from LLM
        
    Returns:
        DataFrame with original transactions and categorization results
    """
    logger.info("Preparing categorized data for sheet update")
    
    # Create a DataFrame from the categorized transactions
    categorized_df = pd.DataFrame(categorized_transactions)
    # Combine Category and Subcategory into a new column
    categorized_df["Predicted Category"] = categorized_df["_Category"].str.strip() + ": " + categorized_df["_Subcategory"].str.strip()
    categorized_df = categorized_df[["_Description", "Predicted Category", "_Confidence", "_Reasoning"]]
    
    # Merge with the original transactions DataFrame
    logger.debug(f"Original transactions columns: {transactions_df.columns.tolist()}")
    logger.debug(f"Categorized transactions columns: {categorized_df.columns.tolist()}")
    
    # Keep track of original row count
    original_row_count = transactions_df.shape[0]

    # Perform the merge
    result_df = pd.merge(
        transactions_df,
        categorized_df,
        left_on=description_column,
        right_on='_Description',
        how='left'
    ).drop(columns=['_Description'])

    # Check for row duplication
    if result_df.shape[0] > original_row_count:
        duplicated_rows = result_df.shape[0] - original_row_count
        error_message = (
            f"❌ Merge increased rows by {duplicated_rows}. "
            "This likely means that multiple rows in `categorized_df` match the same description. "
            "Ensure each description is unique or resolve one-to-many joins explicitly."
        )
        logger.error(error_message)
        raise ValueError(error_message)
    
    # Check if any transactions were not categorized
    uncategorized_count = result_df['Predicted Category'].isna().sum()
    if uncategorized_count > 0:
        logger.warning(f"{uncategorized_count} transactions could not be categorized")
    
    logger.debug("Prepared data for sheet update")
    return result_df