"""
Módulo que contiene funciones para validar entradas del usuario.
"""

from datetime import datetime


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
