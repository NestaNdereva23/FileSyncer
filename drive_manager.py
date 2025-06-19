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


    def list_files(self, page_size: int=50, use_cache:bool=True) -> List[Dict[str, Any]]:
        if not self.auth_manager.is_authenticated():
            raise Exception("You are npt authenticated with Google drive")

        try:
            if use_cache and self.auth_manager.current_user_email:

                cached_files = self.db_manager.get_cached_files(self.auth_manager.current_user_email)
                print("retrieved cached files")
                if cached_files:
                    self.logger.info(f"Retrieved {len(cached_files)} files from cache")
                    return cached_files

            # fetch from google drive
            result = (
                self.auth_manager.service.files()
                .list(
                    pageSize=page_size,
                    fields="nextPageToken, files(id, name, size, modifiedTime, mimeType)"
                )
                .execute()
            )
            files = result.get("files", [])

            if self.auth_manager.current_user_email:
                for file_info in files:
                    self.db_manager.cache_file_info(self.auth_manager.current_user_email, file_info)

            self.logger.info(f"Retrieved {len(files)} files from Google Drive")
            return files

        except HttpError as error:
            error_message = f"Failed to list files: {str(error)}"
            self.logger.error(error_message)
            raise Exception(error_message)

    def download_file(self, file_id:str, filename:str, download_path:str=".") -> str:
        if not self.auth_manager.is_authenticated():
            raise Exception("Not authenticated with Google drive")

        #get file metadata
        try:
            file_metadata = self.auth_manager.service.files().get(fileId=file_id).execute()
            full_path = os.path.join(download_path, filename)
            request = self.auth_manager.service.files().get_media(fileId=file_id)

            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)

            done=False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    self.logger.info(f"Download  progress: {int(status.progress() * 100)}%")

            #write the bytes to file
            file_io.seek(0)
            with open(full_path, 'wb') as f:
                f.write(file_io.read())

            self.logger.info(f"Successfully downloaded: {filename}")
            return full_path

        except HttpError as error:
            error_message = f"Failed to download files: {str(error)}"
            self.logger.error(error_message)
            raise Exception(error_message)

    def upload_file(self, file_path:str, remote_name:str = None) -> str:
        if not self.auth_manager.is_authenticated():
            raise Exception("Not authenticated with Google drive")

        try:
            if not os.path.exists(file_path):
                raise Exception(f"File not found: {file_path}")

            file_name = remote_name or os.path.basename(file_path)

            #Detect MIME type
            mime_type,_ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'

            file_metadata = {"name": file_name}
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

            #upload
            file = (
                self.auth_manager.service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            file_id = file.get("id")
            self.logger.info(f"Successfully uploaded: {file_name} (ID: {file_id})")

            #refesh the cache
            if self.auth_manager.current_user_email:
                self.list_files(use_cache=False)

            return file_id

        except HttpError as error:
            error_message = f"Failed to upload files: {str(error)}"
            self.logger.error(error_message)
            raise Exception(error_message)







