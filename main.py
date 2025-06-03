import io
import mimetypes
import sys
import os
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QListWidget, QLineEdit, QPushButton,
                             QLabel, QMessageBox, QFileDialog, QListWidgetItem)
from PyQt5.QtCore import Qt, QUrl
import json
from urllib.parse import unquote 
from authenticate import Authenticate

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import google.auth

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

        #Sync files button  --updates the files list
        self.sync_files_button = QPushButton("Sync Files")
        self.sync_files_button.setStyleSheet("Color: green")
        self.sync_files_button.clicked.connect(self.sync_files)
        self.buttons_layout.addWidget(self.sync_files_button)

        #download files button
        self.download_files_button = QPushButton("Download")
        self.download_files_button.setStyleSheet("Color: red")
        self.download_files_button.clicked.connect(self.download_file)
        self.buttons_layout.addWidget(self.download_files_button)

        # Upload files button
        self.upload_files_button = QPushButton("Upload Files")
        self.upload_files_button.setStyleSheet("Color: green")
        self.upload_files_button.clicked.connect(self.select_file)
        self.buttons_layout.addWidget(self.upload_files_button)

        # Files list
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
                # # self.files_list.addItem(item['name'])
                # self.files_list.addItems([item['name'], item['id']])
                # print(item)
                file_item = QListWidgetItem(item['name'])
                file_item.setData(Qt.UserRole, item['id'])
                self.files_list.addItem(file_item)

        except HttpError as error:
            QMessageBox.critical(self, "Google Drive Error", f"An error occurred: {error}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list files: {str(e)}")

    def download_file(self):
        current_file = self.files_list.currentItem()

        if current_file:
            file_id = current_file.data(Qt.UserRole)

        # google drive download implem
        try:
            # get the file metadata before downloading
            file_metadata = self.auth.service.files().get(fileId=file_id).execute()
            filename = file_metadata['name']

            # Create drive api client
            with open(filename, 'wb') as file:
                request = self.auth.service.files().get_media(fileId=file_id, supportsAllDrives=True)
                file = io.BytesIO()
                downloader = MediaIoBaseDownload(file, request)
                done = False

                while done is False:
                    status, done = downloader.next_chunk()
                    print(f"Download {int(status.progress() * 100)}%")

                '''Write the data into the file'''
                file.seek(0)
                with open(filename, 'wb') as f:
                    f.write(file.read())

            QMessageBox.critical(self, "Download Success", f"Successfully downloaded the file {filename}")

        except HttpError as error:
            QMessageBox.critical(self, "Download Error", f"Failed to Download File: {str(error)}")
            file = None

    # select a file from path
    def select_file(self):
        try:
            file_path, _ = QFileDialog.getOpenFileUrl(None, "File")
            file_url = file_path.toLocalFile()    # clean to get base file path
            # selected_file_name = os.path.basename(file_url) # get base file name
            if file_url:
                self.upload_file(file_url)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to select file: {str(e)}")

    # upload selected File 
    def upload_file(self, file_url):
        print(f"ready to upload file at: {file_url}")
        try:
            file_name = os.path.basename(file_url)

            #detect mime type
            mime_type, _ = mimetypes.guess_type(file_url)
            if mime_type is None:
                mime_type = 'application/octet-stream'

            print(f"Detected MIME type: {mime_type}")

            file_metadata = {"name": file_name}
            media = MediaFileUpload(file_url, mimetype=mime_type, resumable=True)

            file = (
                self.auth.service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            print(f'File with ID: "{file}" has been uploaded')
        except HttpError as error:
            print(f"An error occurred: {error}")
            file = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileSyncer()
    window.show()
    sys.exit(app.exec_())


