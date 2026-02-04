"""
Configuration Loader - Loads and manages application configuration.
Supports YAML config files with environment variable interpolation.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def _interpolate_env_vars(value: Any) -> Any:
    """Recursively interpolate environment variables in config values."""
    if isinstance(value, str):
        # Match ${VAR_NAME} or $VAR_NAME patterns
        pattern = r'\$\{([^}]+)\}|\$([A-Z_][A-Z0-9_]*)'
        
        def replace(match):
            var_name = match.group(1) or match.group(2)
            return os.getenv(var_name, "")
        
        return re.sub(pattern, replace, value)
    elif isinstance(value, dict):
        return {k: _interpolate_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_interpolate_env_vars(item) for item in value]
    return value


class Config:
    """
    Configuration manager.
    
    Usage:
        config = Config.load("config.yaml")
        api_key = config.get("llm.providers.openai.api_key")
    """
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    @classmethod
    def load(cls, path: str | Path) -> "Config":
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f) or {}
        
        # Interpolate environment variables
        data = _interpolate_env_vars(raw_data)
        return cls(data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a config value by dot-notation key.
        
        Example:
            config.get("llm.providers.openai.api_key")
        """
        keys = key.split(".")
        value = self._data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_section(self, key: str) -> Dict[str, Any]:
        """Get an entire config section as a dict."""
        result = self.get(key, {})
        return result if isinstance(result, dict) else {}
    
    @property
    def raw(self) -> Dict[str, Any]:
        """Get the raw config data."""
        return self._data


# Global config instance
_config: Optional[Config] = None


def load_config(path: str | Path = "config.yaml") -> Config:
    """Load the global config."""
    global _config
    _config = Config.load(path)
    return _config


def get_config() -> Config:
    """Get the global config instance."""
    if _config is None:
        raise RuntimeError("Config not loaded. Call load_config() first.")
    return _config
