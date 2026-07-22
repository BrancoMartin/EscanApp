## 1. Semilla determinística de marcas

- [x] 1.1 Constante `MARCAS_CONOCIDAS`: lista de marcas canónicas + índice normalizado (lower, sin acentos) → forma canónica
- [x] 1.2 Helper `_detectar_marcas(nombre, descripcion)`: devuelve las marcas canónicas que aparecen como palabra completa
- [x] 1.3 Inyectar el/los atributo(s) `marca` en `attribute_extractor` tras la salida del modelo, sin duplicar si el modelo ya lo trajo, respetando `MAX_ATRIBUTOS` (la marca va primero para que no se caiga en el recorte)

## 2. Garantía dura contra valores nulos

- [x] 2.1 Normalizar valor y comparar contra `SINONIMOS_NULL` también para los atributos de semilla
- [x] 2.2 Filtro final: descartar cualquier atributo con valor vacío/sinónimo antes de retornar (`_valor_es_nulo`)

## 3. Prompt del Modelfile

- [x] 3.1 Actualizar `SYSTEM` de `Modelfiles/AttributeExtractor`: guía adjetivo vs. sustantivo propio + que un sustantivo propio suelto es candidato a marca
- [x] 3.2 Documentar el rebuild (`ollama create attribute-extractor -f Modelfiles/AttributeExtractor`)
- [ ] 3.3 **PENDIENTE (requiere Ollama en la máquina):** ejecutar el rebuild del tag para que el nuevo prompt tenga efecto

## 4. Verificación

- [x] 4.1 `python -m py_compile Backend/agent/model_attribute_extractor.py`
- [x] 4.2 Test offline de `_detectar_marcas` y del filtro de nulos (sin Ollama): marca en nombre, marca en descripción, marca con acento, valor "none", subcadena que no matchea
- [x] 4.3 `openspec validate agent-brand-attribute-detection` (válido)
