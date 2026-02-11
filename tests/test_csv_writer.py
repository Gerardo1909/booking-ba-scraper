"""
Tests unitarios para el módulo CSVWriter.
"""

import csv

import pytest
import pytest_check as check

from models.hotel import Hotel
from writers.csv_writer import CSVWriter


@pytest.fixture
def sample_hotels():
    """Fixture que retorna una lista de hoteles de prueba."""
    return [
        Hotel(
            nombre_hotel="Hotel Test 1",
            ubicacion="Palermo",
            checkin_date="2025-03-01",
            checkout_date="2025-03-02",
            precio_inicial="100.0",
            precio_impuesto="20.0",
            precio_final="120.0",
            calificacion="Wonderful",
            puntaje="9.1",
            cantidad_reviews="100 reviews",
            link_detalle="https://booking.com/hotel1",
        ),
        Hotel(
            nombre_hotel="Hotel Test 2",
            ubicacion="Recoleta",
            checkin_date="2025-03-01",
            checkout_date="2025-03-02",
            precio_inicial="200.0",
            precio_impuesto="40.0",
            precio_final="240.0",
            calificacion="Very Good",
            puntaje="8.5",
            cantidad_reviews="50 reviews",
            link_detalle="https://booking.com/hotel2",
        ),
    ]


@pytest.fixture
def temp_output_dir(tmp_path):
    """Fixture que retorna un directorio temporal para outputs."""
    return tmp_path / "test_output"


def test_get_next_filename_should_increment_counter_and_format_correctly_when_called():
    """Verifica que los nombres de archivo se generen con formato y contador correctos."""
    writer = CSVWriter()

    filename1 = writer._get_next_filename()
    filename2 = writer._get_next_filename()
    filename3 = writer._get_next_filename()

    check.equal(filename1.name, "booking_hotels_001.csv")
    check.equal(filename2.name, "booking_hotels_002.csv")
    check.equal(filename3.name, "booking_hotels_003.csv")
    check.equal(writer._file_counter, 3)


def test_write_batch_should_create_csv_file_with_headers_when_buffer_has_data(
    sample_hotels, temp_output_dir
):
    """Verifica que se escriba un archivo CSV con headers cuando hay datos en el buffer."""
    writer = CSVWriter()
    writer.output_dir = temp_output_dir
    writer.output_dir.mkdir(parents=True, exist_ok=True)
    writer._buffer = sample_hotels[:1]

    writer._write_batch()

    filepath = temp_output_dir / "booking_hotels_001.csv"
    check.is_true(filepath.exists())

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        check.equal(len(rows), 1)
        check.equal(rows[0]["nombre_hotel"], "Hotel Test 1")
        check.equal(rows[0]["precio_final"], "120.0")

    check.equal(len(writer._buffer), 0)
    check.equal(writer._total_written, 1)


def test_write_batch_should_not_create_file_when_buffer_is_empty(temp_output_dir):
    """Verifica que no se cree ningún archivo cuando el buffer está vacío."""
    writer = CSVWriter()
    writer.output_dir = temp_output_dir
    writer.output_dir.mkdir(parents=True, exist_ok=True)

    writer._write_batch()

    csv_files = list(writer.output_dir.glob("*.csv"))
    check.equal(len(csv_files), 0)
    check.equal(writer._file_counter, 0)


def test_write_from_generator_should_write_multiple_batches_when_exceeds_batch_size(
    sample_hotels, temp_output_dir
):
    """Verifica que se escriban múltiples archivos cuando se excede el tamaño del batch."""
    writer = CSVWriter()
    writer.output_dir = temp_output_dir
    writer.output_dir.mkdir(parents=True, exist_ok=True)
    writer.batch_size = 1

    def hotel_generator():
        for hotel in sample_hotels:
            yield hotel

    total = writer.write_from_generator(hotel_generator())

    check.equal(total, 2)
    check.equal(writer._file_counter, 2)

    csv_files = sorted(writer.output_dir.glob("*.csv"))
    check.equal(len(csv_files), 2)


def test_flush_should_write_remaining_hotels_when_buffer_not_empty(
    sample_hotels, temp_output_dir
):
    """Verifica que flush escriba los hoteles restantes del buffer."""
    writer = CSVWriter()
    writer.output_dir = temp_output_dir
    writer.output_dir.mkdir(parents=True, exist_ok=True)
    writer._buffer = sample_hotels[:1]

    writer.flush()

    check.equal(len(writer._buffer), 0)
    check.equal(writer._total_written, 1)

    csv_files = list(writer.output_dir.glob("*.csv"))
    check.equal(len(csv_files), 1)


def test_get_stats_should_return_correct_metrics_when_called(
    sample_hotels, temp_output_dir
):
    """Verifica que get_stats retorne métricas correctas después de escribir."""
    writer = CSVWriter()
    writer.output_dir = temp_output_dir
    writer.output_dir.mkdir(parents=True, exist_ok=True)
    writer.batch_size = 2

    def hotel_generator():
        for hotel in sample_hotels:
            yield hotel

    writer.write_from_generator(hotel_generator())
    stats = writer.get_stats()

    check.equal(stats["total_written"], 2)
    check.equal(stats["files_created"], 1)
    check.is_true("test_output" in stats["output_dir"])


def test_context_manager_should_flush_on_exit_when_buffer_has_data(
    sample_hotels, temp_output_dir
):
    """Verifica que el context manager ejecute flush automáticamente al salir."""
    with CSVWriter() as writer:
        writer.output_dir = temp_output_dir
        writer.output_dir.mkdir(parents=True, exist_ok=True)
        writer._buffer = sample_hotels[:1]

    check.equal(len(writer._buffer), 0)
    check.equal(writer._total_written, 1)
