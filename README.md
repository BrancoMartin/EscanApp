# EscanApp

Sistema de venta con escaneo de codigo de barras, 
desarrollado para pequeños comercios. 
Permite gestionar productos, registrar ventas y generar tickets de forma fácil y rapida.


## FUNCIONALIDADES:
**Gestion de productos** : El usuario carga manualmente sus productos mediante un formulario, escaneando su codigo de barras
para guardarlo en la base de datos.

**Escaneo en caja**: Al atender a un cliente el usuario escanea los productos, y se genera un ticket en tiempo 
real con el detalle de la compra.

**Cierre de venta**: El usuario cierra la venta mediante un boton "cerrar venta" y esta queda guardada en la base de datos como closed.

**Historial de ventas**: Se pueden consultar las ventas realizadas en las ultimas 24 horas. Las ventas anteriores a las 24 horas no se muestran.

## TECNOLOGIAS UTILIZADAS: 

**Frontend**: React + Vite

**Backend**: Fast API (python)

**Base de datos**: SQLite

**ORM**: SQLAlchemy

**Escritorio**: pywebview

**Empaquetado**: PyInstaller

## INSTALACION Y USO (Clientes)

Descargá el archivo .zip de la sección Releases
Descomprimí el archivo
Hacé doble clic en POS.exe
