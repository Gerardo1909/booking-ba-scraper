"""
Punto de entrada principal para ejecutar el flujo de scraping.

Inicializa el scraper y el writer, valida parámetros y ejecuta
el pipeline de extracción de hoteles.
"""

from datetime import datetime

from scraping.scraper import BookingScraper
from utils.logger import scraping_logger
from writers.csv_writer import CSVWriter


def validate_date(date_str: str, field_name: str) -> str:
    """
    Valida que una fecha tenga formato YYYY-MM-DD.

    Args:
        date_str: Fecha en formato string.
        field_name: Nombre del campo para mensajes de error.

    Returns:
        La fecha validada.

    Raises:
        ValueError: Si el formato es inválido.
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise ValueError(
            f"{field_name} debe tener formato YYYY-MM-DD. Recibido: {date_str}"
        )


def validate_dates(checkin: str, checkout: str) -> tuple[str, str]:
    """
    Valida las fechas de check-in y check-out.

    Args:
        checkin: Fecha de check-in.
        checkout: Fecha de check-out.

    Returns:
        Tupla con las fechas validadas.

    Raises:
        ValueError: Si las fechas son inválidas o checkout <= checkin.
    """
    checkin = validate_date(checkin, "checkin_date")
    checkout = validate_date(checkout, "checkout_date")

    checkin_dt = datetime.strptime(checkin, "%Y-%m-%d")
    checkout_dt = datetime.strptime(checkout, "%Y-%m-%d")

    if checkout_dt <= checkin_dt:
        raise ValueError("checkout_date debe ser posterior a checkin_date")

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if checkin_dt < today:
        raise ValueError("checkin_date no puede ser una fecha pasada")

    return checkin, checkout


def run_scraping(
    max_hotels: int,
    checkin_date: str,
    checkout_date: str,
    group_adults: int = 2,
    rooms_number: int = 1,
    group_children: int = 0,
) -> None:
    """
    Ejecuta el pipeline completo de scraping y guardado.

    Args:
        max_hotels: Número máximo de hoteles a extraer.
        checkin_date: Fecha de check-in (YYYY-MM-DD).
        checkout_date: Fecha de check-out (YYYY-MM-DD).
        group_adults: Número de adultos.
        rooms_number: Número de habitaciones.
        group_children: Número de niños.
    """
    # Validar fechas
    checkin_date, checkout_date = validate_dates(checkin_date, checkout_date)

    scraping_logger.info("=" * 50)
    scraping_logger.info("INICIANDO PIPELINE DE SCRAPING")
    scraping_logger.info("=" * 50)
    scraping_logger.info("Parámetros:")
    scraping_logger.info(f"  - Max hoteles: {max_hotels}")
    scraping_logger.info(f"  - Check-in: {checkin_date}")
    scraping_logger.info(f"  - Check-out: {checkout_date}")
    scraping_logger.info(f"  - Adultos: {group_adults}")
    scraping_logger.info(f"  - Habitaciones: {rooms_number}")
    scraping_logger.info(f"  - Niños: {group_children}")

    with CSVWriter() as writer:
        with BookingScraper(
            max_hotels=max_hotels,
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            group_adults=group_adults,
            rooms_number=rooms_number,
            group_children=group_children,
        ) as scraper:
            writer.write_from_generator(scraper.scrape())

        stats = writer.get_stats()

    scraping_logger.info("=" * 50)
    scraping_logger.info("PIPELINE FINALIZADO")
    scraping_logger.info(f"  - Total hoteles escritos: {stats['total_written']}")
    scraping_logger.info(f"  - Archivos generados: {stats['files_created']}")
    scraping_logger.info(f"  - Directorio de salida: {stats['output_dir']}")
    scraping_logger.info("=" * 50)


if __name__ == "__main__":
    run_scraping(
        max_hotels=120,
        checkin_date="2026-02-13",
        checkout_date="2026-02-14",
        group_adults=2,
        rooms_number=1,
        group_children=0,
    )
