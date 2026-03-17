"""
Tests for B2B usage tracking module.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from core.usage_tracking import log_b2b_usage


class TestLogB2BUsage:
    """Tests for log_b2b_usage function."""

    @patch("core.usage_tracking.SessionLocal")
    def test_successful_logging(self, mock_session_cls):
        """Verify a usage record is committed on success."""
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        log_b2b_usage(
            tenant_id=1,
            endpoint="/v2/b2b/generate",
            method="POST",
            status_code=200,
            response_time_ms=150,
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("core.usage_tracking.SessionLocal")
    def test_sqlalchemy_error_is_swallowed(self, mock_session_cls):
        """Verify SQLAlchemyError is caught and does not propagate."""
        mock_db = MagicMock()
        mock_db.commit.side_effect = SQLAlchemyError("db error")
        mock_session_cls.return_value = mock_db

        # Must NOT raise
        log_b2b_usage(
            tenant_id=1,
            endpoint="/v2/b2b/generate",
            method="POST",
            status_code=200,
        )

        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("core.usage_tracking.SessionLocal")
    def test_unexpected_error_is_swallowed(self, mock_session_cls):
        """Verify unexpected exceptions are caught and do not propagate."""
        mock_db = MagicMock()
        mock_db.add.side_effect = RuntimeError("unexpected")
        mock_session_cls.return_value = mock_db

        # Must NOT raise
        log_b2b_usage(
            tenant_id=1,
            endpoint="/v2/b2b/generate",
            method="POST",
            status_code=500,
            error_message="something broke",
        )

        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("core.usage_tracking.SessionLocal")
    def test_user_id_defaults_to_none(self, mock_session_cls):
        """Verify user_id is None when not provided (B2B flow)."""
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        log_b2b_usage(
            tenant_id=1,
            endpoint="/v2/b2b/generate",
            method="POST",
            status_code=200,
        )

        record = mock_db.add.call_args[0][0]
        assert record.user_id is None
        assert record.tenant_id == 1

    @patch("core.usage_tracking.SessionLocal")
    def test_error_message_stored(self, mock_session_cls):
        """Verify error_message is passed through to the record."""
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        log_b2b_usage(
            tenant_id=5,
            endpoint="/v2/b2b/critic/analyze",
            method="POST",
            status_code=502,
            error_message="Critic service returned an error.",
        )

        record = mock_db.add.call_args[0][0]
        assert record.error_message == "Critic service returned an error."
        assert record.status_code == 502

    @patch("core.usage_tracking.SessionLocal")
    def test_session_always_closed(self, mock_session_cls):
        """Verify db.close() is called even when commit raises."""
        mock_db = MagicMock()
        mock_db.commit.side_effect = SQLAlchemyError("commit failed")
        mock_session_cls.return_value = mock_db

        log_b2b_usage(
            tenant_id=1,
            endpoint="/v2/b2b/generate",
            method="POST",
            status_code=200,
        )

        mock_db.close.assert_called_once()
