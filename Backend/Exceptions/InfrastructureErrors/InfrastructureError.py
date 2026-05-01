class InfrastructureError(Exception):
    """Clase base para errores de infraestructura."""

    def __init__(self, message: str):
        super().__init__(message)

class DatabaseIntegrityError(InfrastructureError):
    """Violación de integridad (UNIQUE, FK, etc.)"""

    def __init__(self, message: str = "Database integrity error occurred."):
        super().__init__(message)

class DatabaseOperationalError(InfrastructureError):
    """DB caída, timeout, conexión"""
    def __init__(self, message: str = "Database operational error occurred."):
        super().__init__(message)

class DatabaseProgrammingError(InfrastructureError):
    """Error de query, columna inexistente, SQL mal"""
    def __init__(self, message: str = "Database programming error occurred."):
        super().__init__(message)