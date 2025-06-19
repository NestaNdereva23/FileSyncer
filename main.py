import io
import mimetypes
import sys
import os
import shutil
from os import PRIO_PGRP

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPushButton, QLabel, QMessageBox, QFileDialog,
    QListWidgetItem, QStatusBar, QMenuBar, QAction, QProgressBar
)
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal
import json
from urllib.parse import unquote 
from authenticate import AuthManager
from googleapiclient.errors import HttpError
from database import DatabaseManager
from drive_manager import DriveManager

#Base Class
''' Habdle file operations without blocking UI '''
class FileOperationThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, operation, *args, **kwargs):
        super().__init__()
        self.operation = operation
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.operation(*self.args, **self.kwargs)
            self.finished.emit(True, str(result))
        except Exception as e:
            self.finished.emit(False, str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # managers
        self.db_manager = DatabaseManager()
        self.auth_manager = AuthManager(self.db_manager)
        self.drive_manager = DriveManager(self.auth_manager, self.db_manager)

        self.init_ui()
        self.restore_session()

    def init_ui(self):

        self.setWindowTitle("File Syncer")
        self.setGeometry(100, 100, 800, 600)

        #Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        #Main Layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Status section
        status_layout = QHBoxLayout()
        self.auth_status_label = QLabel("Not authenticated")
        self.auth_status_label.setStyleSheet("color: red; font-weight: bold;")
        self.user_info_label = QLabel("")
        status_layout.addWidget(QLabel("Status:"))
        status_layout.addWidget(self.auth_status_label)
        status_layout.addWidget(self.user_info_label)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)

        #Buttons layout
        buttons_layout = QHBoxLayout()

        self.auth_button = QPushButton("Authenticate")
        self.auth_button.clicked.connect(self.handle_authentication)

        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.handle_logout)
        self.logout_button.setEnabled(False)

        self.refresh_button = QPushButton("Refresh Files")
        self.refresh_button.clicked.connect(self.refresh_files)
        self.refresh_button.setEnabled(False)

        self.upload_button = QPushButton("Upload File")
        self.upload_button.clicked.connect(self.upload_file)
        self.upload_button.setEnabled(False)

        self.download_button = QPushButton("Download Selected")
        self.download_button.clicked.connect(self.download_selected_file)
        self.download_button.setEnabled(False)

        buttons_layout.addWidget(self.auth_button)
        buttons_layout.addWidget(self.logout_button)
        buttons_layout.addWidget(self.refresh_button)
        buttons_layout.addWidget(self.upload_button)
        buttons_layout.addWidget(self.download_button)

        main_layout.addLayout(buttons_layout)

        # Files list
        self.files_list = QListWidget()
        self.files_list.setStyleSheet("QListWidget { font-size: 12px; }")
        self.files_list.itemSelectionChanged.connect(self.on_file_selection_changed)
        main_layout.addWidget(self.files_list)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        auth_action = QAction('Authenticate', self)
        auth_action.triggered.connect(self.handle_authentication)
        file_menu.addAction(auth_action)

        logout_action = QAction('Logout', self)
        logout_action.triggered.connect(self.handle_logout)
        file_menu.addAction(logout_action)

        file_menu.addSeparator()

        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def restore_session(self):
        """Try to restore previous user session"""
        if self.auth_manager.initialize_session():
            self.update_ui_authenticated(True)
            self.load_files()
            self.status_bar.showMessage("Session restored successfully")
        else:
            self.update_ui_authenticated(False)
            self.status_bar.showMessage("No previous session found")

    def handle_authentication(self):
        self.status_bar.showMessage("Authenticating......")
        self.auth_button.setEnabled(False)

        try:
            success, message = self.auth_manager.authenticate()
            if success:
                self.update_ui_authenticated(True)
                self.load_files()
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.critical(self, "Authentication Failed", message)
                self.update_ui_authenticated(False)
            self.status_bar.showMessage(message)
        except Exception as e:
            err_msg = f"Authentication error: {str(e)}"
            QMessageBox.critical(self, "Error", err_msg)
            self.status_bar.showMessage(err_msg)
        finally:
            self.auth_button.setEnabled(True)

    def update_ui_authenticated(self, is_authenticated: bool):
        if is_authenticated:
            self.auth_status_label.setText("Authenticated")
            self.auth_status_label.setStyleSheet("color: green; font-weight:bold")
            self.user_info_label.setText(f"User: {self.auth_manager.get_current_user()}")
            self.auth_button.setText("Re-authenticate")
            self.logout_button.setEnabled(True)
            self.refresh_button.setEnabled(True)
            self.upload_button.setEnabled(True)
        else:
            self.auth_status_label.setText("NOt Authenticated")
            self.auth_status_label.setStyleSheet("color: red; font-weight:bold")
            self.user_info_label.setText(f"User: {self.auth_manager.get_current_user()}")
            self.auth_button.setText("Authenticate")
            self.logout_button.setEnabled(False)
            self.refresh_button.setEnabled(False)
            self.upload_button.setEnabled(False)

    def load_files(self, use_cache: bool = True):
        if not self.auth_manager.is_authenticated():
            return

        try:
            self.status_bar.showMessage("Loading files.....")
            print("loading")
            files = self.drive_manager.list_files(use_cache=use_cache)
            print("listing")
            self.populate_files_list(files)
            self.status_bar.showMessage(f"Loaded {len(files)} files")
        except Exception as e:
            err_msg = f"Failed to load files: {str(e)}"
            QMessageBox.critical(self, "Error", err_msg)
            self.status_bar.showMessage(err_msg)

    def populate_files_list(self, files):
        '''Populate file list widget'''
        print("about to populate")
        self.files_list.clear()

        for file_info in files:
            file_name = file_info.get('name', 'Unknown')
            file_size = file_info.get('size', 0)

            if file_size:
                size_mb = int(file_size) / (1024*1024)
                size_str = f" {size_mb:.2f}MB" if size_mb > 1 else f" {int(file_size)/1000} KB"
            else:
                size_str = ""

            disp_text = f"{file_name}__{size_str}"
            item = QListWidgetItem(disp_text)
            item.setData(Qt.UserRole, file_info)
            self.files_list.addItem(item)

    def handle_logout(self):
        reply = QMessageBox.question(
            self, 'Confirm Logout',
            'Are you sure you want to logout?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.auth_manager.logout():
                self.update_ui_authenticated(False)
                self.files_list.clear()
                self.status_bar.showMessage("Logged out successfully")
                QMessageBox.information(self, "Success", "Logged out success")
            else:
                QMessageBox.critical(self, "Error", "Failed to logout")

    def upload_file(self):
        ''' Upload file to google drive '''
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Upload")

        if file_path:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)

            self.upload_thread = FileOperationThread(
                self.drive_manager.upload_file, file_path
            )
            self.upload_thread.finished.connect(self.on_upload_finished)
            self.upload_thread.start()

    def on_upload_finished(self, success: bool, message:str):
        self.progress_bar.setVisible(False)

        if success:
            QMessageBox.information(self, "Success", f"File uploaded successfully!\n File ID: {message}")
            self.refresh_files()
        else:
            QMessageBox.critical(self, "Upload Failed", message)

        self.status_bar.showMessage("Upload completed" if success else "Upload failed")

    def download_selected_file(self):
    
        current_item = self.files_list.currentItem()
        if not current_item:
            return

        file_info = current_item.data(Qt.UserRole)
        file_id = file_info.get('id')
        file_name = file_info.get('name')

        if not file_id or not file_name:
            QMessageBox.warning(self, "Error", "Invalid file selection")
            return
        
        download_path = QFileDialog.getExistingDirectory(self, "Select Dowload Location")
        if not download_path:
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.download_thread = FileOperationThread(
            self.drive_manager.download_file, file_id, file_name, download_path
        )
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()

    def on_download_finished(self, success:bool, message:str):
        self.progress_bar.setVisible(False)


        if success:
            QMessageBox.information(self, "Success", f"File downloaded successfully!\n Saved to: {message}")
            self.refresh_files()
        else:
            QMessageBox.critical(self, "Downlaod Failed", message)

        self.status_bar.showMessage("Download completed" if success else "Download failed")

    def refresh_files(self):
        self.load_files(use_cache=False)
    
    def on_file_selection_changed(self):
        current_item = self.files_list.currentItem()
        self.download_button.setEnabled(current_item is  not None and self.auth_manager.is_authenticated())

    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


