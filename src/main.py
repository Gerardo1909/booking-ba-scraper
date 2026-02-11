"""
Punto de entrada principal para ejecutar el flujo de scraping.

Inicializa el scraper y el writer, valida parámetros y ejecuta
el pipeline de extracción de hoteles.
"""

from scraping.scraper import BookingScraper
from utils.input_validators import validate_dates
from utils.logger import scraping_logger
from writers.csv_writer import CSVWriter


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
        max_hotels=10,
        checkin_date="2026-02-13",
        checkout_date="2026-02-14",
        group_adults=2,
        rooms_number=1,
        group_children=0,
    )
