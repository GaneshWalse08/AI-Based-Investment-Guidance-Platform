"""
Authentication & User Management Service
Upgraded: Now uses SQLite for permanent user storage.
"""
import sqlite3
import hashlib
import uuid
import json
import time
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'esg_users.db')

class AuthService:
    def __init__(self):
        self._init_db()
        self._seed_demo_users()

    def _get_db_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_db_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    preferences TEXT,
                    created_at REAL
                )
            ''')
            conn.commit()

    def _hash(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def _seed_demo_users(self):
        # Check if demo user exists before seeding
        with self._get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', ('demo_investor',)).fetchone()
            if not user:
                self.register('demo_investor', 'demo@esgplatform.com', 'demo1234', {
                    'risk_tolerance': 'moderate',
                    'budget': 50000,
                    'duration': '1-3 years',
                    'sectors': ['Technology', 'Healthcare', 'Clean Energy'],
                    'esg_priority': 'high',
                })

    def register(self, username, email, password, preferences=None):
        if not username or not email or not password:
            return {'success': False, 'message': 'All fields are required.'}
        
        default_prefs = {
            'risk_tolerance': 'moderate',
            'budget': 10000,
            'duration': '1-3 years',
            'sectors': [],
            'esg_priority': 'medium',
        }
        final_prefs = preferences if preferences else default_prefs
        
        uid = str(uuid.uuid4())
        pwd_hash = self._hash(password)
        
        try:
            with self._get_db_connection() as conn:
                conn.execute(
                    'INSERT INTO users (id, username, email, password_hash, preferences, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (uid, username, email, pwd_hash, json.dumps(final_prefs), time.time())
                )
                conn.commit()
            
            user_obj = {
                'id': uid,
                'username': username,
                'email': email,
                'preferences': final_prefs
            }
            return {'success': True, 'user': user_obj, 'message': 'Account created successfully!'}
        except sqlite3.IntegrityError:
            return {'success': False, 'message': 'Username already exists. Please choose another.'}

    def login(self, username, password):
        pwd_hash = self._hash(password)
        with self._get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ? AND password_hash = ?', (username, pwd_hash)).fetchone()
            
            if user:
                user_obj = {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'preferences': json.loads(user['preferences']) if user['preferences'] else {}
                }
                return {'success': True, 'user': user_obj}
            
        return {'success': False, 'message': 'Invalid username or password.'}

    def get_profile(self, user_id):
        with self._get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            if user:
                user_obj = {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'preferences': json.loads(user['preferences']) if user['preferences'] else {}
                }
                return {'success': True, 'user': user_obj}
        return {'success': False, 'message': 'User not found.'}

    def update_profile(self, user_id, preferences):
        with self._get_db_connection() as conn:
            user = conn.execute('SELECT preferences FROM users WHERE id = ?', (user_id,)).fetchone()
            if not user:
                return {'success': False, 'message': 'User not found.'}
            
            current_prefs = json.loads(user['preferences']) if user['preferences'] else {}
            current_prefs.update(preferences)
            
            conn.execute('UPDATE users SET preferences = ? WHERE id = ?', (json.dumps(current_prefs), user_id))
            conn.commit()
            
        return {'success': True, 'message': 'Profile preferences updated successfully.'}

    def get_all_users(self):
        with self._get_db_connection() as conn:
            users = conn.execute('SELECT id, username, email, preferences FROM users').fetchall()
            result = []
            for u in users:
                result.append({
                    'id': u['id'],
                    'username': u['username'],
                    'email': u['email'],
                    'preferences': json.loads(u['preferences']) if u['preferences'] else {}
                })
            return result