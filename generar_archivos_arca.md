# Documentación Técnica: `generar_archivos_arca.py`

Este documento describe el funcionamiento, arquitectura, reglas de negocio y modo de uso del script Python `generar_archivos_arca.py`, diseñado para procesar el padrón inmobiliario y generar los archivos estandarizados requeridos por **ARCA / AFIP** según las especificaciones del **Formulario F6500 (SETI Provincias)**.

---

## Tabla de Contenidos
1. [Descripción General](#descripción-general)
2. [Archivos de Referencia y Requisitos](#archivos-de-referencia-y-requisitos)
3. [Instalación y Requisitos del Entorno](#instalación-y-requisitos-del-entorno)
4. [Uso y Parámetros por Línea de Comandos](#uso-y-parámetros-por-línea-de-comandos)
5. [Estructura y Especificación de Archivos Generados](#estructura-y-especificación-de-archivos-generados)
   - [1. Rótulo Cabecera (31 posiciones)](#1-rótulo-cabecera-31-posiciones)
   - [2. Propiedades Titulares (344 posiciones)](#2-propiedades-titulares-344-posiciones)
6. [Reglas de Formateo y Mapeo de Datos](#reglas-de-formateo-y-mapeo-de-datos)
7. [Ejemplo de Ejecución](#ejemplo-de-ejecución)

---

## Descripción General

El script `generar_archivos_arca.py` toma como insumo un archivo CSV (`2025_arca.csv`) que contiene la información de catastros, valuaciones y titularidad de inmuebles de la provincia de Tierra del Fuego, y genera dos archivos de texto de ancho fijo codificados en `ISO-8859-1` (Latin-1) con salto de línea estándar Windows (`\r\n`):

1. **`ROTULO_CABECERA.txt`**: Archivo de control de cabecera (Tipo de Registro `01`) de **31 posiciones de ancho fijo**.
2. **`PROPIEDADES_TITULARES.txt`**: Archivo de detalle de inmuebles y cotitulares (Tipo de Registro `02`) de **344 posiciones de ancho fijo** por registro.

---

## Archivos de Referencia y Requisitos

La estructura de campos y reglas de formato cumplen estrictamente con los siguientes documentos normativos:
- **`ANEXO SETI PROVINCIAS.PDF`**: Especificaciones generales de validación, codificación `ISO-8859-1`, reglas de completitud y tablas de códigos anexas (1 a 14).
- **`F6500 DISENO SETI.XLS`**: Posicionamiento exacto (`Desde`, `Hasta`, `Cant.`), tipo de dato y descripción de campos para los registros de Tipo 01 (Rótulo Cabecera) y Tipo 02 (Propiedades Titulares).
- **`2025_arca.csv`**: Origen de datos primario.

---

## Instalación y Requisitos del Entorno

El script está desarrollado en **Python 3.8+** y utiliza las siguientes librerías estándar y de procesamiento de datos:

```bash
pip install pandas numpy
```

---

## Uso y Parámetros por Línea de Comandos

### Sintaxis Básica:
```bash
python generar_archivos_arca.py [OPCIONES]
```

### Opciones Disponibles:

| Parámetro | Descripción | Valor por Defecto |
|---|---|---|
| `--csv` | Ruta al archivo CSV de origen | `2025_arca.csv` |
| `--out-dir` | Directorio de destino para los archivos planos | `..\titularesARCA` |
| `--year` | Año de corte de la información (formato AAAA) | `2025` |
| `--out-cabecera` | Nombre del archivo de Rótulo Cabecera | `ROTULO_CABECERA.txt` |
| `--out-titulares` | Nombre del archivo de Propiedades Titulares | `PROPIEDADES_TITULARES.txt` |

### Ejemplos de Uso:

#### 1. Ejecución estándar con valores por defecto:
```bash
python generar_archivos_arca.py
```

#### 2. Especificando rutas de entrada/salida y año de corte personalizado:
```bash
python generar_archivos_arca.py --csv "./datos_2026.csv" --out-dir "./salida" --year 2026
```

---

## Estructura y Especificación de Archivos Generados

### 1. Rótulo Cabecera (31 posiciones)

Archivo único por envío que valida el número total de registros de detalle.

| Campo | Posiciones | Cantidad | Tipo | Descripción / Valor |
|---|---|---|---|---|
| Tipo de Registro | 1 - 2 | 2 | Numérico | Fijo `"01"` |
| Código de Provincia | 3 - 4 | 2 | Numérico | Fijo `"24"` (Tierra del Fuego) |
| Corte de Información | 5 - 8 | 4 | Numérico | Año en formato `AAAA` (ej. `"2025"`) |
| Secuencia | 9 - 10 | 2 | Numérico | `"00"` (Original) |
| Cantidad de Registros | 11 - 22 | 12 | Numérico | Cantidad total de registros de Tipo 02 (relleno ceros izq) |
| Número de Formulario | 23 - 26 | 4 | Numérico | Fijo `"6500"` |
| Versión Formulario | 27 - 31 | 5 | Numérico | Fijo `"00100"` |

---

### 2. Propiedades Titulares (344 posiciones)

Se incluye 1 registro por cada titular poseedor del inmueble.

| N° | Posición | Cant. | Tipo | Campo | Regla / Mapeo desde CSV |
|---|---|---|---|---|---|
| 1 | 1 - 2 | 2 | Num (2) | Tipo de Registro | Fijo `"02"` |
| 2 | 3 - 52 | 50 | AlfaNum (3) | Razón Social / Apellido y Nombre | Columna `Titular`. Izq, max 50 chars, espacio-padded |
| 3 | 53 - 63 | 11 | Num (2) | CUIT, CUIL, CDI | DNI/CUIL/CUIT de 11 dígitos si aplica, sino `"00000000000"` |
| 4 | 64 - 65 | 2 | Num (2) | Tipo de Documento | DNI/MI=`96`, LE=`90`, LC=`89`, CI=`24`, CUIT=`80`, CUIL=`86`, CDI=`87`, Otro=`00` |
| 5 | 66 - 76 | 11 | Num (2) | Número de Documento | Columna `Nro Documento`. Numérico 11 dígitos ceros izq |
| 6 | 77 - 81 | 5 | Num (2) | Porcentaje de Titularidad | `9(3)v99`. Columna `Dominio` (ej. 100,0 -> `"10000"`, 50,0 -> `"05000"`) |
| 7 | 82 - 82 | 1 | Alfa (1) | Marca Tipo Domicilio | Fijo `"I"` (Inmueble) |
| 8 | 83 - 112 | 30 | AlfaNum (3) | Domicilio - Calle | Fijo `"SIN CALLE"` o alineado izq espacio-padded |
| 9 | 113 - 118 | 6 | AlfaNum (3) | Domicilio - Número/Km. | Fijo `"S/N"` o alineado izq espacio-padded |
| 10 | 119 - 123 | 5 | AlfaNum (3) | Domicilio - Sector | 5 espacios en blanco (Opcional) |
| 11 | 124 - 128 | 5 | AlfaNum (3) | Domicilio - Torre | 5 espacios en blanco (Opcional) |
| 12 | 129 - 133 | 5 | AlfaNum (3) | Domicilio - Piso | 5 espacios en blanco (Opcional) |
| 13 | 134 - 138 | 5 | AlfaNum (3) | Domicilio - Dto/Ofic/Local | 5 espacios en blanco (Opcional) |
| 14 | 139 - 143 | 5 | AlfaNum (3) | Domicilio - Manzana | 5 espacios en blanco (Opcional) |
| 15 | 144 - 168 | 25 | AlfaNum (3) | Domicilio - Barrio | 25 espacios en blanco (Opcional) |
| 16 | 169 - 198 | 30 | AlfaNum (3) | Localidad | Columna `Departamento` ('Rio Grande', 'Tolhuin', 'Ushuaia') |
| 17 | 199 - 206 | 8 | AlfaNum (3) | Código Postal | CPA (8 pos): Rio Grande -> `"V9420   "`, Ushuaia -> `"V9410   "`, Tolhuin -> `"V9405   "` |
| 18 | 207 - 208 | 2 | Num (2) | Código de Provincia | Fijo `"24"` (Tierra del Fuego) |
| 19 | 209 - 209 | 1 | Alfa (1) | Zona del Inmueble | Columna `Padron`: 'Urbano' -> `"U"`, 'Rural' -> `"R"` |
| 20 | 210 - 269 | 60 | AlfaNum (3) | Nomenclatura Catastral | Nomenclatura unívoca por inmueble (ej. `DEP:RG-PAR:18014-SEC:A-MAC:1-PARC:1a`) |
| 21 | 270 - 299 | 30 | AlfaNum (3) | Matrícula del Inmueble | Columna `Instrumento` / `Tipo de Instrumento` recortado a 30 pos |
| 22 | 300 - 312 | 13 | Num (2) | Valuación Fiscal | `9(11)v99`. 100% de valuación fiscal (`Valor Total` * 100, 13 dígitos ceros izq) |
| 23 | 313 - 325 | 13 | Num (2) | Base Imponible | `9(11)v99`. 100% de base imponible (`Valor Total` * 100, 13 dígitos ceros izq) |
| 24 | 326 - 327 | 2 | Num (2) | Tipo de Inmueble | 01=Casa, 02=Depto, 06=Lote, 08=Mejoras, 09=Rural c/viv, 10=Rural s/viv, 99=Otros |
| 25 | 328 - 340 | 13 | Num (2) | Superficie | `9(11)v99`. Superficie * 100 (`Superficie UF/UC` si > 0, sino `Superficie`) |
| 26 | 341 - 341 | 1 | Num (2) | Unidad de Medida | `1`=Metro cuadrado (m2), `4`=Hectárea (Ha) |
| 27 | 342 - 344 | 3 | Num (2) | Cantidad de Titulares | Conteo total de titulares para la misma Nomenclatura Catastral (3 dígitos ceros izq) |

---

## Reglas de Formateo y Mapeo de Datos

1. **Tipos de Datos y Alineación**:
   - **Tipo 1 (Alfabético)** / **Tipo 3 (Alfanumérico)**: Alineados a la izquierda, se completan con espacios en blanco a la derecha hasta alcanzar la longitud especificada.
   - **Tipo 2 (Numérico)**: Rellenos con ceros a la izquierda. Los valores ausentes o nulos sin validación obligatoria se completan totalmente con ceros (`"00...0"`).
2. **Campos con Decimales Implicados (`v99`)**:
   - Los campos como Valuación Fiscal, Base Imponible y Superficie no llevan comas ni puntos decimales. Se multiplican por 100 y se representan como enteros de 13 dígitos (`9(11)v99`).
   - El Porcentaje de Titularidad se multiplica por 100 y se representa como entero de 5 dígitos (`9(3)v99`). Ejemplo: `100,0%` -> `10000`, `50,0%` -> `05000`.
3. **Nomenclatura Catastral y Cotitularidad**:
   - La Nomenclatura Catastral se genera dinámicamente combinando el departamento y las parcelas/macizos/secciones/partidas para asegurar la unificación de cotitulares.
   - La `Cantidad de Titulares` (Campo 27) se calcula automáticamente agrupando por la Nomenclatura Catastral generada, garantizando que si un inmueble posee N cotitulares, los N registros tengan asignado el valor N.

---

## Ejemplo de Ejecución

Al ejecutar el script desde la consola:

```powershell
python generar_archivos_arca.py
```

### Salida esperada en consola:
```text
Cargando dataset desde: 2025_arca.csv
Total de registros a procesar: 58490
Escribiendo Rótulo Cabecera en: ROTULO_CABECERA.txt
Escribiendo Propiedades Titulares en: PROPIEDADES_TITULARES.txt

==================================================
PROCESO COMPLETADO EXITOSAMENTE!
- Archivo Cabecera: ROTULO_CABECERA.txt (1 registro, 31 pos)
- Archivo Titulares: PROPIEDADES_TITULARES.txt (58490 registros, 344 pos c/u)
==================================================
```
