import json
import os.path
import  logging
from typing import Optional, Tuple
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from database import DatabaseManager
# from main import FileSyncer

#Google Drive service and cedentials
class AuthManager:
    def __init__(self, db_manager=DatabaseManager):
        self.db_manager = db_manager
        self.service = None
        self.credentials = None
        self.current_user_email = None
        self.SCOPES = ["https://www.googleapis.com/auth/drive"]
        self.CREDENTIALS_FILE = "credentials.json"

        #logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def initialize_session(self) -> bool:
        try:
            session = self.db_manager.get_active_user_session()
            if session:
                credentials_data = json.loads(session['credentials.json'])
                creds = Credentials.from_authorized_user_info(credentials_data, self.SCOPES)

                if creds and creds.valid:
                    self.service = build("drive", "v3", credentials=creds)
                    self.credentials = creds
                    self.current_user_email = session['user_email']
                    self.logger.info(f"Restored session for user: {self.current_user_email}")
                    return True
                elif creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    self.service = build("drive", "v3", credentials=creds)
                    self.credentials = creds
                    self.current_user_email = session['user_email']

                    #update stored credentials
                    self.db_manager.save_user_session(
                        self.current_user_email,
                        creds.to_json()
                    )
                    self.logger.info(f"Refreshed session for user: {self.current_user_email}")
                    return True
            return False
        except Exception as e:
            self.logger.info(f"Failed to initialize session: {str(e)}")
            return False

    def authenticate(self) -> Tuple[bool, str]:
        """Google drive authentication"""
        try:
            if not os.path.exists(self.CREDENTIALS_FILE):
                return False, "credentials.json file not found. Add your Google API credentials"
            creds = None

            #try getting existing credentials
            session = self.db_manager.get_active_user_session()
            if session:
                credentials_data = json.loads(session['credentials.json'])
                creds = Credentials.from_authorized_user_file("token.json", self.SCOPES)

            #if not valid creds start google Oauth flow
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        "credentials.json", self.SCOPES)
                    creds = flow.run_local_server(port=0)


            # Build e service
            self.service = build("drive", "v3", credentials=creds)
            self.credentials = creds

            try:
                about = self.service.about().get(fields="user").execute()
                self.current_user_email = about['user']['emailAddress']
            except Exception as e:
                self.current_user_email = "unknown@example.com"
                self.logger.info(f"Could not get user email: {str(e)}")

            # Save session to db
            self.db_manager.save_user_session(
                self.current_user_email,
                creds.to_json()
            )
            self.logger.info(f"Successfully authenticated user: {self.current_user_email}")
            return True, f"Successfully authenticated as {self.current_user_email}"

        except Exception as e:
            error_message = f"Authentication failed: {str(e)}"
            self.logger.error(error_message)
            return False, error_message

    def logout(self) -> bool:
        """Logout current user"""
        try:
            if self.current_user_email:
                self.db_manager.logout_user(self.current_user_email)
                self.logger.info(f"Logged out user: {self.current_user_email}")

            self.service = None
            self.credentials = None
            self.current_user_email = None
            return True
        except Exception as e:
            self.logger.error(f"Logout failed: {str(e)}")
            return False

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return self.service is not None and self.current_user_email is not None

    def get_current_user(self) -> Optional[str]:
        """Get current user email"""
        return self.current_user_email