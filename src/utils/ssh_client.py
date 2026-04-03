"""
SSH client module for H5 Reader.

Provides SSH/SFTP connectivity for remote file access.
"""
from typing import Optional
import paramiko
import json
import os
import logging
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QCheckBox, QMessageBox, QFileDialog

logger = logging.getLogger(__name__)

SETTINGS_FILE = os.path.expanduser('~/.h5reader_ssh_settings')
DEFAULT_DOWNLOAD_DIR = os.path.expanduser('~/Downloads')


def load_saved_settings() -> dict:
    """
    Load saved SSH settings from file.
    
    Returns:
        Dict with saved settings or empty dict if not found.
    """
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load SSH settings: {e}")
    return {'download_dir': DEFAULT_DOWNLOAD_DIR}


def save_settings(settings: dict) -> None:
    """
    Save SSH settings to file.
    
    Args:
        settings: Dict with settings to save.
    """
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)
    except Exception as e:
        logger.warning(f"Could not save SSH settings: {e}")


class SSHConnection:
    """
    SSH/SFTP connection manager.
    
    Provides methods for connecting to SSH servers and transferring files.
    """
    
    def __init__(self):
        """Initialize SSH connection with default values."""
        self.client: Optional[paramiko.SSHClient] = None
        self.sftp: Optional[paramiko.SFTPClient] = None
        self.host: str = ''
        self.port: int = 22
        self.username: str = ''
        self.password: str = ''
        self.connected: bool = False
        self.last_error: str = ''
    
    def connect(self, host: str, port: int, username: str, password: str, key_file: str = None, timeout: int = 30) -> bool:
        """
        Connect to SSH server.
        
        Args:
            host: Server hostname or IP address
            port: SSH port number
            username: Username for authentication
            password: Password for authentication
            key_file: Optional path to private key file
            timeout: Connection timeout in seconds
        
        Returns:
            True if connection successful, False otherwise
        """
        self.last_error = ''
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': host,
                'port': port,
                'username': username,
                'timeout': timeout,
                'banner_timeout': 30,
                'auth_timeout': 30,
                'allow_agent': False,
                'look_for_keys': False,
                'compress': True
            }
            
            if key_file:
                connect_kwargs['key_filename'] = key_file
            else:
                connect_kwargs['password'] = password
            
            logger.info(f"Connecting to {host}:{port} as {username}...")
            self.client.connect(**connect_kwargs)
            logger.info("Connected, opening SFTP...")
            self.sftp = self.client.open_sftp()
            self.host = host
            self.port = port
            self.username = username
            self.password = password
            self.connected = True
            logger.info("SFTP session opened successfully")
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"SSH connection error: {self.last_error}")
            return False
    
    def disconnect(self) -> None:
        """Close SSH and SFTP connections."""
        try:
            if self.sftp:
                self.sftp.close()
                self.sftp = None
        except Exception as e:
            logger.warning(f"Error closing SFTP: {e}")
        try:
            if self.client:
                self.client.close()
                self.client = None
        except Exception as e:
            logger.warning(f"Error closing SSH client: {e}")
        self.connected = False
    
    def list_directory(self, path: str) -> list:
        """
        List directory contents.
        
        Args:
            path: Directory path to list
        
        Returns:
            List of filenames in directory, empty list if not connected
        """
        if not self.connected or not self.sftp:
            return []
        try:
            return self.sftp.listdir(path)
        except Exception as e:
            logger.warning(f"Could not list directory {path}: {e}")
            return []
    
    def list_directory_attr(self, path: str) -> list:
        """
        List directory contents with attributes.
        
        Args:
            path: Directory path to list
        
        Returns:
            List of SFTPAttributes, empty list if not connected
        """
        if not self.connected or not self.sftp:
            return []
        try:
            return self.sftp.listdir_attr(path)
        except Exception as e:
            logger.warning(f"Could not list directory {path}: {e}")
            return []
    
    def is_connected(self) -> bool:
        """
        Check if connection is active.
        
        Returns:
            True if connected, False otherwise
        """
        return self.connected


class SSHDialog(QDialog):
    """
    Dialog for SSH connection settings.
    
    Provides UI for entering host, port, credentials, and key file options.
    """
    
    def __init__(self, parent=None):
        """
        Initialize SSH connection dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle('SSH Connection')
        self.setModal(True)
        self._setup_ui()
        self._load_saved_settings()
    
    def _load_saved_settings(self):
        """Load and apply saved settings."""
        settings = load_saved_settings()
        if settings:
            self.host_input.setText(settings.get('host', ''))
            self.port_input.setValue(settings.get('port', 22))
            self.user_input.setText(settings.get('username', ''))
            if settings.get('use_key', False):
                self.key_check.setChecked(True)
                self.key_input.setText(settings.get('key_file', ''))
            else:
                self.pass_input.setText(settings.get('password', ''))
            self.download_dir_input.setText(settings.get('download_dir', DEFAULT_DOWNLOAD_DIR))
    
    def _on_browse_download(self):
        """Open file dialog to select download directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Download Directory", 
            self.download_dir_input.text() or DEFAULT_DOWNLOAD_DIR
        )
        if directory:
            self.download_dir_input.setText(directory)
    
    def _save_settings(self, host: str, port: int, username: str, password: str, use_key: bool, key_file: str, download_dir: str):
        """
        Save settings to file.
        
        Args:
            host: Server hostname
            port: SSH port
            username: Username
            password: Password
            use_key: Whether to use key authentication
            key_file: Path to key file
            download_dir: Download directory path
        """
        settings = {
            'host': host,
            'port': port,
            'username': username,
            'use_key': use_key,
            'download_dir': download_dir
        }
        if use_key:
            settings['key_file'] = key_file
        else:
            settings['password'] = password
        save_settings(settings)
    
    def _setup_ui(self):
        """Set up dialog UI components."""
        layout = QVBoxLayout(self)
        
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel('Host:'))
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText('example.com or IP')
        host_layout.addWidget(self.host_input)
        layout.addLayout(host_layout)
        
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel('Port:'))
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(22)
        port_layout.addWidget(self.port_input)
        layout.addLayout(port_layout)
        
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel('Username:'))
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText('username')
        user_layout.addWidget(self.user_input)
        layout.addLayout(user_layout)
        
        pass_layout = QHBoxLayout()
        pass_layout.addWidget(QLabel('Password:'))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText('password')
        pass_layout.addWidget(self.pass_input)
        layout.addLayout(pass_layout)
        
        key_layout = QHBoxLayout()
        self.key_check = QCheckBox('Use key file:')
        self.key_check.toggled.connect(self._on_key_toggled)
        key_layout.addWidget(self.key_check)
        self.key_input = QLineEdit()
        self.key_input.setEnabled(False)
        self.key_input.setPlaceholderText('/path/to/keyfile')
        key_layout.addWidget(self.key_input)
        layout.addLayout(key_layout)
        
        download_layout = QHBoxLayout()
        download_layout.addWidget(QLabel('Download dir:'))
        self.download_dir_input = QLineEdit()
        self.download_dir_input.setPlaceholderText(DEFAULT_DOWNLOAD_DIR)
        download_layout.addWidget(self.download_dir_input)
        self.browse_download_btn = QPushButton('Browse')
        self.browse_download_btn.clicked.connect(self._on_browse_download)
        download_layout.addWidget(self.browse_download_btn)
        layout.addLayout(download_layout)
        
        save_check_layout = QHBoxLayout()
        self.save_check = QCheckBox('Save settings')
        self.save_check.setChecked(True)
        save_check_layout.addWidget(self.save_check)
        layout.addLayout(save_check_layout)
        
        self.connect_btn = QPushButton('Connect')
        self.connect_btn.clicked.connect(self.accept)
        layout.addWidget(self.connect_btn)
        
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)
    
    def _on_key_toggled(self, checked: bool):
        """
        Handle key file checkbox toggle.
        
        Args:
            checked: Whether checkbox is checked
        """
        self.pass_input.setEnabled(not checked)
        self.key_input.setEnabled(checked)
    
    def get_connection_params(self) -> tuple:
        """
        Get connection parameters from dialog.
        
        Returns:
            Tuple of (host, port, username, password, key_file, download_dir)
        """
        host = self.host_input.text()
        port = self.port_input.value()
        username = self.user_input.text()
        use_key = self.key_check.isChecked()
        password = self.pass_input.text() if not use_key else ''
        key_file = self.key_input.text() if use_key else None
        download_dir = self.download_dir_input.text() or DEFAULT_DOWNLOAD_DIR
        
        if self.save_check.isChecked():
            self._save_settings(host, port, username, password, use_key, key_file if use_key else '', download_dir)
        
        return (host, port, username, password, key_file, download_dir)
