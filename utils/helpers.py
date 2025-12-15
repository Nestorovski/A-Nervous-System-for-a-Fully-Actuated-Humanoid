"""Utility functions for application"""

import logging
import os
from typing import Any, Dict

def setup_logging(level=logging.INFO, log_file=None):
    """Setup application logging"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            *(logging.FileHandler(log_file) for _ in [log_file] if log_file)
        ]
    )

def ensure_directory(path: str) -> bool:
    """Ensure directory exists, create if necessary"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Failed to create directory {path}: {e}")
        return False

def clamp_value(value: float, min_val: float, max_val: float) -> float:
    """Clamp value to range"""
    return max(min_val, min(max_val, value))

def scale_value(value: float, from_min: float, from_max: float,
               to_min: float, to_max: float) -> float:
    """Scale value from one range to another"""
    # Clamp input to source range
    value = clamp_value(value, from_min, from_max)

    # Scale to target range
    if from_max == from_min:
        return to_min

    ratio = (value - from_min) / (from_max - from_min)
    return to_min + ratio * (to_max - to_min)

def deep_merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = base.copy()

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result

def format_bytes(size: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}TB"

def validate_config(config: Dict[str, Any], schema: Dict[str, Any]) -> list:
    """Basic configuration validation"""
    errors = []

    for key, expected_type in schema.items():
        if key in config:
            if not isinstance(config[key], expected_type):
                errors.append(f"'{key}' should be {expected_type.__name__}, got {type(config[key]).__name__}")
        else:
            errors.append(f"Missing required config key: '{key}'")

    return errors
