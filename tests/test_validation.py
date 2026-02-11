"""
Tests unitarios para funciones de validación de fechas.
"""

from datetime import datetime, timedelta

import pytest
from pytest_check import check

from utils.input_validators import validate_date, validate_dates


class TestValidateDate:
    """Tests para validate_date()"""

    def test_validate_date_should_return_valid_date_when_format_is_correct(self):
        """Verifica que se acepte una fecha con formato YYYY-MM-DD válido."""
        with check:
            result = validate_date("2025-03-15", "test_field")
            assert result == "2025-03-15"

        with check:
            result = validate_date("2026-12-31", "test_field")
            assert result == "2026-12-31"

    def test_validate_date_should_raise_error_when_date_is_invalid(self):
        """Verifica que se lance ValueError cuando la fecha no existe."""
        with pytest.raises(ValueError):
            validate_date("2025-02-30", "test_field")

        with pytest.raises(ValueError):
            validate_date("2025-13-01", "test_field")


class TestValidateDates:
    """Tests para validate_dates()"""

    def test_validate_dates_should_return_tuple_when_dates_are_valid(self):
        """Verifica que se retorne tupla de fechas cuando ambas son válidas."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

        checkin, checkout = validate_dates(tomorrow, day_after)

        with check:
            assert checkin == tomorrow
        with check:
            assert checkout == day_after

    def test_validate_dates_should_raise_error_when_checkout_before_checkin(self):
        """Verifica que se lance ValueError cuando checkout es anterior a checkin."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

        with pytest.raises(ValueError, match="checkout_date debe ser posterior"):
            validate_dates(day_after, tomorrow)

    def test_validate_dates_should_raise_error_when_checkout_equals_checkin(self):
        """Verifica que se lance ValueError cuando checkout es igual a checkin."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        with pytest.raises(ValueError, match="checkout_date debe ser posterior"):
            validate_dates(tomorrow, tomorrow)

    def test_validate_dates_should_raise_error_when_checkin_is_past_date(self):
        """Verifica que se lance ValueError cuando checkin es una fecha pasada."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        with pytest.raises(
            ValueError, match="checkin_date no puede ser una fecha pasada"
        ):
            validate_dates(yesterday, tomorrow)

    def test_validate_dates_should_accept_today_as_checkin(self):
        """Verifica que se acepte hoy como fecha de checkin."""
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        checkin, checkout = validate_dates(today, tomorrow)

        with check:
            assert checkin == today
        with check:
            assert checkout == tomorrow
