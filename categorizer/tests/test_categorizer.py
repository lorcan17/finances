"""
Tests for the transaction categorization module.
"""

import json
import os
import unittest
from unittest.mock import patch, MagicMock

import pandas as pd

from categorizer.transaction_categorizer import TransactionCategorizer


class TestTransactionCategorizer(unittest.TestCase):
    """Test cases for TransactionCategorizer."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock API key
        self.api_key = "test_api_key"
        
        # Sample test data
        self.categories_data = [
            {"category": "Food", "subcategory": "Groceries"},
            {"category": "Food", "subcategory": "Restaurants"},
            {"category": "Transportation", "subcategory": "Gas"},
            {"category": "Utilities", "subcategory": "Electricity"}
        ]
        
        self.transactions_data = [
            {"description": "WALMART", "amount": "45.67"},
            {"description": "SHELL GAS", "amount": "35.00"},
            {"description": "UBER EATS", "amount": "25.99"}
        ]
        
        self.expected_result = [
            {
                "description": "WALMART",
                "amount": "45.67",
                "category": "Food",
                "subcategory": "Groceries",
                "confidence": "High",
                "reasoning": "Walmart is primarily a grocery and general merchandise store."
            },
            {
                "description": "SHELL GAS",
                "amount": "35.00",
                "category": "Transportation",
                "subcategory": "Gas",
                "confidence": "High", 
                "reasoning": "Shell is a gas station."
            },
            {
                "description": "UBER EATS",
                "amount": "25.99",
                "category": "Food",
                "subcategory": "Restaurants",
                "confidence": "High",
                "reasoning": "Uber Eats is a food delivery service typically used for restaurant meals."
            }
        ]
    
    @patch('langchain_openai.ChatOpenAI')
    def test_categorize_transactions(self, mock_chat_openai):
        """Test transaction categorization."""
        # Set up the mock
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        # Configure mock response
        mock_response = MagicMock()
        mock_response.content = json.dumps(self.expected_result)
        mock_llm.invoke.return_value = mock_response
        
        # Create categorizer with mock
        categorizer = TransactionCategorizer(
            api_key=self.api_key,
            model_name="test-model"
        )
        
        # Call the method
        result = categorizer.categorize_transactions(
            self.categories_data,
            self.transactions_data
        )
        
        # Verify result
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["category"], "Food")
        self.assertEqual(result[1]["subcategory"], "Gas")
        self.assertEqual(result[2]["confidence"], "High")
        
        # Verify the mock was called
        mock_llm.invoke.assert_called_once()

    @patch('langchain_openai.ChatOpenAI')
    def test_handle_json_decode_error(self, mock_chat_openai):
        """Test handling of invalid JSON responses."""
        # Set up the mock to return invalid JSON
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        mock_response = MagicMock()
        mock_response.content = "This is not valid JSON"
        mock_llm.invoke.return_value = mock_response
        
        # Create categorizer with mock
        categorizer = TransactionCategorizer(
            api_key=self.api_key
        )
        
        # Call the method
        result = categorizer.categorize_transactions(
            self.categories_data,
            self.transactions_data
        )
        
        # Verify empty result returned on error
        self.assertEqual(result, [])

    @patch('langchain_openai.ChatOpenAI')
    def test_handle_exception(self, mock_chat_openai):
        """Test handling of exceptions during API call."""
        # Set up the mock to raise an exception
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        mock_llm.invoke.side_effect = Exception("API error")
        
        # Create categorizer with mock
        categorizer = TransactionCategorizer(
            api_key=self.api_key
        )
        
        # Call the method
        result = categorizer.categorize_transactions(
            self.categories_data,
            self.transactions_data
        )
        
        # Verify empty result returned on error
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()