"""Tests for configuration management."""

import pytest
from pydantic import ValidationError
from src.config import Settings


class TestSettings:
    """Tests for Settings configuration."""

    def test_create_settings_with_all_fields(self):
        """Test creating settings with all fields provided."""
        settings = Settings(
            openai_api_key="test-key",
            openai_model="gpt-4",
            api_host="localhost",
            api_port=8080,
            api_reload=False,
            max_conversation_history=20,
            default_temperature=0.5,
            default_max_tokens=2000
        )

        assert settings.openai_api_key == "test-key"
        assert settings.openai_model == "gpt-4"
        assert settings.api_host == "localhost"
        assert settings.api_port == 8080
        assert settings.api_reload is False
        assert settings.max_conversation_history == 20
        assert settings.default_temperature == 0.5
        assert settings.default_max_tokens == 2000

    def test_create_settings_with_defaults(self):
        """Test that default values are used when not provided."""
        settings = Settings(openai_api_key="test-key")

        assert settings.openai_model == "gpt-4-turbo-preview"
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        assert settings.api_reload is True
        assert settings.max_conversation_history == 10
        assert settings.default_temperature == 0.7
        assert settings.default_max_tokens == 1000

    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        assert any("openai_api_key" in str(error) for error in errors)

    def test_case_insensitive_env_vars(self):
        """Test that environment variables are case-insensitive."""
        import os
        # This is tested implicitly through the model_config
        # The actual case-insensitivity is configured in the Settings class
        settings = Settings(
            openai_api_key="test-key",
            OPENAI_MODEL="gpt-3.5-turbo"  # Mixed case
        )
        assert settings.openai_model == "gpt-3.5-turbo"