"""
Configuration management for LED Receiver
Supports loading from JSON/YAML files
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger('ndi_receiver.config')


class Config:
    """Configuration manager"""
    
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self.data = data or {}
    
    @classmethod
    def load(cls, filepath: str) -> 'Config':
        """Load configuration from file"""
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")
        
        logger.info(f"Loading config from {filepath}")
        
        # Support JSON and YAML
        if path.suffix in ['.json']:
            with open(path, 'r') as f:
                data = json.load(f)
        elif path.suffix in ['.yaml', '.yml']:
            try:
                import yaml
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
            except ImportError:
                raise ImportError("PyYAML not installed. Install with: pip install pyyaml")
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")
        
        return cls(data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.data.get(key, default)
    
    def save(self, filepath: str):
        """Save configuration to file"""
        path = Path(filepath)
        
        logger.info(f"Saving config to {filepath}")
        
        if path.suffix in ['.json']:
            with open(path, 'w') as f:
                json.dump(self.data, f, indent=2)
        elif path.suffix in ['.yaml', '.yml']:
            try:
                import yaml
                with open(path, 'w') as f:
                    yaml.dump(self.data, f, default_flow_style=False)
            except ImportError:
                raise ImportError("PyYAML not installed")
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")


