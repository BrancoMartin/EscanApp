"""Bloqueo exclusivo para coordinar el mantenimiento de la base.

La aplicacion adquiere este lock al arrancar y lo mantiene mientras vive el
proceso. Restaurar un backup exige el mismo lock: si la app esta corriendo (o
hay otra restauracion en curso), el lock no se puede tomar y la restauracion se
rechaza en vez de reemplazar un archivo en uso.

Se apoya en el bloqueo del sistema operativo, no en la existencia de un archivo:
el SO libera el lock al terminar el proceso, incluso si la app se cierra de
golpe, asi que no quedan locks huerfanos que obliguen a borrar archivos a mano.
"""

import os
import sys

LOCK_FILENAME = ".escanapp.lock"


class DatabaseLockError(RuntimeError):
    """No se pudo obtener el bloqueo exclusivo de la base."""


def lock_path_for(db_path):
    """Lock junto a la base: misma carpeta de datos escribible."""
    directory = os.path.dirname(os.path.abspath(db_path))
    return os.path.join(directory, LOCK_FILENAME)


class DatabaseLock:
    """Lock de archivo exclusivo, opcionalmente no bloqueante."""

    def __init__(self, path):
        self.path = path
        self._handle = None

    def acquire(self, blocking=False):
        """Devuelve True si tomo el lock, False si ya lo tiene otro.

        Nunca lanza por contencion: el llamador decide si la ausencia de lock es
        un error (restaurar) o una condicion a informar.
        """
        if self._handle is not None:
            return True

        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        handle = open(self.path, "a+b")
        try:
            self._lock(handle, blocking)
        except OSError:
            handle.close()
            return False

        self._handle = handle
        return True

    def release(self):
        if self._handle is None:
            return
        handle = self._handle
        self._handle = None
        try:
            self._unlock(handle)
        finally:
            handle.close()

    def __enter__(self):
        if not self.acquire(blocking=False):
            raise DatabaseLockError(
                "No se pudo bloquear la base: hay otra operacion en curso."
            )
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False

    @staticmethod
    def _lock(handle, blocking):
        handle.seek(0)
        if sys.platform == "win32":
            import msvcrt

            mode = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
            msvcrt.locking(handle.fileno(), mode, 1)
        else:
            import fcntl

            flags = fcntl.LOCK_EX
            if not blocking:
                flags |= fcntl.LOCK_NB
            fcntl.flock(handle.fileno(), flags)

    @staticmethod
    def _unlock(handle):
        handle.seek(0)
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


_runtime_lock = None


def acquire_runtime_lock(db_path):
    """Toma y retiene el lock de la base durante toda la vida del proceso.

    Idempotente: si ya se tomo, devuelve el mismo lock. Se llama desde el
    arranque de la aplicacion, antes de aplicar migraciones.
    """
    global _runtime_lock

    if _runtime_lock is not None:
        return _runtime_lock

    lock = DatabaseLock(lock_path_for(db_path))
    if not lock.acquire(blocking=False):
        raise DatabaseLockError(
            "Otra instancia de EscanApp (o una restauracion) esta usando la base "
            "de datos en este momento. Cerra la otra ventana e intenta de nuevo."
        )

    _runtime_lock = lock
    return lock


def release_runtime_lock():
    """Libera el lock del proceso. Se usa en pruebas y en un cierre ordenado."""
    global _runtime_lock

    if _runtime_lock is None:
        return
    _runtime_lock.release()
    _runtime_lock = None
