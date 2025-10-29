from pydantic_settings import BaseSettings
from typing import Optional, List, Union
import os


class Settings(BaseSettings):
    # Основные настройки приложения
    app_name: str = "User Management System"
    debug: bool = False
    domain: str = "user-management.yourdomain.com"
    api_base_url: str = "https://user-management.yourdomain.com/api"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    
    # Настройки базы данных
    database_url: str = "sqlite:///./data/users.db"
    
    # Active Directory настройки
    ad_domain: str = "central.st-ing.com"
    ad_server: str = "dc.central.st-ing.com"
    ad_use_ssl: bool = False
    ldap_port: int = 389
    ldap_ssl_port: int = 636
    
    # Exchange Server настройки
    exchange_server: str = "mailzone.central.st-ing.com"
    exchange_database: str = "STI_Mailbox"
    
    # SMTP настройки
    smtp_server: str = "mailzone.central.st-ing.com"
    smtp_port: int = 465
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_ssl: bool = True
    smtp_from: Optional[str] = None
    
    # 1C интеграция
    onec_endpoint: str = "/api/oneC/receive"
    onec_allowed_origins: Union[str, List[str]] = "172.17.177.57:3048,localhost:3048,user-management.yourdomain.com,https://user-management.yourdomain.com"
    
    # CORS настройки
    cors_origins: Union[str, List[str]] = "http://localhost,http://localhost:3000,https://user-management.yourdomain.com,https://www.user-management.yourdomain.com"
    
    # Пути к скриптам
    scripts_path: str = "/app/scripts"
    
    # Настройки безопасности
    # Настройки аутентификации администратора
    admin_username: str = "admin"
    admin_password: str = "admin123"
    
    # Пароль по умолчанию для новых пользователей
    default_user_password: str = "User123456"
    
    # Настройки логирования
    log_file: str = "logs/application.log"
    log_max_size_mb: int = 10
    log_max_files: int = 5
    log_level: str = "INFO"
    
    # Настройки пагинации
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Настройки экспорта
    export_max_records: int = 10000
    
    ldap_timeout: int = 30
    winrm_timeout: int = 30
    smtp_timeout: int = 30
    max_retry_attempts: int = 3

    data_dir: str = "./data"
    logs_dir: str = "./logs"
    temp_dir: str = "./temp"
    export_dir: str = "./exports"
    
    # Настройки LDAP
    ldap_base_dn: str = "DC=central,DC=st-ing,DC=com"
    ldap_user_ou: str = "OU=Users,DC=central,DC=st-ing,DC=com"
    ldap_dismissed_ou: str = "OU=Уволенные сотрудники,DC=central,DC=st-ing,DC=com"
    
    # Настройки WinRM для выполнения PowerShell на Windows сервере
    winrm_server: Optional[str] = None  # Если не указан, используется ad_server
    winrm_port: int = 5985
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self._parse_list_variables()
        
        db_path = self.database_url.replace("sqlite:///", "")
        if db_path.startswith("./"):
            db_path = db_path[2:]
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        

        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    def _parse_list_variables(self):
        """Парсит строковые переменные окружения в списки"""
        if isinstance(self.cors_origins, str):
            self.cors_origins = [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]
        
        if isinstance(self.onec_allowed_origins, str):
            self.onec_allowed_origins = [origin.strip() for origin in self.onec_allowed_origins.split(',') if origin.strip()]


settings = Settings()
