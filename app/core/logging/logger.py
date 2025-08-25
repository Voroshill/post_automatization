import logging
import os
import glob
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


class UnifiedLogger:
    """Единый логгер для всего приложения с ротацией файлов"""
    
    def __init__(self, log_dir: str = "logs", max_size_mb: int = 10, max_files: int = 5):
        self.log_dir = log_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_files = max_files
        
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        self.log_file = os.path.join(log_dir, "application.log")
        
        self._setup_root_logger()
        
        self.app_logger = logging.getLogger("app")
        self.api_logger = logging.getLogger("api")
        self.db_logger = logging.getLogger("database")
        self.auth_logger = logging.getLogger("auth")
        self.export_logger = logging.getLogger("export")
        self.ldap_logger = logging.getLogger("ldap")
        self.exchange_logger = logging.getLogger("exchange")
        self.winrm_logger = logging.getLogger("winrm")
        
        self._cleanup_old_logs()
    
    def _setup_root_logger(self):
        """Настраивает корневой логгер с ротацией файлов"""
        logging.getLogger().handlers.clear()
        
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=self.max_size_bytes,
            backupCount=self.max_files - 1,
            encoding='utf-8'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def _cleanup_old_logs(self):
        """Очищает старые лог файлы если превышен лимит"""
        try:
            pattern = os.path.join(self.log_dir, "application.*")
            log_files = glob.glob(pattern)
            log_files.sort(key=os.path.getmtime, reverse=True)
            
            if len(log_files) > self.max_files:
                files_to_delete = log_files[self.max_files:]
                for file_path in files_to_delete:
                    try:
                        os.remove(file_path)
                        print(f"🗑️ Удален старый лог файл: {file_path}")
                    except Exception as e:
                        print(f"❌ Ошибка удаления файла {file_path}: {e}")
        
        except Exception as e:
            print(f"❌ Ошибка очистки логов: {e}")
    
    def get_logger(self, name: str):
        """Возвращает логгер для указанного модуля"""
        return logging.getLogger(name)
    
    def log_startup(self):
        """Логирует информацию о запуске приложения"""
        self.app_logger.info("🚀 Приложение запущено")
        self.app_logger.info(f"📁 Директория логов: {os.path.abspath(self.log_dir)}")
        self.app_logger.info(f"📏 Максимальный размер файла: {self.max_size_bytes // (1024*1024)} MB")
        self.app_logger.info(f"📚 Максимальное количество файлов: {self.max_files}")


unified_logger = UnifiedLogger()

app_logger = unified_logger.app_logger
api_logger = unified_logger.api_logger
db_logger = unified_logger.db_logger
auth_logger = unified_logger.auth_logger
export_logger = unified_logger.export_logger
ldap_logger = unified_logger.ldap_logger
exchange_logger = unified_logger.exchange_logger
winrm_logger = unified_logger.winrm_logger

def log_application_startup():
    """Логирует информацию о запуске приложения"""
    unified_logger.log_startup()
