"""
Módulo para escritura incremental de hoteles en archivos CSV.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterator, List

from config.settings import settings
from models.hotel import Hotel
from utils.logger import scraping_logger


class CSVWriter:
    """
    Escritor de archivos CSV con soporte para escritura incremental por batches.
    """

    FIELDNAMES = [
        "nombre_hotel",
        "ubicacion",
        "checkin_date",
        "checkout_date",
        "precio_inicial",
        "precio_impuesto",
        "precio_final",
        "calificacion",
        "puntaje",
        "cantidad_reviews",
        "link_detalle",
    ]

    def __init__(self) -> None:
        """
        Inicializa el writer con configuración de batches y directorio de salida.
        """
        self.batch_size = settings.BATCH_SIZE
        self.output_dir = self._create_output_dir()
        self._buffer: List[Hotel] = []
        self._file_counter: int = 0
        self._total_written: int = 0

        scraping_logger.info(
            f"CSVWriter inicializado: batch_size={self.batch_size}, "
            f"output_dir={self.output_dir}"
        )

    def _create_output_dir(self) -> Path:
        """
        Crea el directorio de salida con timestamp.

        Returns:
            Path al directorio creado.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = settings.DATA_DIR / f"ingestion_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _get_next_filename(self) -> Path:
        """
        Genera el nombre del siguiente archivo CSV.

        Returns:
            Path al siguiente archivo.
        """
        self._file_counter += 1
        filename = f"booking_hotels_{self._file_counter:03d}.csv"
        return self.output_dir / filename

    def _write_batch(self) -> None:
        """
        Escribe el buffer actual a un archivo CSV y lo vacía.
        """
        if not self._buffer:
            return

        filepath = self._get_next_filename()
        scraping_logger.info(
            f"Escribiendo batch {self._file_counter}: {len(self._buffer)} hoteles -> {filepath.name}"
        )

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            writer.writeheader()

            for hotel in self._buffer:
                writer.writerow(hotel.model_dump())

        self._total_written += len(self._buffer)
        self._buffer.clear()

    def add_hotel(self, hotel: Hotel) -> None:
        """
        Agrega un hotel al buffer. Si el buffer alcanza el batch_size, escribe a disco.

        Args:
            hotel: Hotel a agregar.
        """
        self._buffer.append(hotel)

        if len(self._buffer) >= self.batch_size:
            self._write_batch()

    def write_from_generator(self, hotels: Iterator[Hotel]) -> int:
        """
        Consume un generador de hoteles y los escribe en batches.

        Args:
            hotels: Iterador de objetos Hotel.

        Returns:
            Total de hoteles escritos.
        """
        for hotel in hotels:
            self.add_hotel(hotel)

        # Escribir hoteles restantes en el buffer
        self.flush()

        return self._total_written

    def flush(self) -> None:
        """
        Fuerza la escritura de cualquier hotel pendiente en el buffer.
        """
        if self._buffer:
            self._write_batch()

    def get_stats(self) -> dict:
        """
        Retorna estadísticas de escritura.

        Returns:
            Diccionario con total_written, files_created, output_dir.
        """
        return {
            "total_written": self._total_written,
            "files_created": self._file_counter,
            "output_dir": str(self.output_dir),
        }

    def __enter__(self) -> "CSVWriter":
        """
        Permite usar el writer como context manager.

        Returns:
            La instancia del writer.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Asegura que se escriban los hoteles pendientes al salir del context.
        """
        self.flush()
        stats = self.get_stats()
        scraping_logger.info(
            f"CSVWriter finalizado: {stats['total_written']} hoteles en "
            f"{stats['files_created']} archivos"
        )
