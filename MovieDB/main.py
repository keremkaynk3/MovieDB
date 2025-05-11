import sys
import sqlite3
import hashlib
import pandas as pd
import pytesseract
from PIL import Image
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QMessageBox, QListWidget, QDialog, QFormLayout,
                            QSpinBox, QDoubleSpinBox, QTextEdit, QTableWidget,
                            QTableWidgetItem, QHeaderView, QComboBox, QFileDialog,
                            QGroupBox, QRadioButton, QProgressDialog)
from PyQt6.QtCore import Qt, QEvent

# Set Tesseract path - try multiple possible locations
possible_tesseract_paths = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    r'C:\Tesseract-OCR\tesseract.exe',
    r'/usr/bin/tesseract',
    r'/usr/local/bin/tesseract'
]

for path in possible_tesseract_paths:
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
        break

# SQLite database connection
def create_connection():
    conn = sqlite3.connect('moviedb.sqlite')
    return conn

# Create tables
def setup_database():
    conn = create_connection()
    cursor = conn.cursor()
    
    # Create users table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            security_question TEXT,
            security_answer TEXT
        )
    ''')
    
    # Create movies table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_name TEXT,
            published_year INTEGER,
            genre TEXT,
            director TEXT,
            actors TEXT,
            imdb_rating REAL,
            personal_rating REAL,
            watch_date TEXT,
            note TEXT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# Hash the password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MovieDB - Login")
        self.setFixedSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Username
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        
        # Password
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.login_button = QPushButton("Login")
        self.register_button = QPushButton("Register")
        self.forgot_password_button = QPushButton("Forgot Password")
        
        self.login_button.clicked.connect(self.login)
        self.register_button.clicked.connect(self.show_register)
        self.forgot_password_button.clicked.connect(self.show_forgot_password)
        
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)
        button_layout.addWidget(self.forgot_password_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username=? AND password=?',
                       (username, hash_password(password)))
        user = cursor.fetchone()
        conn.close()

        if user:
            self.main_window = MainWindow(user[0])
            self.main_window.show()
            self.close()
        else:
            QMessageBox.critical(self, "Error", "Invalid username or password.")

    def show_register(self):
        self.register_window = RegisterWindow()
        self.register_window.show()

    def show_forgot_password(self):
        self.forgot_password_dialog = ForgotPasswordDialog(self)
        self.forgot_password_dialog.show()

class RegisterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MovieDB - Register")
        self.setFixedSize(400, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Username
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        
        # Password
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        
        # Confirm Password
        self.confirm_password_label = QLabel("Confirm Password:")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm_password_label)
        layout.addWidget(self.confirm_password_input)
        
        # Security Question
        self.security_label = QLabel("What was your elementary school teacher's name?")
        self.security_input = QLineEdit()
        layout.addWidget(self.security_label)
        layout.addWidget(self.security_input)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        
        # Register Button
        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.register)
        button_layout.addWidget(self.register_button)
        
        # Back Button
        self.back_button = QPushButton("Back to Login")
        self.back_button.clicked.connect(self.close)
        button_layout.addWidget(self.back_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        security_answer = self.security_input.text()

        if not username or not password or not confirm_password or not security_answer:
            QMessageBox.critical(self, "Error", "Please fill in all fields.")
            return

        if password != confirm_password:
            QMessageBox.critical(self, "Error", "Passwords do not match.")
            return

        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, password, security_question, security_answer) 
                VALUES (?, ?, ?, ?)
            ''', (username, hash_password(password), 
                 "What was your elementary school teacher's name?", 
                 security_answer))
            conn.commit()
            QMessageBox.information(self, "Success", "Registration successful. You can now log in.")
            self.close()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "Username already exists.")
        finally:
            conn.close()

class ForgotPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Forgot Password")
        self.setFixedSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Username
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        
        # Security Question
        self.security_label = QLabel("What was your elementary school teacher's name?")
        self.security_input = QLineEdit()
        layout.addWidget(self.security_label)
        layout.addWidget(self.security_input)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        
        # Verify Button
        self.verify_button = QPushButton("Verify")
        self.verify_button.clicked.connect(self.verify_security)
        button_layout.addWidget(self.verify_button)
        
        # Back Button
        self.back_button = QPushButton("Back to Login")
        self.back_button.clicked.connect(self.close)
        button_layout.addWidget(self.back_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def verify_security(self):
        username = self.username_input.text()
        security_answer = self.security_input.text()
        
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, security_answer 
            FROM users 
            WHERE username=?
        ''', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and user[1] and user[1].lower() == security_answer.lower():
            self.change_password_dialog = ChangePasswordDialog(user[0])
            self.change_password_dialog.show()
            self.close()
        else:
            QMessageBox.critical(self, "Error", "Invalid username or security answer.")

class ChangePasswordDialog(QDialog):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Change Password")
        self.setFixedSize(400, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # New Password
        self.password_label = QLabel("New Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        
        # Confirm Password
        self.confirm_password_label = QLabel("Confirm New Password:")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm_password_label)
        layout.addWidget(self.confirm_password_input)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        
        # Save Button
        self.save_button = QPushButton("Save New Password")
        self.save_button.clicked.connect(self.save_password)
        button_layout.addWidget(self.save_button)
        
        # Back Button
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.close)
        button_layout.addWidget(self.back_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def save_password(self):
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if password != confirm_password:
            QMessageBox.critical(self, "Error", "Passwords do not match.")
            return

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET password=? 
            WHERE id=?
        ''', (hash_password(password), self.user_id))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Success", "Password has been changed successfully.")
        self.close()

class MovieDialog(QDialog):
    def __init__(self, parent=None, movie_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Movie")
        self.setFixedSize(500, 650)
        self.movie_data = movie_data
        self.setup_ui()
        
        if self.movie_data:
            self.fill_movie_data()

    def setup_ui(self):
        layout = QFormLayout()
        
        # Movie Name
        self.name_input = QLineEdit()
        layout.addRow("Movie Name:", self.name_input)
        
        # Published Year
        self.year_input = QSpinBox()
        self.year_input.setRange(1900, 2100)
        layout.addRow("Published Year:", self.year_input)
        
        # Genre
        self.genre_input = QLineEdit()
        layout.addRow("Genre:", self.genre_input)
        
        # Director
        self.director_input = QLineEdit()
        layout.addRow("Director:", self.director_input)
        
        # Actors
        self.actors_input = QLineEdit()
        layout.addRow("Actors (comma separated):", self.actors_input)
        
        # IMDB Rating
        self.imdb_input = QDoubleSpinBox()
        self.imdb_input.setRange(0, 10)
        self.imdb_input.setSingleStep(0.1)
        layout.addRow("IMDB Rating:", self.imdb_input)
        
        # Personal Rating
        self.personal_rating_input = QDoubleSpinBox()
        self.personal_rating_input.setRange(0, 10)
        self.personal_rating_input.setSingleStep(0.1)
        layout.addRow("Personal Rating:", self.personal_rating_input)
        
        # Watch Date
        self.watch_date_input = QLineEdit()
        self.watch_date_input.setPlaceholderText("DD/MM/YYYY")
        layout.addRow("Watch Date:", self.watch_date_input)
        
        # Note
        self.note_input = QTextEdit()
        layout.addRow("Note:", self.note_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow("", button_layout)
        
        self.setLayout(layout)

    def get_movie_data(self):
        watch_date = self.watch_date_input.text()
        # Convert DD/MM/YYYY to YYYY-MM-DD for database storage
        if watch_date:
            try:
                day, month, year = watch_date.split('/')
                watch_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except:
                watch_date = ""
                
        return {
            'movie_name': self.name_input.text(),
            'published_year': self.year_input.value(),
            'genre': self.genre_input.text(),
            'director': self.director_input.text(),
            'actors': self.actors_input.text(),
            'imdb_rating': self.imdb_input.value(),
            'personal_rating': self.personal_rating_input.value(),
            'watch_date': watch_date,
            'note': self.note_input.toPlainText()
        }

    def fill_movie_data(self):
        if isinstance(self.movie_data, dict):
            # Handle dictionary input
            self.name_input.setText(self.movie_data.get('movie_name', ''))
            self.year_input.setValue(self.movie_data.get('published_year', 0))
            self.genre_input.setText(self.movie_data.get('genre', ''))
            self.director_input.setText(self.movie_data.get('director', ''))
            self.actors_input.setText(self.movie_data.get('actors', ''))
            self.imdb_input.setValue(self.movie_data.get('imdb_rating', 0))
            self.personal_rating_input.setValue(self.movie_data.get('personal_rating', 0))
            watch_date = self.movie_data.get('watch_date', '')
            if watch_date:
                try:
                    year, month, day = watch_date.split('-')
                    watch_date = f"{day}/{month}/{year}"
                except:
                    pass
            self.watch_date_input.setText(watch_date)
            self.note_input.setText(self.movie_data.get('note', ''))
        else:
            # Handle tuple input (from database)
            self.name_input.setText(self.movie_data[0] or '')
            self.year_input.setValue(self.movie_data[1] or 0)
            self.genre_input.setText(self.movie_data[2] or '')
            self.director_input.setText(self.movie_data[3] or '')
            self.actors_input.setText(self.movie_data[4] or '')
            self.imdb_input.setValue(self.movie_data[5] or 0)
            self.personal_rating_input.setValue(self.movie_data[6] or 0)
            watch_date = self.movie_data[7] or ''
            if watch_date:
                try:
                    year, month, day = watch_date.split('-')
                    watch_date = f"{day}/{month}/{year}"
                except:
                    pass
            self.watch_date_input.setText(watch_date)
            self.note_input.setText(self.movie_data[8] or '')

class IMDBTop1000Window(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("IMDB TOP 1000")
        self.setMinimumSize(1200, 800)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setup_ui()
        self.load_movies()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Search control
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search movies...")
        self.search_input.textChanged.connect(self.apply_search)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Movie table
        self.movie_table = QTableWidget()
        self.movie_table.setColumnCount(6)
        self.movie_table.setHorizontalHeaderLabels([
            "Title", "Year", "Genre", "Director", 
            "Actors", "IMDB Rating"
        ])
        
        # Set column widths
        header = self.movie_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Title
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Year
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Genre
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Director
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Actors
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # IMDB Rating
        
        layout.addWidget(self.movie_table)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        
        # Add to My List button
        self.add_button = QPushButton("Add Selected Movie to My List")
        self.add_button.clicked.connect(self.add_to_my_list)
        button_layout.addWidget(self.add_button)
        
        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def apply_search(self):
        search_text = self.search_input.text().lower()
        for row in range(self.movie_table.rowCount()):
            movie_name = self.movie_table.item(row, 0).text().lower()
            if search_text in movie_name:
                self.movie_table.setRowHidden(row, False)
            else:
                self.movie_table.setRowHidden(row, True)

    def load_movies(self):
        try:
            df = pd.read_csv('imdb_top_1000.csv')
            self.movie_table.setRowCount(len(df))
            
            for row, (_, movie) in enumerate(df.iterrows()):
                self.movie_table.setItem(row, 0, QTableWidgetItem(str(movie['Series_Title'])))
                self.movie_table.setItem(row, 1, QTableWidgetItem(str(movie['Released_Year'])))
                self.movie_table.setItem(row, 2, QTableWidgetItem(str(movie['Genre'])))
                self.movie_table.setItem(row, 3, QTableWidgetItem(str(movie['Director'])))
                self.movie_table.setItem(row, 4, QTableWidgetItem(str(movie['Star1'] + ', ' + movie['Star2'] + ', ' + movie['Star3'] + ', ' + movie['Star4'])))
                self.movie_table.setItem(row, 5, QTableWidgetItem(str(movie['IMDB_Rating'])))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load IMDB TOP 1000 list: {str(e)}")

    def add_to_my_list(self):
        current_row = self.movie_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a movie to add")
            return

        try:
            movie_data = {
                'movie_name': self.movie_table.item(current_row, 0).text(),
                'published_year': int(self.movie_table.item(current_row, 1).text()),
                'genre': self.movie_table.item(current_row, 2).text(),
                'director': self.movie_table.item(current_row, 3).text(),
                'actors': self.movie_table.item(current_row, 4).text(),
                'imdb_rating': float(self.movie_table.item(current_row, 5).text()),
                'personal_rating': 0,
                'note': "Added from IMDB TOP 1000"
            }

            dialog = MovieDialog(self, movie_data)
            if dialog.exec():
                self.parent().add_movie_from_imdb(dialog.get_movie_data())
                QMessageBox.information(self, "Success", "Movie added to your list!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error adding movie: {str(e)}")

class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Movies")
        self.setFixedSize(600, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(self.browse_button)
        layout.addLayout(file_layout)
        
        # Column mapping
        self.mapping_group = QGroupBox("Column Mapping")
        mapping_layout = QFormLayout()
        self.movie_name_combo = QComboBox()
        self.year_combo = QComboBox()
        self.genre_combo = QComboBox()
        self.director_combo = QComboBox()
        self.actors_combo = QComboBox()
        self.imdb_rating_combo = QComboBox()
        self.personal_rating_combo = QComboBox()
        self.watch_date_combo = QComboBox()
        self.note_combo = QComboBox()
        
        mapping_layout.addRow("Movie Name:", self.movie_name_combo)
        mapping_layout.addRow("Year:", self.year_combo)
        mapping_layout.addRow("Genre:", self.genre_combo)
        mapping_layout.addRow("Director:", self.director_combo)
        mapping_layout.addRow("Actors:", self.actors_combo)
        mapping_layout.addRow("IMDB Rating:", self.imdb_rating_combo)
        mapping_layout.addRow("Personal Rating:", self.personal_rating_combo)
        mapping_layout.addRow("Watch Date:", self.watch_date_combo)
        mapping_layout.addRow("Note:", self.note_combo)
        
        self.mapping_group.setLayout(mapping_layout)
        layout.addWidget(self.mapping_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.import_button = QPushButton("Import")
        self.cancel_button = QPushButton("Cancel")
        self.import_button.clicked.connect(self.import_data)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "Excel Files (*.xlsx *.xls);;CSV Files (*.csv)"
        )
            
        if file_path:
            self.file_path.setText(file_path)
            self.load_file_columns(file_path)
                
    def load_file_columns(self, file_path):
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
                
            columns = df.columns.tolist()
            
            # Clear and update all combos
            for combo in [self.movie_name_combo, self.year_combo, self.genre_combo,
                         self.director_combo, self.actors_combo, self.imdb_rating_combo,
                         self.personal_rating_combo, self.watch_date_combo, self.note_combo]:
                combo.clear()
                combo.addItem("-- Select Column --")
                combo.addItems(columns)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load file: {str(e)}")
            
    def import_data(self):
        if not self.file_path.text():
            QMessageBox.warning(self, "Warning", "Please select a file first.")
            return
            
        try:
            self.import_from_file()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")
            
    def import_from_file(self):
        if self.file_path.text().endswith('.csv'):
            df = pd.read_csv(self.file_path.text())
        else:
            df = pd.read_excel(self.file_path.text())
        
        # Create column mapping
        mapping = {
            'movie_name': self.movie_name_combo.currentText(),
            'published_year': self.year_combo.currentText(),
            'genre': self.genre_combo.currentText(),
            'director': self.director_combo.currentText(),
            'actors': self.actors_combo.currentText(),
            'imdb_rating': self.imdb_rating_combo.currentText(),
            'personal_rating': self.personal_rating_combo.currentText(),
            'watch_date': self.watch_date_combo.currentText(),
            'note': self.note_combo.currentText()
        }
        
        # Remove unmapped columns
        mapping = {k: v for k, v in mapping.items() if v != "-- Select Column --"}
        
        # Create new dataframe with mapped columns
        new_df = pd.DataFrame()
        for db_col, file_col in mapping.items():
            if file_col in df.columns:
                new_df[db_col] = df[file_col]
                
        # Convert data types
        if 'published_year' in new_df.columns:
            new_df['published_year'] = pd.to_numeric(new_df['published_year'], errors='coerce')
        if 'imdb_rating' in new_df.columns:
            new_df['imdb_rating'] = pd.to_numeric(new_df['imdb_rating'], errors='coerce')
        if 'personal_rating' in new_df.columns:
            new_df['personal_rating'] = pd.to_numeric(new_df['personal_rating'], errors='coerce')
            
        # Convert watch date format if exists
        if 'watch_date' in new_df.columns:
            new_df['watch_date'] = pd.to_datetime(new_df['watch_date'], errors='coerce')
            new_df['watch_date'] = new_df['watch_date'].dt.strftime('%Y-%m-%d')
            
        # Insert into database
        conn = create_connection()
        cursor = conn.cursor()
        
        # Create progress dialog
        progress = QProgressDialog("Importing movies...", "Cancel", 0, len(new_df), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        
        success_count = 0
        error_count = 0
        
        for index, row in new_df.iterrows():
            if progress.wasCanceled():
                break
                
            progress.setValue(index)
            
            try:
                data = row.to_dict()
                data['user_id'] = self.parent().user_id
                
                # Create placeholders for SQL query
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['?' for _ in data])
                
                cursor.execute(f'''
                    INSERT INTO movies ({columns})
                    VALUES ({placeholders})
                ''', list(data.values()))
                
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"Error importing row {index}: {str(e)}")
                
        conn.commit()
        conn.close()
        
        progress.setValue(len(new_df))
        
        message = f"Import completed!\nSuccessfully imported: {success_count}\nFailed: {error_count}"
        QMessageBox.information(self, "Import Results", message)
        self.accept()

class MainWindow(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("MovieDB")
        self.setMinimumSize(1000, 600)
        self.setup_ui()
        self.load_movies()

    def setup_ui(self):
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Filter and Sort controls
        filter_layout = QHBoxLayout()
        
        # Genre filter
        self.genre_filter = QLineEdit()
        self.genre_filter.setPlaceholderText("Filter by genre...")
        self.genre_filter.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("Genre:"))
        filter_layout.addWidget(self.genre_filter)
        
        # Sort controls
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Sort by...",
            "Name (A-Z)",
            "Name (Z-A)",
            "Year (Newest)",
            "Year (Oldest)",
            "IMDB Rating (High-Low)",
            "IMDB Rating (Low-High)",
            "Personal Rating (High-Low)",
            "Personal Rating (Low-High)",
            "Watch Date (Newest)",
            "Watch Date (Oldest)"
        ])
        self.sort_combo.currentIndexChanged.connect(self.apply_sorting)
        filter_layout.addWidget(QLabel("Sort:"))
        filter_layout.addWidget(self.sort_combo)
        
        layout.addLayout(filter_layout)
        
        # Movie table
        self.movie_table = QTableWidget()
        self.movie_table.setColumnCount(9)
        self.movie_table.setHorizontalHeaderLabels([
            "Movie Name", "Year", "Genre", "Director", 
            "Actors", "IMDB Rating", "Personal Rating", "Watch Date", "Note"
        ])
        # Set column widths
        header = self.movie_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Movie name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Year
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Genre
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Director
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Actors
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # IMDB Rating
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Personal Rating
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Watch Date
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)  # Note
        
        layout.addWidget(self.movie_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Movie")
        self.edit_button = QPushButton("Edit Movie")
        self.delete_button = QPushButton("Delete Movie")
        self.logout_button = QPushButton("Change User")
        self.imdb_button = QPushButton("IMDB TOP 1000")
        self.import_button = QPushButton("Import Movies")
        self.exit_button = QPushButton("Exit")
        
        self.add_button.clicked.connect(self.add_movie)
        self.edit_button.clicked.connect(self.edit_movie)
        self.delete_button.clicked.connect(self.delete_movie)
        self.logout_button.clicked.connect(self.logout)
        self.imdb_button.clicked.connect(self.show_imdb_list)
        self.import_button.clicked.connect(self.show_import_dialog)
        self.exit_button.clicked.connect(self.exit_application)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.imdb_button)
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.logout_button)
        button_layout.addWidget(self.exit_button)
        layout.addLayout(button_layout)

    def apply_filters(self):
        genre_filter = self.genre_filter.text().lower()
        self.load_movies(genre_filter=genre_filter)

    def apply_sorting(self):
        sort_index = self.sort_combo.currentIndex()
        if sort_index == 0:  # "Sort by..."
            return
            
        sort_options = {
            1: ("movie_name", "ASC"),  # Name (A-Z)
            2: ("movie_name", "DESC"),  # Name (Z-A)
            3: ("published_year", "DESC"),  # Year (Newest)
            4: ("published_year", "ASC"),  # Year (Oldest)
            5: ("imdb_rating", "DESC"),  # IMDB Rating (High-Low)
            6: ("imdb_rating", "ASC"),  # IMDB Rating (Low-High)
            7: ("personal_rating", "DESC"),  # Personal Rating (High-Low)
            8: ("personal_rating", "ASC"),  # Personal Rating (Low-High)
            9: ("strftime('%Y-%m-%d', watch_date)", "DESC"),  # Watch Date (Newest)
            10: ("strftime('%Y-%m-%d', watch_date)", "ASC")  # Watch Date (Oldest)
        }
        
        sort_field, sort_order = sort_options[sort_index]
        self.load_movies(sort_field=sort_field, sort_order=sort_order)

    def load_movies(self, genre_filter=None, sort_field=None, sort_order=None):
        conn = create_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT movie_name, published_year, genre, director, 
                   actors, imdb_rating, personal_rating, watch_date, note 
            FROM movies 
            WHERE user_id=?
        '''
        params = [self.user_id]
        
        if genre_filter:
            query += " AND LOWER(genre) LIKE ?"
            params.append(f"%{genre_filter}%")
            
        if sort_field:
            query += f" ORDER BY {sort_field} {sort_order}"
            
        cursor.execute(query, params)
        movies = cursor.fetchall()
        
        self.movie_table.setRowCount(len(movies))
        for row, movie in enumerate(movies):
            self.movie_table.setItem(row, 0, QTableWidgetItem(movie[0] or ""))
            self.movie_table.setItem(row, 1, QTableWidgetItem(str(movie[1]) if movie[1] else ""))
            self.movie_table.setItem(row, 2, QTableWidgetItem(movie[2] or ""))
            self.movie_table.setItem(row, 3, QTableWidgetItem(movie[3] or ""))
            self.movie_table.setItem(row, 4, QTableWidgetItem(movie[4] or ""))
            self.movie_table.setItem(row, 5, QTableWidgetItem(str(movie[5]) if movie[5] else ""))
            self.movie_table.setItem(row, 6, QTableWidgetItem(str(movie[6]) if movie[6] else ""))
            watch_date = movie[7] or ""
            if watch_date:
                try:
                    year, month, day = watch_date.split('-')
                    watch_date = f"{day}/{month}/{year}"
                except:
                    pass
            self.movie_table.setItem(row, 7, QTableWidgetItem(watch_date))
            self.movie_table.setItem(row, 8, QTableWidgetItem(movie[8] or ""))
        
        conn.close()

    def add_movie(self):
        dialog = MovieDialog(self)
        if dialog.exec():
            movie_data = dialog.get_movie_data()
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO movies (
                    movie_name, published_year, genre, director, 
                    actors, imdb_rating, personal_rating, watch_date, note, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                movie_data['movie_name'],
                movie_data['published_year'],
                movie_data['genre'],
                movie_data['director'],
                movie_data['actors'],
                movie_data['imdb_rating'],
                movie_data['personal_rating'],
                movie_data['watch_date'],
                movie_data['note'],
                self.user_id
            ))
            conn.commit()
            conn.close()
            self.load_movies()

    def edit_movie(self):
        current_row = self.movie_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a movie to edit")
            return

        movie_name = self.movie_table.item(current_row, 0).text()
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT movie_name, published_year, genre, director, 
                   actors, imdb_rating, personal_rating, watch_date, note 
            FROM movies 
            WHERE movie_name=? AND user_id=?
        ''', (movie_name, self.user_id))
        movie = cursor.fetchone()
        conn.close()

        if movie:
            dialog = MovieDialog(self, movie)
            if dialog.exec():
                movie_data = dialog.get_movie_data()
                conn = create_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE movies 
                    SET movie_name=?, published_year=?, genre=?, director=?,
                        actors=?, imdb_rating=?, personal_rating=?, watch_date=?, note=?
                    WHERE movie_name=? AND user_id=?
                ''', (
                    movie_data['movie_name'],
                    movie_data['published_year'],
                    movie_data['genre'],
                    movie_data['director'],
                    movie_data['actors'],
                    movie_data['imdb_rating'],
                    movie_data['personal_rating'],
                    movie_data['watch_date'],
                    movie_data['note'],
                    movie_name,
                    self.user_id
                ))
                conn.commit()
                conn.close()
                self.load_movies()

    def delete_movie(self):
        current_row = self.movie_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a movie to delete")
            return

        movie_name = self.movie_table.item(current_row, 0).text()
        reply = QMessageBox.question(self, "Confirm Delete",
                                   f"Are you sure you want to delete {movie_name}?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM movies WHERE movie_name=? AND user_id=?',
                           (movie_name, self.user_id))
            conn.commit()
            conn.close()
            self.load_movies()

    def logout(self):
        reply = QMessageBox.question(self, "Confirm Logout",
                                   "Are you sure you want to change user?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.login_window = LoginWindow()
            self.login_window.show()
            self.close()

    def show_imdb_list(self):
        self.imdb_window = IMDBTop1000Window(self)
        self.imdb_window.show()

    def add_movie_from_imdb(self, movie_data):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO movies (
                movie_name, published_year, genre, director, 
                actors, imdb_rating, personal_rating, watch_date, note, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            movie_data['movie_name'],
            movie_data['published_year'],
            movie_data['genre'],
            movie_data['director'],
            movie_data['actors'],
            movie_data['imdb_rating'],
            movie_data['personal_rating'],
            movie_data['watch_date'],
            movie_data['note'],
            self.user_id
        ))
        conn.commit()
        conn.close()
        self.load_movies()

    def show_import_dialog(self):
        dialog = ImportDialog(self)
        if dialog.exec():
            self.load_movies()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Confirm Exit",
                                   "Are you sure you want to exit?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    def exit_application(self):
        self.close()

if __name__ == '__main__':
    setup_database()
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
