## 1. Servicio de enriquecimiento (capa correcta, una sola implementación)

- [ ] 1.1 Crear `Backend/services/product_enrichment_service.py` con los helpers de texto (`normalizar`, `raiz`, `match_productos_por_valor`, `is_valid_str`, `NULL_SYNONYMS`, `MAX_CATEGORIAS_PROMPT`)
- [ ] 1.2 Mover `_asignar_atributos_existentes` → `asignar_atributos_existentes` (determinístico, sin modelo)
- [ ] 1.3 Mover `_enriquecer_producto_con_atributos` → `enriquecer_producto` (1 modelo; `create_categories` solo como fallback)
- [ ] 1.4 `controller_agent.py` importa del servicio con alias, sin tocar los ~100 puntos de uso existentes
- [ ] 1.5 Sin `isinstance()` (regla del proyecto)

## 2. POST /api/products/ — responder sin esperar a la IA

- [ ] 2.1 Responder apenas el producto está persistido
- [ ] 2.2 Disparar `enriquecer_producto` en un hilo daemon con su propia sesión de base
- [ ] 2.3 El hilo cierra su sesión siempre y traga sus errores (el alta ya respondió)
- [ ] 2.4 Borrar del controlador la copia con dos modelos (`create_categories` + `attribute_extractor` en serie)
- [ ] 2.5 No disparar enriquecimiento cuando el alta falla (barcode duplicado, precio inválido)

## 2b. El proveedor que escribió el usuario es la verdad

- [ ] 2b.1 `attribute_extractor`: sobrescribir con el literal del usuario el valor de proveedor que emita el modelo (antes solo se completaba si el modelo lo omitía)
- [ ] 2b.2 Verificar que altas sucesivas con el mismo proveedor comparten un único atributo

## 3. Frontend — alta de producto

- [ ] 3.1 Detección lector/manual en el campo de código de barras (umbral 50 ms, mismo criterio que la pantalla de escaneo)
- [ ] 3.2 Indicador discreto "Escaneado" / "Ingresado a mano" junto al campo
- [ ] 3.3 Reinicio de la detección cuando el campo queda vacío
- [ ] 3.4 NO auto-enviar el formulario al detectar el lector (faltan nombre y precio)
- [ ] 3.5 Limpiar el campo proveedor al crear (hoy queda con el valor anterior)
- [ ] 3.6 Estado de envío en el botón, para que el click no parezca perdido

## 4. Verificación

- [ ] 4.1 `python -m py_compile` de los archivos Python tocados
- [ ] 4.2 Test offline del servicio de enriquecimiento (sin Ollama): atributos existentes se asignan sin modelo
- [ ] 4.3 Medir el POST end-to-end contra una copia de `pos.db`: antes ~13 s → objetivo < 0.5 s
- [ ] 4.4 Verificar que el enriquecimiento efectivamente ocurre después (atributos asignados unos segundos más tarde)
- [ ] 4.5 Verificar que el agente sigue creando productos igual (no se rompió al mover los helpers)
- [ ] 4.6 `npm run build` del frontend sin errores
- [ ] 4.7 `openspec validate fast-product-creation`
