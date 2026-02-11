"""
Page Object Model para la página de búsqueda de Booking.com.

Centraliza todos los selectores de elementos de la página para facilitar
el mantenimiento cuando Booking.com cambie su estructura HTML.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BookingSearchPageElements:
    """
    Selectores de elementos para la página de resultados de búsqueda.
    """

    # Tarjeta de hotel
    HOTEL_CARD: str = "[data-testid='property-card']"

    # Elementos dentro de la tarjeta
    HOTEL_NAME: str = "[data-testid='title']"
    HOTEL_LOCATION: str = "[data-testid='address-link']"
    HOTEL_INITIAL_PRICE: str = "[data-testid='price-and-discounted-price']"

    # Este o puede tener texto inidcando que el precio inicial incluye fee
    # o puede tener texto + precio, ej "Includes taxes and fees" o "+$ 61,426 taxes and fees"
    HOTEL_FEES: str = "[data-testid='taxes-and-charges']"

    HOTEL_RATING_LABEL: str = "div.f63b14ab7a f546354b44 becbee2f63"
    HOTEL_SCORE: str = "div.f63b14ab7a dff2e52086"
    HOTEL_REVIEWS_COUNT: str = "div.fff1944c52 fb14de7f14 eaa8455879"
    HOTEL_LINK: str = "[data-testid='title-link']"

    # Pasar de página
    LOAD_MORE_BUTTON: str = 'button:has-text("Load more results")'

    # Cierre de pop-ups
    CLOSE_POPUPS = 'button[aria-label="Dismiss sign-in info."], button[aria-label="Close"], .modal-close'


# Instancia singleton para uso en el scraper
PAGE_ELEMENTS = BookingSearchPageElements()
