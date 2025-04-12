import os
from configparser import ConfigParser

class ConfigManager:
    def __init__(self, config_path="config/settings.ini"):
        self.config_path = config_path
        self.config = self._read_config()

    def _read_config(self):
        """Read and validate configuration file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file {self.config_path} not found.")
        
        parser = ConfigParser()
        parser.read(self.config_path)
        
        config = {section: dict(parser.items(section)) for section in parser.sections()}
        
        # Validate required fields
        required = {
            'API': ['tushare_token'],
            'Database': ['daily_db', 'financial_db']
        }
        for section, fields in required.items():
            if section not in config:
                raise ValueError(f"Missing section {section} in config.")
            for field in fields:
                if field not in config[section]:
                    raise ValueError(f"Missing field {field} in section {section}.")
        
        return config

    def get_api_config(self):
        """Return API configuration."""
        return self.config['API']

    def get_database_config(self):
        """Return database configuration."""
        return self.config['Database']