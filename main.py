import sys
import os
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QListWidget, QLineEdit, QPushButton, 
                             QLabel, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QUrl
import json
from urllib.parse import unquote 
from authenticate import Authenticate

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

#Base Class
class FileSyncer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.auth = Authenticate(parent=self) # create an instance of authenticate
        
        self.setWindowTitle("File Syncer")
        self.setGeometry(100, 100, 400, 500)

        #Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        #Main Layout
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        #Buttons layout
        self.buttons_layout = QHBoxLayout()
        self.main_layout.addLayout(self.buttons_layout)

        #Authentication status label
        self.auth_status_label = QLabel("Not authenticated")
        self.auth_status_label.setStyleSheet("color: red;")
        self.main_layout.addWidget(self.auth_status_label)

        self.auth.try_to_authenticate()
        #authentiate button
        self.authenticate_button = QPushButton("Authenticate Google Drive")
        self.authenticate_button.clicked.connect(self.handle_authentication)
        self.buttons_layout.addWidget(self.authenticate_button)

        #Sync files button
        self.sync_files_button = QPushButton("Sync Files")
        self.sync_files_button.setStyleSheet("Color: green")
        self.sync_files_button.clicked.connect(self.sync_files)
        self.buttons_layout.addWidget(self.sync_files_button)

        #Upload files button
        self.upload_files_button = QPushButton("Upload Files")
        self.upload_files_button.setStyleSheet("Color: green")
        self.buttons_layout.addWidget(self.upload_files_button)

        #Files list
        self.files_list = QListWidget()
        self.files_list.setStyleSheet("QListWidget { font-size: 14px; }")
        self.main_layout.addWidget(self.files_list)




    def handle_authentication(self):
        auth_success = self.auth.authenticate_google_drive()
        self.handle_auth_status(auth_success)

    def handle_auth_status(self, is_authenticated):
        """Update the UI based on authentication status"""
        print(is_authenticated)
        if is_authenticated:
            self.auth_status_label.setText(" Authenticated with Google drive")
            self.auth_status_label.setStyleSheet("color: green;")
            self.upload_files_button.setEnabled(True)
            self.authenticate_button.setText("Re-authenticate")
        else:
            self.auth_status_label.setText(" Not authenticated!!")
            self.auth_status_label.setStyleSheet("color: red;")
            self.upload_files_button.setEnabled(False)
            self.authenticate_button.setText("Authenticate Google Drive")
        pass

    def sync_files(self):
        if not self.auth.service:
            QMessageBox.warning(self, "Not Authenticated", "Pleaase authenticate with Google")
            return

        self.list_drive_files()

    #List drive files
    def list_drive_files(self):
        try:
            #Call the drive api
            result = (
                self.auth.service.files()
                .list(pageSize=10, fields="nextPageToken, files(id, name)")
                .execute()
            )
            items = result.get("files", [])

            if not items:
                print("No files found.")
                QMessageBox.information(self, "No Files", "No files found in Google Drive")
                return
            
            print("Files:")
            #clear the existing items
            self.files_list.clear()

            for item in items:
                self.files_list.addItem(item['name'])
        
        except HttpError as error:
            QMessageBox.critical(self, "Google Drive Error", f"An error occurred: {error}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list files: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileSyncer()
    window.show()
    sys.exit(app.exec_())


