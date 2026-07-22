## 1. Detección determinística del código de barras

- [ ] 1.1 Helper `_barcode_en_mensaje(msg)`: devuelve la primera secuencia de 6+ dígitos, o None
- [ ] 1.2 Helper `_es_consulta_de_barcode(msg)`: hay barcode Y el mensaje no trae verbo de acción de gestión
- [ ] 1.3 Reemplazar el `^\d{6,}$` por la detección ampliada, conservando la prioridad del producto pendiente
- [ ] 1.4 Extraer la respuesta de escaneo a un helper (`_responder_barcode`) para no duplicarla

## 2. Red de seguridad: el asesor nunca ve un código de barras

- [ ] 2.1 En la rama `consulta_general`, antes de invocar `handle_general_query`: si el mensaje trae un barcode, resolverlo por base
- [ ] 2.2 Si el barcode no existe en la base, responder que no se encontró — nunca especular

## 3. Sin regresiones

- [ ] 3.1 Barcode pelado sigue igual (encontrado / no encontrado + arranca creación)
- [ ] 3.2 "creame el producto X con codigo 779…" sigue ruteando a `crear_productos`
- [ ] 3.3 El flujo de creación en curso sigue consumiendo el barcode
- [ ] 3.4 "aumentame un 10%" no se confunde con un barcode (menos de 6 dígitos)

## 4. Verificación

- [ ] 4.1 `python -m py_compile` de los archivos tocados
- [ ] 4.2 Test offline del enrutado (sin Ollama): casos con barcode pelado, con palabras, con verbo de acción, sin barcode
- [ ] 4.3 Reproducir el bug original contra el backend y confirmar que ya no responde el promedio
- [ ] 4.4 `openspec validate fix-agent-barcode-lookup`
