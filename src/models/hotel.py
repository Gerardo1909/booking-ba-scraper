"""
Módulo que contiene el modelo de datos que representa a un hotel obtenido.
"""

from pydantic import BaseModel, Field


class Hotel(BaseModel):
    """
    Modelo que representa la información extraída de un hotel en Booking.com.
    """

    nombre_hotel: str = Field(default="N/A", description="Nombre del establecimiento")
    ubicacion: str = Field(default="N/A", description="Localidad o barrio")
    checkin_date: str = Field(default="N/A", description="Fecha de entrada")
    checkout_date: str = Field(default="N/A", description="Fecha de salida")
    precio_inicial: str = Field(default="N/A", description="Precio inicial mostrado")
    precio_impuesto: str = Field(default="N/A", description="Impuestos")
    precio_final: str = Field(
        default="N/A", description="Precio final (suma inicial + impuestos si aplica)"
    )
    calificacion: str = Field(default="N/A", description="Categoría textual del rating")
    puntaje: str = Field(default="N/A", description="Score numérico")
    cantidad_reviews: str = Field(default="N/A", description="Cantidad de reviews")
    link_detalle: str = Field(default="N/A", description="URL al detalle del hotel")

    class Config:
        """Configuración del modelo Pydantic."""

        str_strip_whitespace = True
