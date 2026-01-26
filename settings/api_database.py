"""
API Configuration Database Module

This module provides SQLite-based storage for API configuration metadata.
Actual API key values are stored in .streamlit/secrets.toml for security.

SQLite stores:
- Custom model configurations (name, model_id, provider, temperature, base_url)
- Provider settings (enabled status, base URLs)

Author: Claude Code
Date: 26 January 2026
"""

import sqlite3
import os
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

# Database file location
DB_PATH = "settings/config/api_config.db"


def get_db_path() -> str:
    """Get the database file path, ensuring directory exists"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return DB_PATH


@contextmanager
def get_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """Initialize the database with required tables"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Custom models table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                provider TEXT NOT NULL DEFAULT 'OpenAIChatCompletionClient',
                model_id TEXT NOT NULL,
                base_url TEXT DEFAULT 'https://openrouter.ai/api/v1',
                temperature REAL DEFAULT 0.2,
                api_provider TEXT DEFAULT 'OPENROUTER',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Provider settings table (for future use)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provider_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_name TEXT UNIQUE NOT NULL,
                is_enabled INTEGER DEFAULT 1,
                base_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()


# ============ Custom Models Operations ============

def get_all_custom_models() -> List[Dict[str, Any]]:
    """Get all custom models from database"""
    init_database()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM custom_models ORDER BY name")
        rows = cursor.fetchall()

        models = []
        for row in rows:
            models.append({
                "id": row["id"],
                "name": row["name"],
                "provider": row["provider"],
                "config": {
                    "model": row["model_id"],
                    "temperature": row["temperature"],
                    "base_url": row["base_url"]
                },
                "api_provider": row["api_provider"]
            })
        return models


def get_custom_model_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get a specific custom model by name"""
    init_database()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM custom_models WHERE name = ?", (name,))
        row = cursor.fetchone()

        if row:
            return {
                "id": row["id"],
                "name": row["name"],
                "provider": row["provider"],
                "config": {
                    "model": row["model_id"],
                    "temperature": row["temperature"],
                    "base_url": row["base_url"]
                },
                "api_provider": row["api_provider"]
            }
        return None


def add_custom_model(
    name: str,
    model_id: str,
    provider: str = "OpenAIChatCompletionClient",
    base_url: str = "https://openrouter.ai/api/v1",
    temperature: float = 0.2,
    api_provider: str = "OPENROUTER"
) -> bool:
    """Add a new custom model to database"""
    init_database()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO custom_models (name, provider, model_id, base_url, temperature, api_provider)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, provider, model_id, base_url, temperature, api_provider))
            return True
    except sqlite3.IntegrityError:
        # Model with this name already exists
        return False
    except Exception as e:
        print(f"Error adding custom model: {e}")
        return False


def update_custom_model(
    name: str,
    model_id: Optional[str] = None,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: Optional[float] = None,
    api_provider: Optional[str] = None
) -> bool:
    """Update an existing custom model"""
    init_database()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query
            updates = []
            params = []

            if model_id is not None:
                updates.append("model_id = ?")
                params.append(model_id)
            if provider is not None:
                updates.append("provider = ?")
                params.append(provider)
            if base_url is not None:
                updates.append("base_url = ?")
                params.append(base_url)
            if temperature is not None:
                updates.append("temperature = ?")
                params.append(temperature)
            if api_provider is not None:
                updates.append("api_provider = ?")
                params.append(api_provider)

            if not updates:
                return True  # Nothing to update

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(name)

            query = f"UPDATE custom_models SET {', '.join(updates)} WHERE name = ?"
            cursor.execute(query, params)
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating custom model: {e}")
        return False


def delete_custom_model(name: str) -> bool:
    """Delete a custom model from database"""
    init_database()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM custom_models WHERE name = ?", (name,))
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting custom model: {e}")
        return False


def model_exists(name: str) -> bool:
    """Check if a model with the given name exists"""
    init_database()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM custom_models WHERE name = ?", (name,))
        return cursor.fetchone() is not None


# ============ Provider Settings Operations ============

def get_provider_settings(provider_name: str) -> Optional[Dict[str, Any]]:
    """Get settings for a specific provider"""
    init_database()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM provider_settings WHERE provider_name = ?", (provider_name,))
        row = cursor.fetchone()

        if row:
            return {
                "provider_name": row["provider_name"],
                "is_enabled": bool(row["is_enabled"]),
                "base_url": row["base_url"]
            }
        return None


def set_provider_settings(provider_name: str, is_enabled: bool = True, base_url: str = None) -> bool:
    """Set or update provider settings"""
    init_database()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO provider_settings (provider_name, is_enabled, base_url)
                VALUES (?, ?, ?)
                ON CONFLICT(provider_name) DO UPDATE SET
                    is_enabled = excluded.is_enabled,
                    base_url = excluded.base_url,
                    updated_at = CURRENT_TIMESTAMP
            """, (provider_name, int(is_enabled), base_url))
            return True
    except Exception as e:
        print(f"Error setting provider settings: {e}")
        return False


# ============ Migration Helper ============

def migrate_from_json(json_models: List[Dict[str, Any]]) -> int:
    """Migrate custom models from JSON format to SQLite"""
    init_database()
    migrated = 0

    for model in json_models:
        name = model.get("name", "")
        config = model.get("config", {})

        if not name or not config.get("model"):
            continue

        success = add_custom_model(
            name=name,
            model_id=config.get("model", ""),
            provider=model.get("provider", "OpenAIChatCompletionClient"),
            base_url=config.get("base_url", "https://openrouter.ai/api/v1"),
            temperature=config.get("temperature", 0.2),
            api_provider=model.get("api_provider", "OPENROUTER")
        )

        if success:
            migrated += 1

    return migrated
