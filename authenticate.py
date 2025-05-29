import os.path
import  logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QListWidget, QLineEdit, QPushButton, 
                             QLabel, QMessageBox, QFileDialog)


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time

# from main import FileSyncer

class Authenticate:
    def __init__(self, parent=None):
        self.parent = parent
        
        #Google Drive service and credentials
        self.service = None
        self.credentials = None
        self.SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
        self.is_authenticated = False

    def update_auth_status(self, is_authenticated):
        #update and return the authentication statis
        self.is_authenticated = is_authenticated
        return is_authenticated

    def try_to_authenticate(self):
        #if creds exist try authenticating automatically
        try:
            if os.path.exists("token.json"):
                creds = Credentials.from_authorized_user_file("token.json", self.SCOPES)
                if creds and creds.valid:
                    self.service = build("drive", "v3", credentials=creds)
                    self.credentials = creds
                    self.is_authenticated   #??
                elif creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    self.service = build("drive", "v3", credentials=creds)
                    self.credentials = creds
                    self.update_auth_status(True)
                    #Save the refreshed credentials
                    with open("token.json", "w") as token:
                        token.write(creds.to_json())
                    return True
            return False
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Auto Authentication Failed: {str(e)}")
            self.update_auth_status(False)
            return False

    def authenticate_google_drive(self):
        """Handle Google drive authentication"""

        try:
            creds = None
            if os.path.exists("token.json"):

                creds = Credentials.from_authorized_user_file("token.json", self.SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        "credentials.json", self.SCOPES)
                    creds = flow.run_local_server(port=0)

                # save credentials
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
            # Build e service
            self.service = build("drive", "v3", credentials=creds)
            self.credentials = creds
            self.update_auth_status(True)

            QMessageBox.information(self.parent, "Success", "Successfully authenticated with Google Drive!")
            return True
        except Exception as e:
            self.update_auth_status(False)
            QMessageBox.critical(self.parent, "Error", f"Google Failed to authenticate:{str(e)}")
            return False