"""
Google Sheets integration utilities.
"""

import json
import logging
from typing import Dict, Any, Optional

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

from cryptography.fernet import Fernet
from config import settings

logger = logging.getLogger(__name__)


class GoogleSheetsClient:
    """
    Client for interacting with Google Sheets API.
    """
    
    def __init__(self, credentials_path: str) -> None:
        """
        Initialize the GoogleSheetsClient with credentials.
        
        Args:
            credentials_path: Path to the encrypted Google credentials file
        """
        self.credentials_path = credentials_path
        self.service = None
        
    def _get_service(self) -> Resource:
        """
        Get or create the Google Sheets service.
        
        Returns:
            Authenticated Google Sheets service
        """
        if self.service is None:
            try:
                # In the original code, there was a decrypt_creds function
                # Here we're assuming that function exists in a utility module
                credentials = self._decrypt_credentials(self.credentials_path)
                SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
                creds = service_account.Credentials.from_service_account_info(
                credentials, scopes=SCOPES)
                # Create the service
                self.service = build('sheets', 'v4', credentials=creds)
                logger.debug("Google Sheets service initialized successfully")
            except Exception as e:
                logger.exception("Failed to initialize Google Sheets service: %s", str(e))
                raise
                
        return self.service
    
    def _decrypt_credentials(self, credentials_path: str) -> service_account.Credentials:
        """
        Decrypt Google Cloud credentials from an encrypted file.
        
        Args:
            credentials_path: Path to the encrypted credentials file
            
        Returns:
            Google service account credentials
        """
        # This implementation depends on your specific encryption method
        # For now, we'll just load the credentials directly
        # In a real implementation, you would decrypt them first
        
        try:
            # Placeholder for actual decryption logic
            logger.debug("Decrypting Google credentials from %s", credentials_path)
            
            # For demonstration purposes, assuming the file is already decrypted
            fernet = Fernet(settings.ENCRYPT_KEY)
            with open(credentials_path, "rb") as file:
                # read the encrypted data
                encrypted_data = file.read()
                # decrypt data
            keys = fernet.decrypt(encrypted_data)
            keys = json.loads(keys)
            return keys
        except Exception as e:
            logger.exception("Failed to decrypt credentials: %s", str(e))
            raise
    
    def export_sheet_range(self, spreadsheet_id: str, range_name: str) -> pd.DataFrame:
        """
        Export data from a Google Sheet range into a pandas DataFrame.
        
        Args:
            spreadsheet_id: ID of the Google Spreadsheet
            range_name: A1 notation of the range to export
            
        Returns:
            DataFrame containing the data from the specified range
        """
        try:
            logger.debug("Exporting data from sheet range: %s", range_name)
            service = self._get_service()
            
            # Call the Sheets API
            sheet = service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.warning("No data found in range: %s", range_name)
                return pd.DataFrame()
                
            # Convert to DataFrame
            # Assuming first row contains headers
            df = pd.DataFrame(values[1:], columns=values[0])
            logger.debug("Successfully exported %d rows from %s", len(df), range_name)
            return df
            
        except HttpError as e:
            logger.exception("Google Sheets API error: %s", str(e))
            raise
        except Exception as e:
            logger.exception("Error exporting sheet range: %s", str(e))
            raise
    def update_sheet_range(self, spreadsheet_id: str, range_name: str, df: pd.DataFrame) -> None:
        """
        Update a Google Sheet range with data from a pandas DataFrame.
        
        Args:
            spreadsheet_id: ID of the Google Sheet
            range_name: A1 notation of the range to update
            df: DataFrame containing the data to update
        """
        logger.info(f"Updating range {range_name} in sheet {spreadsheet_id}")
        try:
            # Convert DataFrame to list of lists for Google Sheets API
            df_clean =  df.copy()
            df_clean = df_clean.fillna("")
            
            headers = df_clean.columns.tolist()
            data = df_clean.values.tolist()
            values = [headers] + data
            
            body = {
                'values': values
            }
            
            service = self._get_service()
            
            # Call the Sheets API
            sheet = service.spreadsheets()
            result = sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells')
            logger.info(f"Updated {updated_cells} cells in Google Sheets")
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error updating sheet range: {str(e)}")
            raise