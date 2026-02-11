"""
Tests unitarios para BookingScraper.
"""

from pytest_check import check

from scraping.scraper import BookingScraper


class TestBuildUrl:
    """Tests para construcción de URL de búsqueda."""

    def test_build_url_should_include_all_parameters_when_initialized(self):
        """Verifica que la URL incluya todos los parámetros configurados."""
        scraper = BookingScraper(
            max_hotels=10,
            checkin_date="2026-03-01",
            checkout_date="2026-03-02",
            group_adults=3,
            rooms_number=2,
            group_children=1,
        )

        url = scraper._build_url()

        with check:
            assert "checkin=2026-03-01" in url
        with check:
            assert "checkout=2026-03-02" in url
        with check:
            assert "group_adults=3" in url
        with check:
            assert "no_rooms=2" in url
        with check:
            assert "group_children=1" in url
        with check:
            assert "Buenos+Aires" in url
        with check:
            assert "dest_id=-979186" in url

    def test_build_url_should_use_default_parameters_when_not_provided(self):
        """Verifica que use valores por defecto cuando no se especifican parámetros opcionales."""
        scraper = BookingScraper(
            max_hotels=5,
            checkin_date="2026-04-10",
            checkout_date="2026-04-11",
        )

        url = scraper._build_url()

        with check:
            assert "group_adults=2" in url
        with check:
            assert "no_rooms=1" in url
        with check:
            assert "group_children=0" in url


class TestCleanPrice:
    """Tests para limpieza de precios."""

    def test_clean_price_should_return_float_when_given_formatted_price(self):
        """Verifica que extraiga números de precios formateados con símbolos y comas."""
        scraper = BookingScraper(
            max_hotels=1, checkin_date="2026-01-01", checkout_date="2026-01-02"
        )

        with check:
            assert scraper._clean_price("$ 230,821") == 230821.0
        with check:
            assert scraper._clean_price("+$ 61,426") == 61426.0
        with check:
            assert scraper._clean_price("$ 1,234.56") == 1234.56

    def test_clean_price_should_return_zero_when_given_invalid_input(self):
        """Verifica que retorne 0.0 cuando el input es inválido o N/A."""
        scraper = BookingScraper(
            max_hotels=1, checkin_date="2026-01-01", checkout_date="2026-01-02"
        )

        with check:
            assert scraper._clean_price("N/A") == 0.0
        with check:
            assert scraper._clean_price("") == 0.0
        with check:
            assert scraper._clean_price("Includes taxes") == 0.0

    def test_clean_price_should_handle_decimal_prices_when_present(self):
        """Verifica que maneje correctamente precios con decimales."""
        scraper = BookingScraper(
            max_hotels=1, checkin_date="2026-01-01", checkout_date="2026-01-02"
        )

        result = scraper._clean_price("$ 150.75")

        assert result == 150.75


class TestMaxHotels:
    """Tests para límite de hoteles."""

    def test_max_hotels_should_be_capped_at_500_when_given_higher_value(self):
        """Verifica que el límite máximo de hoteles sea 500."""
        scraper = BookingScraper(
            max_hotels=1000, checkin_date="2026-01-01", checkout_date="2026-01-02"
        )

        assert scraper.max_hotels == 500

    def test_max_hotels_should_accept_value_when_below_500(self):
        """Verifica que acepte valores menores a 500."""
        scraper = BookingScraper(
            max_hotels=50, checkin_date="2026-01-01", checkout_date="2026-01-02"
        )

        assert scraper.max_hotels == 50
