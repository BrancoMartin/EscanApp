## ADDED Requirements

### Requirement: Semilla determinística de marcas conocidas

El sistema SHALL mantener una lista de marcas conocidas del rubro (kiosco/almacén argentino) que incluye al menos: Mondelez, Arcor, Terrabusi, Milka, Felfort, Georgalos, Bagley, Guaymallén, Jorgito, Ferrero, Nestlé, Mars Wrigley, Lheritier, Billiken, Tofi.

Si alguna de esas marcas aparece como palabra completa (sin distinción de mayúsculas/minúsculas ni acentos) en el `nombre` o la `descripcion` del producto, el sistema SHALL emitir determinísticamente un atributo `{"categoria": "marca", "valor": <marca canónica>}` y asociarlo al producto, SIN depender de la salida del modelo `AttributeExtractor`. El valor SHALL normalizarse a la forma canónica de la lista (misma marca → mismo valor siempre).

Esta detección SHALL correr sin invocar ningún modelo y NO SHALL agregar latencia al request.

#### Scenario: Marca conocida en el nombre

- **WHEN** se crea un producto cuyo nombre o descripción contiene una marca de la lista (ej. "Chocolate Milka relleno")
- **THEN** el sistema crea (o reutiliza) la categoría `marca`
- **AND** asigna al producto el atributo `marca = "Milka"` con la forma canónica de la lista
- **AND** lo hace aunque el modelo `AttributeExtractor` no la haya devuelto

#### Scenario: Misma marca escrita distinto

- **WHEN** dos productos mencionan la misma marca con distinta capitalización o acentuación (ej. "guaymallen" y "Guaymallén")
- **THEN** ambos reciben el atributo `marca` con el MISMO valor canónico
- **AND** un ajuste de precio por ese atributo agrupa a los dos

#### Scenario: Marca desconocida no forzada

- **WHEN** el nombre/descripción no contiene ninguna marca de la lista
- **THEN** la semilla determinística NO agrega ningún atributo `marca`
- **AND** la detección de marca queda a cargo del modelo (que puede o no proponerla)

### Requirement: Garantía dura contra atributos con valor nulo

La capa determinística del `AttributeExtractor` SHALL garantizar que ningún atributo retornado —venga del modelo o de una semilla— tenga `valor` vacío o sinónimo de nulo (`null`, `none`, `nada`, `ninguno`, `ninguna`, `n/a`, `-`, `desconocido`, etc.). Un atributo que no cumpla SHALL descartarse antes de retornar, nunca persistirse.

#### Scenario: Modelo devuelve valor nulo

- **WHEN** el modelo devuelve un atributo con `valor` igual a "none", "ninguno", vacío o similar
- **THEN** el sistema descarta ese atributo y NO lo asocia al producto

## MODIFIED Requirements

### Requirement: Extracción de atributos por IA

El sistema SHALL extraer atributos (categoría + valor) del nombre y descripción de un producto usando el modelo attribute_extractor.

El `AttributeExtractor` SHALL distinguir entre un adjetivo descriptivo (característica del producto: sabor, material, tamaño) y un sustantivo propio suelto (candidato a marca). Un sustantivo propio capitalizado que no sea un adjetivo descriptivo SHALL tratarse como `marca`; un adjetivo descriptivo SHALL tratarse como atributo de característica (`tipo`, `material`, `sabor`, …), NO como marca. La salida del modelo SHALL complementarse con la semilla determinística de marcas conocidas y con la garantía dura contra valores nulos.

#### Scenario: Extracción al crear producto

- **WHEN** se crea un producto desde el chat
- **THEN** el sistema invoca attribute_extractor para inferir atributos
- **AND** aplica la semilla determinística de marcas conocidas sobre nombre y descripción
- **AND** descarta cualquier atributo con valor nulo o sinónimo de nulo
- **AND** crea categorías y atributos faltantes
- **AND** asocia los atributos al producto

#### Scenario: Adjetivo no es marca

- **WHEN** la descripción trae un adjetivo descriptivo (ej. "chocolatado", "grande")
- **THEN** el sistema NO lo clasifica como `marca`
- **AND** puede clasificarlo como característica (`tipo`, `sabor`, …) o descartarlo
