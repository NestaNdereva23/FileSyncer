import io
import os
import mimetypes
from typing import List, Dict, Any, Optional
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from database import DatabaseManager
import logging

class DriveManager:
    ''' handles google drives operations like download, upload'''

    def __init__(self, auth_manager, db_manager: DatabaseManager):
        self.auth_manager = auth_manager
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)

