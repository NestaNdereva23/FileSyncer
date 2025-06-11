import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
import logging

class DatabaseManager:
    """Handles all database operations for the app"""

    def __init__(self, db_path: str = "filesyncer.db"):
        self.db_path = db_path
        self.init_database()


    def init_database(self):
        # initialize the db with required tables
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # User sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT UNIQUE,
                    credentials_json TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # App settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Monitored paths
            # cursor.execute('''
            #    # CREATE TABLE IF NOT EXISTS monitored_paths (
            #     1                      id INTEGER PRIMARY KEY AUTOINCREMENT,
            #     2                      user_email TEXT,
            #     3                      local_path TEXT,
            #     4                      remote_path TEXT,
            #     5                      is_active BOOLEAN DEFAULT TRUE,
            #     6                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            # ●   7                      FOREIGN KEY (user_email) REFERENCES user_sessions (user_email)
            #     8                  )
            #     9              ''')
            # ●  10
            # File Cache table --> track filestates 
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT,
                    file_id TEXT,
                    file_name TEXT,
                    file_size INTEGER,
                    modified_time TEXT,
                    mime_type TEXT,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_email) REFERENCES user_sessions (user_email)
                )
             ''')

            conn.commit()

    def save_user_session(self, user_email: str, credentials_json: str):
        """Save or update user session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_sessions (user_email, credentials_json, is_active, last_login)
                VALUES (?, ?, TRUE, CURRENT_TIMESTAMP)
            ''', (user_email, credentials_json))
            conn.commit()
    
    def get_active_user_session(self) -> Optional[Dict[str, Any]]:
        '''gET Active user session'''
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                            SELECT user_email, credential_json, last_login
                            FROM user_sessions
                            WHERE is_active = TRUE
                            ORDER BY last_login DESC
                            LIMIT 1
                         ''')
            result = cursor.fetchone()
            if result:
                return {
                    'user_email': result[0],
                    'credentials_json': result[1],
                    'last_login': result[2]
                }
            return None

    def logout_user(self, user_email: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_sessions
                SET is_active = FALSE
                WHERE user_email = ?
            ''', (user_email,))
            conn.commit()

    def save_setting(self, key: str, value:str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO app_settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value,))
            conn.commit()

    def get_setting(self, key: str, default:str = None) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM app_settings WHERE key = ?', (key,))
            result = cursor.fetchone()
            return  result[0] if result else default

    def cache_file_info(self, user_email: str, file_info: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO file_cache
                (user_email, file_id, file_name, file_size, modified_time, mime_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_email,
                  file_info.get('id'),
                  file_info.get('name'),
                  file_info.get('size'),
                  file_info.get('modifiedTime'),
                  file_info.get('mimeType')
                  ))
            conn.commit()

    def get_cached_files(self, user_email: str) -> list:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT file_id, file_name, file_size, modified_time, mime_type
                FROM file_cache
                WHERE user_email = ?
                ORDER BY cached_at DESC
            ''', (user_email,))
            results = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'size': row[2],
                    'modifiedTime': row[3],
                    'mimeType': row[4],
                    'cachedAt': row[5]
                }
                for row in results
            ]







