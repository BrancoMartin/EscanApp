"""Restauracion de copias de seguridad desde la linea de comandos.

Uso (desde la raiz del repo, con el entorno virtual activo):

    python scripts/restore_backup.py --list
    python scripts/restore_backup.py --restore pos-backup-0001-20260102-100000.db
    python scripts/restore_backup.py --restore C:\\ruta\\a\\una\\copia.db

EscanApp tiene que estar CERRADA: la restauracion reemplaza la base activa y
toma el mismo lock que usa la aplicacion mientras esta abierta. Antes de
reemplazar nada se guarda una copia verificada de la base actual
(``pos-prerestore-*.db``), que es el camino de vuelta si algo falla.

Las copias viven en la carpeta de datos del usuario:
    %LOCALAPPDATA%\\EscanApp\\backups
"""

import argparse
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from Backend import database_backup, database_restore, runtime  # noqa: E402


def _print_backups(backups):
    if not backups:
        print(f"No hay copias de seguridad en: {runtime.backups_dir()}")
        return

    print(f"Copias de seguridad en: {runtime.backups_dir()}")
    for backup in backups:
        megabytes = backup["size_bytes"] / (1024 * 1024)
        print(
            f"  {backup['name']}  "
            f"{backup['created_at']}  {megabytes:.2f} MB  ({backup['kind']})"
        )


def _resolve(name_or_path):
    """Acepta un nombre dentro de backups/ o una ruta completa."""
    if os.path.isabs(name_or_path) or os.path.sep in name_or_path:
        return name_or_path
    return os.path.join(runtime.backups_dir(), name_or_path)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Lista y restaura copias de seguridad de la base de EscanApp."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--list", action="store_true", help="Muestra las copias disponibles."
    )
    group.add_argument(
        "--restore",
        metavar="ARCHIVO",
        help="Restaura la copia indicada (nombre dentro de backups/ o ruta completa).",
    )
    args = parser.parse_args(argv)

    if args.list:
        _print_backups(database_backup.list_backups())
        return 0

    backup_path = _resolve(args.restore)
    try:
        result = database_restore.restore_backup(backup_path)
    except database_restore.RestoreBlockedError as error:
        print(f"RESTAURACION BLOQUEADA: {error}")
        return 2
    except database_restore.RestoreError as error:
        print(f"NO SE RESTAURO NADA: {error}")
        return 1

    print("Restauracion completada.")
    print(f"  Copia usada: {result['restored_from']}")
    print(f"  Revision de esquema: {result['schema_revision']}")
    if result["safety_backup"]:
        print(f"  Base anterior guardada en: {result['safety_backup']}")
    print("Abri EscanApp: si la copia es de una version anterior, se migra al arrancar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
