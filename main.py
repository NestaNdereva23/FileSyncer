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

#Base Class
class FileSyncer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Syncer")
        self.setGeometry(100, 100, 400, 500)

    
        #Google Drive service and credentials
        self.service = None
        self.credentials = None
        self.SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]

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

        #Sync files button
        self.sync_files_button = QPushButton("Sync Files")
        self.sync_files_button.setStyleSheet("Color: green")
        self.buttons_layout.addWidget(self.sync_files_button)

        #Upload files button
        self.upload_files_button = QPushButton("Upload Files")
        self.upload_files_button.setStyleSheet("Color: green")
        self.buttons_layout.addWidget(self.upload_files_button)

        #Files list
        self.files_list = QListWidget()
        self.files_list.setStyleSheet("QListWidget { font-size: 14px; }")
        self.main_layout.addWidget(self.files_list)

        self.auth = Authenticate(self) # create an instance of authenticate
        self.auth.try_to_authenticate()
       # self.is_authenticated = Authenticate.update_auth_status()

    # def is_authenticated(self, is_authenticated):


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileSyncer()
    window.show()
    sys.exit(app.exec_())


