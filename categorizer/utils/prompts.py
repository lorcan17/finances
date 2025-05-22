"""
Prompt templates for transaction categorization.
"""

import json
import logging
from typing import List, Dict, Any

import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from anthropic import Anthropic

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
            "_Description": "paybyphone",
            "_Category": "Transportation",
            "_Subcategory": "Parking",
            "_Confidence": 7,
            "_Reasoning": "Paybyphone is a parking app"
        }
        
        # Create the prompt
        prompt = f"""
You are an expert transaction categorizer for a person who logs their personal expenses.
Please see the below categories and subcategories:

```json
{categories_json}
```

Please categorize this JSON of transaction descriptions and add fields for category, subcategory, confidence level (1-10 with 10 being highest), and reasoning for each transaction:

For each transaction, please analyze the merchant name and amount (if provided) to determine the most likely category and subcategory. Include your reasoning for each classification and a confidence level indicating how certain you are about the categorization.

Return the result as a JSON array. Do not include any extra text, comments, or explanations. Output ONLY valid JSON in string. Do not return in a code block like "```json"

Example of an item in the json array:
```json
{json.dumps(example_output)}
```

Important guidelines:
1. Always match to the closest existing category and subcategory - do not create new ones
2. Be specific in your reasoning, explaining why this merchant belongs to the chosen category
3. Only use the confidence level of 9-10 for obvious matches (e.g., "TRADER JOE'S" is clearly "Food: Groceries")
4. Use context clues from the merchant name to make educated guesses when necessary
5. If you're truly uncertain, use a confidence level of 3 or lower
6. Keep in mind the codes in the description .i.e [CK] is a cheque and mostly likely represents rent and [DN] is direct deposit
"""
        
        logger.debug("Categorization prompt built successfully")
        return prompt
        
    except Exception as e:
        logger.exception("Error building categorization prompt: %s", str(e))
        raise


class OpenAITransactionCategorizer:
    """
    A class to categorize financial transactions using OpenAI's LLM.
    """

    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo", temperature: float = 0):
        """
        Initialize the OpenAI TransactionCategorizer.

        Args:
            api_key: OpenAI API key
            model_name: Name of the OpenAI model to use
            temperature: Temperature parameter for LLM generation
        """
        logger.info("Initializing OpenAITransactionCategorizer with model: %s", model_name)
        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )

    def categorize_transactions(self, prompt,
                              transactions_data: dict) -> List[Dict[str, Any]]:
        """
        Categorize a list of transactions using OpenAI's LLM.

        Args:
            categories_df: DataFrame of available categories and subcategories
            transactions_df: DataFrame of transaction descriptions to categorize
            description_column: Name of the column containing transaction descriptions

        Returns:
            List of categorized transactions with additional metadata
        """
        if len(transactions_data) == 0:
            return None
        
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=json.dumps(transactions_data))
        ]
        
        try:
            # Get response from model
            logger.debug("Sending request to OpenAI LLM")
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


class AnthropicTransactionCategorizer:
    """
    A class to categorize financial transactions using Anthropic's Claude.
    """

    def __init__(self, api_key: str, model_name: str = "claude-3-haiku-20240307", temperature: float = 0):
        """
        Initialize the Anthropic TransactionCategorizer.

        Args:
            api_key: Anthropic API key
            model: Anthropic model to use (default: claude-3-7-sonnet-20250219)
            temperature: Temperature parameter for LLM generation
        """
        logger.info(f"Initializing AnthropicTransactionCategorizer with model: {model_name}")
        self.client = Anthropic(api_key=api_key)
        self.model = model_name
        self.temperature = temperature
    
    def categorize_transactions(self, prompt,
                              transactions_data: dict) -> List[Dict[str, Any]]:
        """
        Categorize a list of transactions using Anthropic's Claude.

        Args:
            categories_df: DataFrame of available categories and subcategories
            transactions_df: DataFrame of transaction descriptions to categorize
            description_column: Name of the column containing transaction descriptions

        Returns:
            List of categorized transactions with additional metadata
        """
        if len(transactions_data) == 0:
            return None
        
        try:
            # Get response from Anthropic API
            logger.debug("Sending request to Anthropic API")
            response = self.client.messages.create(
                model=self.model,
                system=prompt,
                messages=[
                    {"role": "user", "content": json.dumps(transactions_data)}
                ],
                max_tokens=4000,
                temperature=self.temperature
            )
            
            raw_output = response.content[0].text.strip()
            
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