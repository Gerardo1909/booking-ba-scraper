"""
Módulo que contiene el scraper principal del sistema.
"""

import random
import re
import time
from typing import Generator, List, Optional

from playwright.sync_api import (
    Browser,
    BrowserContext,
    ElementHandle,
    Page,
    Playwright,
    sync_playwright,
)
from playwright_stealth import Stealth

from config.settings import settings
from models.hotel import Hotel
from scraping.page_elements import PAGE_ELEMENTS
from utils.logger import scraping_logger


class BookingScraper:
    """
    Scraper para extraer información de hoteles desde Booking.com.
    """

    def __init__(
        self,
        max_hotels: int,
        checkin_date: str,
        checkout_date: str,
        group_adults: int = 2,
        rooms_number: int = 1,
        group_children: int = 0,
    ) -> None:
        """
        Inicializa el scraper con la cantidad máxima de hoteles a extraer.

        Args:
            max_hotels: Número máximo de hoteles a obtener (máximo 500).
            checkin_date: Fecha de check-in en formato YYYY-MM-DD.
            checkout_date: Fecha de check-out en formato YYYY-MM-DD.
            group_adults: Número de adultos (default: 2).
            rooms_number: Número de habitaciones (default: 1).
            group_children: Número de niños (default: 0).
        """
        self.max_hotels = min(max_hotels, 500)
        self.checkin_date = checkin_date
        self.checkout_date = checkout_date
        self.group_adults = group_adults
        self.rooms_number = rooms_number
        self.group_children = group_children

        self.url = self._build_url()
        self._processed_hotels: set[str] = set()

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        scraping_logger.info(
            f"Scraper inicializado: max_hotels={self.max_hotels}, "
            f"checkin={checkin_date}, checkout={checkout_date}"
        )

    def _build_url(self) -> str:
        """
        Construye la URL de búsqueda con los parámetros configurados.

        Returns:
            URL completa para la búsqueda en Buenos Aires.
        """
        base_url = "https://www.booking.com"
        params = (
            f"/searchresults.html?ss=Buenos+Aires"
            f"&ssne=Buenos+Aires&ssne_untouched=Buenos+Aires"
            f"&dest_id=-979186&dest_type=city"
            f"&checkin={self.checkin_date}"
            f"&checkout={self.checkout_date}"
            f"&group_adults={self.group_adults}"
            f"&no_rooms={self.rooms_number}"
            f"&group_children={self.group_children}"
            f"&lang=en-us"
        )
        return f"{base_url.rstrip('/')}/{params.lstrip('/')}"

    def _init_browser(self, playwright: Playwright) -> Browser:
        """
        Inicializa el browser en modo headless.

        Args:
            playwright: Instancia de Playwright.

        Returns:
            Browser configurado y listo para usar.
        """
        scraping_logger.debug("Iniciando browser en modo headless")
        return playwright.chromium.launch(headless=False)

    def _create_context(self) -> BrowserContext:
        """
        Crea un contexto de browser con configuraciones anti-detección.

        Returns:
            Contexto configurado con user-agent y viewport apropiados.
        """
        if not self._browser:
            raise RuntimeError("Browser no inicializado")

        user_agent = settings.USER_AGENT

        scraping_logger.debug(f"Creando contexto con user-agent: {user_agent[:50]}...")
        return self._browser.new_context(
            user_agent=settings.USER_AGENT,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
        )

    def _navigate_to_search(self) -> None:
        """
        Navega a la página de búsqueda de hoteles en Buenos Aires.

        Espera a que la página cargue completamente antes de retornar.
        """
        if not self._context:
            raise RuntimeError("Contexto no inicializado")

        self._page = self._context.new_page()
        stealth_config = Stealth()
        stealth_config.apply_stealth_sync(self._page)
        scraping_logger.info(f"Navegando a: {self.url}")

        self._page.goto(self.url, timeout=settings.TIMEOUT * 1000)
        self._page.wait_for_load_state("domcontentloaded")

        self._random_delay(2.0, 4.0)
        scraping_logger.info("Página cargada correctamente")

    def _scroll_page(self) -> bool:
        """
        Realiza scroll hacia abajo para triggear lazy loading.

        Returns:
            True si se cargaron nuevos elementos, False si llegó al final.
        """
        if not self._page:
            return False

        previous_height = self._page.evaluate("document.body.scrollHeight")
        self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        self._random_delay(3.0, 6.0)

        new_height = self._page.evaluate("document.body.scrollHeight")
        return new_height > previous_height

    def _handle_popups(self) -> None:
        """Intenta cerrar pop-ups de Genius o login que bloquean el click."""
        if not self._page:
            return

        try:
            close_button = self._page.query_selector(PAGE_ELEMENTS.CLOSE_POPUPS)
            if close_button and close_button.is_visible():
                scraping_logger.info("Pop-up intrusivo detectado. Cerrando...")
                close_button.click()
                self._random_delay(0.5, 1.0)
        except Exception:
            pass

    def _click_load_more(self) -> bool:
        """
        Simula el clic en el botón 'Load more results' si está presente.

        Returns:
            True si se logró hacer clic en el botón, False en caso contrario.
        """
        if not self._page:
            return False

        try:
            button = self._page.wait_for_selector(
                PAGE_ELEMENTS.LOAD_MORE_BUTTON, timeout=5000
            )
            if button and button.is_visible():
                button.scroll_into_view_if_needed()
                scraping_logger.debug(
                    "Botón 'Load more results' detectado. Clickeando..."
                )
                button.click(force=True)
                self._random_delay(3.0, 5.0)
                return True
        except Exception as e:
            scraping_logger.warning(
                "No se encontró más botón de carga o se alcanzó el final."
            )
        return False

    def _get_hotel_cards(self) -> List[ElementHandle]:
        """
        Obtiene todas las tarjetas de hotel actualmente visibles en el DOM.

        Returns:
            Lista de elementos representando cada tarjeta de hotel.
        """
        if not self._page:
            return []
        selector = f"{PAGE_ELEMENTS.HOTEL_CARD}:not([data-scraped='true'])"
        return self._page.query_selector_all(selector)

    def _parse_hotel_card(self, card: ElementHandle) -> Optional[Hotel]:
        """
        Extrae la información de una tarjeta de hotel individual.

        Args:
            card: Elemento de Playwright representando la tarjeta.

        Returns:
            Objeto Hotel con los datos extraídos, o None si falla el parseo.
        """
        try:
            nombre = self._extract_text_safe(card, PAGE_ELEMENTS.HOTEL_NAME)
            link = self._extract_href_safe(card, PAGE_ELEMENTS.HOTEL_LINK)
            card.evaluate("node => node.setAttribute('data-scraped', 'true')")
            # Evitar duplicados usando el link como identificador único
            if link in self._processed_hotels:
                return None
            self._processed_hotels.add(link)

            ubicacion = self._extract_text_safe(card, PAGE_ELEMENTS.HOTEL_LOCATION)

            raw_precio_inicial = self._extract_text_safe(
                card, PAGE_ELEMENTS.HOTEL_INITIAL_PRICE
            )
            precio_inicial_float = self._clean_price(raw_precio_inicial)

            raw_fees = self._extract_text_safe(card, PAGE_ELEMENTS.HOTEL_FEES)
            fees_float = self._clean_price(raw_fees)

            # Calcular total
            precio_final_float = precio_inicial_float + fees_float

            calificacion = self._extract_text_safe(
                card, PAGE_ELEMENTS.HOTEL_RATING_LABEL
            )
            puntaje = self._extract_text_safe(card, PAGE_ELEMENTS.HOTEL_SCORE)
            reviews = self._extract_text_safe(card, PAGE_ELEMENTS.HOTEL_REVIEWS_COUNT)

            return Hotel(
                nombre_hotel=nombre,
                ubicacion=ubicacion,
                checkin_date=self.checkin_date,
                checkout_date=self.checkout_date,
                precio_inicial=str(precio_inicial_float),
                precio_impuesto=str(fees_float),
                precio_final=str(precio_final_float),
                calificacion=calificacion,
                puntaje=puntaje,
                cantidad_reviews=reviews,
                link_detalle=link,
            )

        except Exception as e:
            scraping_logger.warning(f"Error parseando tarjeta de hotel: {e}")
            return None

    def _clean_price(self, price_str: str) -> float:
        """
        Limpia strings como '$ 230,821', '+$ 61,426' o 'Includes taxes'
        y los convierte a float.
        """
        if not price_str or "N/A" in price_str:
            return 0.0
        price_str = price_str.replace("\xa0", " ").strip()
        match = re.search(r"(\d+[\d,.]*)", price_str)
        if match:
            num_str = match.group(1)
            try:
                clean_num = num_str.replace(",", "")
                return float(clean_num)
            except ValueError:
                return 0.0
        return 0.0

    def _extract_text_safe(
        self, card: ElementHandle, selector: str, default: str = "N/A"
    ) -> str:
        """
        Extrae texto de un elemento de forma segura, retornando default si falla.

        Args:
            card: Elemento padre donde buscar.
            selector: Selector CSS del elemento hijo.
            default: Valor por defecto si no se encuentra el elemento.

        Returns:
            Texto extraído o valor por defecto.
        """
        try:
            element = card.query_selector(selector)
            if element:
                text = element.inner_text()
                return text.strip() if text else default
        except Exception:
            pass
        return default

    def _extract_href_safe(
        self, card: ElementHandle, selector: str, default: str = "N/A"
    ) -> str:
        """
        Extrae el atributo href de un elemento de forma segura.

        Args:
            card: Elemento padre donde buscar.
            selector: Selector CSS del elemento hijo.
            default: Valor por defecto si no se encuentra el elemento.

        Returns:
            URL extraída o valor por defecto.
        """
        try:
            element = card.query_selector(selector)
            if element:
                href = element.get_attribute("href")
                return href if href else default
        except Exception:
            pass
        return default

    def _wait_for_new_content(
        self, previous_count: int, timeout_ms: int = 5000
    ) -> bool:
        """
        Espera a que se carguen nuevos hoteles después de scroll/click.

        Args:
            previous_count: Cantidad de hoteles antes de la acción.
            timeout_ms: Tiempo máximo de espera en milisegundos.

        Returns:
            True si se cargaron nuevos hoteles, False si timeout.
        """
        if not self._page:
            return False

        start_time = time.time()
        timeout_sec = timeout_ms / 1000

        while time.time() - start_time < timeout_sec:
            current_count = len(self._get_hotel_cards())
            if current_count > previous_count:
                return True
            time.sleep(0.5)

        return False

    def _apply_backoff(self, attempt: int) -> None:
        """
        Aplica exponential backoff entre intentos.

        Args:
            attempt: Número de intento actual (para calcular delay).
        """
        delay = settings.BACKOFF_FACTOR**attempt
        scraping_logger.debug(f"Aplicando backoff: {delay}s (intento {attempt})")
        time.sleep(delay)

    def _random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """
        Aplica un delay aleatorio para simular comportamiento humano.

        Args:
            min_seconds: Mínimo tiempo de espera.
            max_seconds: Máximo tiempo de espera.
        """
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def scrape(self) -> Generator[Hotel, None, None]:
        """
        Ejecuta el proceso de scraping completo.

        Itera sobre la página, manejando scroll infinito y paginación,
        yieldeando cada hotel a medida que se extrae.

        Yields:
            Objetos Hotel con la información extraída.
        """
        scraped_count = 0
        no_new_content_attempts = 0
        max_no_content_attempts = settings.MAX_RETRIES

        scraping_logger.info(f"Iniciando scraping de hasta {self.max_hotels} hoteles")
        self._handle_popups()

        while scraped_count < self.max_hotels:
            cards = self._get_hotel_cards()
            if not cards:
                scraping_logger.warning(
                    "No se encontraron hoteles disponibles según el criterio de búsqueda"
                )
                break
            previous_count = len(cards)

            # Procesar tarjetas actuales
            for card in cards:
                if scraped_count >= self.max_hotels:
                    break
                # sscraping_logger.info(f"{card}")
                hotel = self._parse_hotel_card(card)
                if hotel:
                    scraped_count += 1
                    scraping_logger.debug(
                        f"Hotel {scraped_count}/{self.max_hotels}: {hotel.nombre_hotel}"
                    )
                    yield hotel

            if scraped_count >= self.max_hotels:
                break

            # Intentar cargar más contenido
            scrolled = self._scroll_page()
            loaded_more = self._click_load_more()

            if scrolled or loaded_more:
                new_content = self._wait_for_new_content(previous_count)
                if new_content:
                    no_new_content_attempts = 0
                    continue

            # No se cargó contenido nuevo
            no_new_content_attempts += 1
            scraping_logger.debug(
                f"Sin contenido nuevo (intento {no_new_content_attempts}/{max_no_content_attempts})"
            )

            if no_new_content_attempts >= max_no_content_attempts:
                scraping_logger.info(
                    f"No hay más contenido disponible. Total extraído: {scraped_count}"
                )
                break

            self._apply_backoff(no_new_content_attempts)

        scraping_logger.info(f"Scraping finalizado. Total hoteles: {scraped_count}")

    def close(self) -> None:
        """
        Cierra el browser y libera recursos.

        Debe llamarse siempre al finalizar el scraping.
        """
        if self._page:
            self._page.close()
            self._page = None

        if self._context:
            self._context.close()
            self._context = None

        if self._browser:
            self._browser.close()
            self._browser = None

        if self._playwright:
            self._playwright.stop()
            self._playwright = None

        scraping_logger.info("Recursos del browser liberados")

    def __enter__(self) -> "BookingScraper":
        """
        Permite usar el scraper como context manager.

        Returns:
            La instancia del scraper con browser inicializado.
        """
        self._playwright = sync_playwright().start()
        self._browser = self._init_browser(self._playwright)
        self._context = self._create_context()
        self._navigate_to_search()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Cierra recursos al salir del context manager.
        """
        self.close()
