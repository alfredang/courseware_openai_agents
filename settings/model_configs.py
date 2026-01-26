"""
Centralized Model Configuration Module

This module manages all AI model configurations for the Courseware AutoGen system.
It provides a unified interface for accessing different model configurations across
all modules (CourseProposal, Assessment, Courseware, etc.).

Author: Derrick Lim
Date: 3 March 2025
"""

import streamlit as st
from typing import Dict, Any

# Get API keys from the new API management system
from settings.api_manager import load_api_keys

api_keys = load_api_keys()
OPENROUTER_API_KEY = api_keys.get("OPENROUTER_API_KEY", "")

# OpenRouter DeepSeek (Default for all modules)
deepseek_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "deepseek/deepseek-chat",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "temperature": 0.2,
        "response_format": {
            "type": "json_object",
            "json_schema": {
                "name": "default_response",
                "strict": False
            }
        },
        "model_info": {
            "family": "unknown",
            "function_calling": False,
            "json_output": True,
            "vision": False,
            "structured_output": True
        }
    }
}

# OpenRouter GPT-4o-Mini
gpt4o_mini_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "openai/gpt-4o-mini",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "temperature": 0.2,
        "response_format": {
            "type": "json_object",
            "json_schema": {
                "name": "default_response",
                "strict": False
            }
        },
        "model_info": {
            "family": "openai",
            "function_calling": True,
            "json_output": True,
            "vision": False,
            "structured_output": True
        }
    }
}

# OpenRouter Claude Sonnet 3.5
claude_sonnet_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "anthropic/claude-3.5-sonnet",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "temperature": 0.2,
        "response_format": {
            "type": "json_object",
            "json_schema": {
                "name": "default_response",
                "strict": False
            }
        },
        "model_info": {
            "family": "anthropic",
            "function_calling": True,
            "json_output": True,
            "vision": True,
            "structured_output": True
        }
    }
}

# OpenRouter Gemini Flash
gemini_flash_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "google/gemini-2.0-flash-exp",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "temperature": 0.2,
        "response_format": {
            "type": "json_object",
            "json_schema": {
                "name": "default_response",
                "strict": False
            }
        },
        "model_info": {
            "family": "google",
            "function_calling": False,
            "json_output": True,
            "vision": True,
            "structured_output": True
        }
    }
}

# OpenRouter Gemini Pro
gemini_pro_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "google/gemini-pro-1.5",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "temperature": 0.2,
        "response_format": {
            "type": "json_object",
            "json_schema": {
                "name": "default_response",
                "strict": False
            }
        },
        "model_info": {
            "family": "google",
            "function_calling": False,
            "json_output": True,
            "vision": True,
            "structured_output": True
        }
    }
}

# Set default config to DeepSeek
default_config = deepseek_config

# Model choices (All via OpenRouter)
MODEL_CHOICES = {
    "DeepSeek-Chat": deepseek_config,
    "GPT-4o-Mini": gpt4o_mini_config,
    "Claude-Sonnet-3.5": claude_sonnet_config,
    "Gemini-Flash": gemini_flash_config,
    "Gemini-Pro": gemini_pro_config
}

def get_model_config(choice: str) -> Dict[str, Any]:
    """
    Return the chosen model config dict from SQLite database, or fallback to static config.

    Args:
        choice: The model choice string (model name)

    Returns:
        Model configuration dictionary with api_provider for dynamic API key resolution
    """
    # First try to get from SQLite database (includes both built-in and custom models)
    from settings.api_database import get_model_by_name

    db_model = get_model_by_name(choice)
    if db_model:
        # Get API key dynamically based on api_provider
        api_keys = load_api_keys()
        api_provider = db_model.get("api_provider", "OPENROUTER")
        api_key = api_keys.get(f"{api_provider}_API_KEY", "")

        return {
            "name": db_model["name"],
            "provider": db_model["provider"],
            "api_provider": api_provider,
            "config": {
                "model": db_model["config"]["model"],
                "base_url": db_model["config"].get("base_url", "https://openrouter.ai/api/v1"),
                "api_key": api_key,
                "temperature": db_model["config"].get("temperature", 0.2),
            }
        }

    # Fallback to static configurations
    static_config = MODEL_CHOICES.get(choice, default_config)
    if static_config:
        # Add api_provider for consistency
        return {**static_config, "api_provider": "OPENROUTER"}

    return {**default_config, "api_provider": "OPENROUTER"}

def get_all_model_choices() -> Dict[str, Dict[str, Any]]:
    """
    Get all available model choices using static configurations only
    
    Returns:
        Dictionary of all available models
    """
    # Return static model configurations only (bypassing UI API manager)
    return MODEL_CHOICES

def get_assessment_default_config() -> Dict[str, Any]:
    """
    Get default model config for Assessment module (DeepSeek via OpenRouter).

    Returns:
        Model configuration optimized for content generation
    """
    return deepseek_config

def get_courseware_default_config() -> Dict[str, Any]:
    """
    Get default model config for Courseware module (DeepSeek via OpenRouter).

    Returns:
        Model configuration optimized for document generation
    """
    return deepseek_config