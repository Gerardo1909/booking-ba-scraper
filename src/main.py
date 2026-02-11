"""
Punto de entrada principal para ejecutar el flujo de scraping.

Proporciona una interfaz de usuario para configurar parámetros de búsqueda
y ejecutar el scraper.
"""

import os

from scraping.scraper import BookingScraper
from utils.input_validators import validate_dates
from utils.logger import scraping_logger
from writers.csv_writer import CSVWriter


def print_welcome():
    """Presenta el propósito del sistema al usuario."""
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 60)
    print("       🏨 BOOKING.COM SCRAPER 🏨")
    print("=" * 60)
    print("Este sistema extrae información detallada de hoteles en la")
    print("Ciudad de Buenos Aires directamente desde Booking.com.")
    print("\nPropósito: Facilitar la comparación de precios finales")
    print("(incluyendo impuestos) para estadías personalizadas.")
    print("-" * 60)
    print("📍 Ubicación fija: Buenos Aires, Argentina.")
    print("=" * 60)


def get_input(prompt: str, default: str) -> str:
    """Obtiene entrada del usuario con un valor por defecto."""
    user_input = input(f"{prompt} [{default}]: ").strip()
    return user_input if user_input else default


def interactive_loop():
    """Bucle principal de la consola interactiva."""
    print_welcome()

    while True:
        try:
            print("\n--- Configuración de nueva búsqueda ---")
            print("(Presione Ctrl+C en cualquier momento para salir)\n")

            checkin = get_input("Fecha de Check-in (YYYY-MM-DD)", "ej, 2026-03-01")
            checkout = get_input("Fecha de Check-out (YYYY-MM-DD)", "ej, 2026-03-05")

            # Parámetros de alojamiento
            max_h = int(get_input("Máximo de hoteles a buscar", "ej, 20"))
            adults = int(get_input("Cantidad de adultos", "ej, 2"))
            rooms = int(get_input("Cantidad de habitaciones", "ej, 1"))
            children = int(get_input("Cantidad de niños", "ej, 0"))

            print("\n🚀 Iniciando proceso...")

            run_scraping(
                max_hotels=max_h,
                checkin_date=checkin,
                checkout_date=checkout,
                group_adults=adults,
                rooms_number=rooms,
                group_children=children,
            )

            continuar = input("\n¿Desea realizar otra búsqueda? (s/n): ").lower()
            if continuar != "s":
                print("\nGracias por usar Booking Scraper. ¡Hasta luego!")
                break

        except ValueError:
            print(
                "\n❌ Error: Por favor ingrese valores numéricos válidos para cantidades."
            )
        except KeyboardInterrupt:
            print("\n\nSaliendo del programa...")
            break
        except Exception as e:
            print(f"\n❌ Ocurrió un error inesperado: {e}")
            scraping_logger.error(f"Error en loop principal: {e}")


def run_scraping(
    max_hotels: int,
    checkin_date: str,
    checkout_date: str,
    group_adults: int,
    rooms_number: int,
    group_children: int,
) -> None:
    """Ejecuta el pipeline de scraping con los parámetros recibidos."""
    try:
        # Validar fechas antes de iniciar
        checkin_date, checkout_date = validate_dates(checkin_date, checkout_date)

        scraping_logger.info("INICIANDO EXTRACCIÓN...")

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

        print("\n✅ ¡Búsqueda completada!")
        print(f"📊 Hoteles encontrados: {stats['total_written']}")
        print(f"📁 Archivo: {stats['output_dir']}")

    except Exception as e:
        print(f"\n⚠️ Error durante el scraping: {e}")


if __name__ == "__main__":
    interactive_loop()
