"""
Prompt templates for transaction categorization.
"""

import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def build_categorization_prompt(categories_data: List[Dict[str, Any]]) -> str:
    """
    Build the prompt for transaction categorization.
    
    Args:
        categories_data: List of categories and subcategories
        
    Returns:
        Formatted prompt string for the LLM
    """
    try:
        logger.debug("Building categorization prompt with %d categories", len(categories_data))
        
        # Convert categories data to JSON
        categories_json = json.dumps(categories_data, indent=2)
        example_output = {
        "Description": "paybyphone",
        "Category": "Transportation",
        "Subcategory": "Parking",
        "Confidence": "High",
        "Reasoning": "Paybyphone is a parking app"
    }
        # Create the prompt
        prompt = f"""
You are an expert transaction categorizer for a person who logs their personal expenses.
Please see the below csv for categories and subcategories:

```json
{categories_json}
```

Please categorize this JSON of transaction descriptions and add fields for category, subcategory, confidence level (High/Medium/Low), and reasoning for each transaction:

For each transaction, please analyze the merchant name and amount to determine the most likely category and subcategory. Include your reasoning for each classification and a confidence level indicating how certain you are about the categorization.

Return the result as a JSON array. Do not include any extra text, comments, or explanations. Output ONLY valid JSON in string. Do not return in a code block like "```json"

Example of an item in the json array
```json
{json.dumps(example_output)}
```

"""
        
        logger.debug("Categorization prompt built successfully")
        return prompt
        
    except Exception as e:
        logger.exception("Error building categorization prompt: %s", str(e))
        raise