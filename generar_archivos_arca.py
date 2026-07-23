#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar los archivos estandarizados ARCA SETI F6500:
1. ROTULO CABECERA (31 caracteres de ancho fijo)
2. PROPIEDADES TITULARES (344 caracteres de ancho fijo)

Fuente de datos: 2025_arca.csv
Normativa: ANEXO SETI PROVINCIAS.PDF y F6500 DISENO SETI.XLS
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd

# Default paths
DEFAULT_CSV = r"2025_arca.csv"
DEFAULT_OUT_DIR = r"."
DEFAULT_YEAR = 2025
DEFAULT_CUIT = "30672049379"


def pad_alpha(val, length):
    """
    Formatea un valor alfanumérico (Tipo 3):
    Alineado a la izquierda, relleno con espacios a la derecha, recortado a 'length'.
    """
    if pd.isna(val) or val is None:
        s = ""
    else:
        s = str(val).strip()
    return s[:length].ljust(length)


def pad_num(val, length):
    """
    Formatea un valor numérico entero (Tipo 2):
    Alineado a la derecha, relleno con ceros a la izquierda, recortado a 'length'.
    """
    if pd.isna(val) or val is None:
        s = ""
    else:
        # Extraer dígitos
        s = str(val).strip()
        # Si tiene punto flotante decimal tipo '18014.0', convertir a entero
        if s.endswith('.0'):
            s = s[:-2]
        s = "".join(filter(str.isdigit, s))
    if not s:
        s = "0"
    return s[-length:].zfill(length)


def parse_money_cents(val):
    """
    Convierte montos monetarios o valores en formato string o numérico
    a un valor entero de centavos (9(11)v99 -> 13 dígitos numéricos).
    Ejemplo: '$791.896,66' -> 79189666 -> '0000079189666'
    """
    if pd.isna(val) or val is None:
        return 0
    s = str(val).replace('$', '').replace('.', '').replace(',', '.').strip()
    try:
        f = float(s)
        return int(round(f * 100))
    except ValueError:
        return 0


def parse_surface_cents(val):
    """
    Convierte superficies a entero con 2 decimales implícitos (9(11)v99 -> 13 dígitos).
    Ejemplo: '15.459,30' -> 1545930 -> '0000001545930'
    """
    if pd.isna(val) or val is None:
        return 0
    s = str(val).replace('.', '').replace(',', '.').strip()
    try:
        f = float(s)
        return int(round(f * 100))
    except ValueError:
        return 0


def parse_dominio_cents(val):
    """
    Convierte porcentaje de dominio a entero con 2 decimales implícitos (9(3)v99 -> 5 dígitos).
    Ejemplo: '100,0' -> 10000 -> '10000'
             '50,0'  -> 5000  -> '05000'
             '33,3'  -> 3330  -> '03330'
    """
    if pd.isna(val) or val is None:
        return 0
    s = str(val).replace('%', '').replace('.', '').replace(',', '.').strip()
    try:
        f = float(s)
        return int(round(f * 100))
    except ValueError:
        return 0


def get_doc_type_code(tipo_doc, nro_doc):
    """
    Mapea el tipo de documento a los códigos oficiales ARCA (Anexo 1):
    80=CUIT, 86=CUIL, 87=CDI, 89=LC, 90=LE, 94=PASAPORTE, 96=DNI, 24=CI Tierra del Fuego
    """
    td = str(tipo_doc).strip().upper() if pd.notna(tipo_doc) else ""
    if td in ['DNI', 'MI']:
        return "96"
    elif td == 'LE':
        return "90"
    elif td == 'LC':
        return "89"
    elif td == 'CI':
        return "24"
    elif td == 'PASAPORTE':
        return "94"
    elif td == 'CUIT':
        return "80"
    elif td == 'CUIL':
        return "86"
    elif td == 'CDI':
        return "87"
    else:
        return "00"


def get_inmueble_type_code(row):
    """
    Mapea las características del inmueble al código del Anexo (11):
    01=Casa, 02=Departamento, 06=Lote, 08=Mejoras, 09=Rural c/viv, 10=Rural s/viv, 99=Otros
    """
    padron = str(row.get('Padron', '')).strip().lower()
    uso = str(row.get('Uso', '')).strip().lower()
    uf = str(row.get('U.F./U.C.', '')).strip()

    if padron == 'rural':
        if uso in ['edificada', 'en construccion']:
            return "09"
        else:
            return "10"
    else:
        if uf and uf.lower() != 'nan':
            return "02"
        elif uso == 'baldia':
            return "06"
        elif uso == 'edificada':
            return "01"
        elif uso in ['a construir', 'en construccion']:
            return "08"
        else:
            return "99"


def get_postal_code(departamento):
    """
    Mapea el departamento al Código Postal Argentino (CPA de 8 caracteres, Anexo 5).
    Rio Grande -> V9420   
    Ushuaia    -> V9410   
    Tolhuin    -> V9405   
    """
    dep = str(departamento).strip().lower() if pd.notna(departamento) else ""
    if 'rio grande' in dep:
        return "V9420   "
    elif 'ushuaia' in dep:
        return "V9410   "
    elif 'tolhuin' in dep:
        return "V9405   "
    else:
        return "V9400   "


def build_nomenclatura(row):
    """
    Construye la Nomenclatura Catastral unívoca del inmueble (Anexo 8).
    Longitud máxima 60 caracteres.
    """
    def cval(key):
        v = row.get(key)
        if pd.isna(v) or v is None:
            return ""
        if isinstance(v, (float, np.floating)) and v.is_integer():
            return str(int(v))
        return str(v).strip()

    parts = []
    dep = cval('Departamento')
    if dep:
        if 'rio' in dep.lower(): parts.append('DEP:RG')
        elif 'ush' in dep.lower(): parts.append('DEP:US')
        elif 'tol' in dep.lower(): parts.append('DEP:TO')
        else: parts.append(f'DEP:{dep[:3].upper()}')
    
    par = cval('Partida')
    if par: parts.append(f'PAR:{par}')
    sec = cval('Seccion')
    if sec: parts.append(f'SEC:{sec}')
    cha = cval('Chacra')
    if cha: parts.append(f'CHA:{cha}')
    qta = cval('Quinta')
    if qta: parts.append(f'QTA:{qta}')
    mac = cval('Macizo')
    if mac: parts.append(f'MAC:{mac}')
    fra = cval('Fraccion')
    if fra: parts.append(f'FRA:{fra}')
    prc = cval('Parcela')
    if prc: parts.append(f'PARC:{prc}')
    uf = cval('U.F./U.C.')
    if uf: parts.append(f'UF:{uf}')

    res = "-".join(parts)
    if not res:
        res = "SIN NOMENCLATURA"
    return res[:60]


def process_data(csv_path, year=DEFAULT_YEAR):
    """
    Carga el CSV de origen, realiza las transformaciones necesarias y
    retorna la línea de ROTULO CABECERA y las líneas de PROPIEDADES TITULARES.
    """
    print(f"Cargando dataset desde: {csv_path}")
    df = pd.read_csv(csv_path, sep=None, engine='python')
    total_records = len(df)
    print(f"Total de registros a procesar: {total_records}")

    # 1. Construir Nomenclatura Catastral por fila
    df['nomenclatura_str'] = df.apply(build_nomenclatura, axis=1)

    # 2. Calcular 'Cantidad de Titulares' por Nomenclatura Catastral (Anexo 14)
    nom_counts = df['nomenclatura_str'].value_counts()
    df['cant_titulares'] = df['nomenclatura_str'].map(nom_counts)

    # 3. Generar registros de PROPIEDADES TITULARES (Tipo 02 - 344 caracteres)
    titulares_lines = []
    
    for idx, row in df.iterrows():
        # Campo 1: Tipo de Registro (2) -> "02"
        f1 = "02"

        # Campo 2: Razón Social o Apellido y Nombre (50) -> Titular
        f2 = pad_alpha(row.get('Titular'), 50)

        # Campo 3: CUIT, CUIL, CDI (11)
        tipo_doc_raw = str(row.get('Tipo Doc')).strip().upper() if pd.notna(row.get('Tipo Doc')) else ""
        nro_doc_raw = str(row.get('Nro Documento')).strip() if pd.notna(row.get('Nro Documento')) else ""
        if nro_doc_raw.endswith('.0'): nro_doc_raw = nro_doc_raw[:-2]
        digits_nro_doc = "".join(filter(str.isdigit, nro_doc_raw))

        cuit_cuil_cdi = "00000000000"
        if tipo_doc_raw in ['CUIT', 'CUIL', 'CDI'] and len(digits_nro_doc) == 11:
            cuit_cuil_cdi = digits_nro_doc
        elif len(digits_nro_doc) == 11:
            cuit_cuil_cdi = digits_nro_doc
        f3 = pad_num(cuit_cuil_cdi, 11)

        # Campo 4: Tipo de documento (2)
        doc_code = get_doc_type_code(tipo_doc_raw, nro_doc_raw)
        f4 = pad_num(doc_code, 2)

        # Campo 5: Número de Documento (11)
        if doc_code in ['80', '86', '87']:
            f5 = pad_num(cuit_cuil_cdi, 11)
        else:
            f5 = pad_num(digits_nro_doc if digits_nro_doc else "0", 11)

        # Campo 6: Porcentaje de Titularidad (5) -> 9(3)v99
        dom_cents = parse_dominio_cents(row.get('Dominio'))
        f6 = pad_num(dom_cents, 5)

        # Campo 7: Marca Tipo de Domicilio (1) -> "I"
        f7 = "I"

        # Campo 8: Domicilio - Calle (30) -> "SIN CALLE" o default
        f8 = pad_alpha("SIN CALLE", 30)

        # Campo 9: Domicilio - Número/Km. (6) -> "S/N"
        f9 = pad_alpha("S/N", 6)

        # Campo 10-15: Domicilio Opcionales (5+5+5+5+5+25 = 50 espacios)
        f10_15 = " " * 50

        # Campo 16: Localidad (30) -> Departamento
        f16 = pad_alpha(row.get('Departamento'), 30)

        # Campo 17: Código Postal (8) -> CPA
        f17 = pad_alpha(get_postal_code(row.get('Departamento')), 8)

        # Campo 18: Código de Provincia (2) -> "24"
        f18 = "24"

        # Campo 19: Zona del Inmueble (1) -> "U" / "R"
        padron_val = str(row.get('Padron', '')).strip().lower()
        f19 = "R" if padron_val == 'rural' else "U"

        # Campo 20: Nomenclatura Catastral (60)
        f20 = pad_alpha(row.get('nomenclatura_str'), 60)

        # Campo 21: Matrícula del Inmueble (30) -> Instrumento
        inst = row.get('Instrumento') if pd.notna(row.get('Instrumento')) else row.get('Tipo de Instrumento')
        f21 = pad_alpha(inst, 30)

        # Campo 22: Valuación Fiscal (13) -> 9(11)v99
        vtotal_cents = parse_money_cents(row.get('Valor Total'))
        f22 = pad_num(vtotal_cents, 13)

        # Campo 23: Base Imponible (13) -> 9(11)v99
        f23 = pad_num(vtotal_cents, 13)

        # Campo 24: Tipo de Inmueble (2)
        f24 = pad_num(get_inmueble_type_code(row), 2)

        # Campo 25: Superficie (13) -> 9(11)v99
        sup_uf = parse_surface_cents(row.get('Superficie UF/UC'))
        sup_tot = parse_surface_cents(row.get('Superficie'))
        sup_used = sup_uf if sup_uf > 0 else sup_tot
        f25 = pad_num(sup_used, 13)

        # Campo 26: Unidad de Medida (1) -> 1=m2, 4=Ha
        uni_med = str(row.get('Uni. Medida', '')).strip().lower()
        f26 = "4" if 'ha' in uni_med else "1"

        # Campo 27: Cantidad de Titulares (3)
        cant_tit = row.get('cant_titulares', 1)
        f27 = pad_num(cant_tit, 3)

        # Concatenar todos los campos para formar la línea de 344 caracteres
        line = f"{f1}{f2}{f3}{f4}{f5}{f6}{f7}{f8}{f9}{f10_15}{f16}{f17}{f18}{f19}{f20}{f21}{f22}{f23}{f24}{f25}{f26}{f27}"
        
        if len(line) != 344:
            raise ValueError(f"Error en la fila {idx}: longitud obtenida {len(line)} != 344")
        
        titulares_lines.append(line)

    # 4. Generar registro de ROTULO CABECERA (Tipo 01 - 31 caracteres)
    # Pos 1-2: "01"
    # Pos 3-4: "24" (Provincia)
    # Pos 5-8: Year (4)
    # Pos 9-10: "00" (Secuencia)
    # Pos 11-22: Cantidad de registros tipo 02 (12)
    # Pos 23-26: "6500" (Formulario)
    # Pos 27-31: "00100" (Versión)
    c1 = "01"
    c2 = "24"
    c3 = pad_num(year, 4)
    c4 = "00"
    c5 = pad_num(total_records, 12)
    c6 = "6500"
    c7 = "00100"

    cabecera_line = f"{c1}{c2}{c3}{c4}{c5}{c6}{c7}"
    if len(cabecera_line) != 31:
        raise ValueError(f"Error en Rótulo Cabecera: longitud obtenida {len(cabecera_line)} != 31")

    return cabecera_line, titulares_lines


def main():
    parser = argparse.ArgumentParser(description="Generador de Archivo Unificado SETI ARCA F6500")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Ruta al archivo CSV de origen")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="Directorio de salida para el archivo")
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR, help="Año de corte de la información")
    parser.add_argument("--cuit", default=DEFAULT_CUIT, help="CUIT del organismo/provincia que presenta el F6500")
    parser.add_argument("--date", default="", help="Fecha del archivo en formato AAAAMMDD (opcional)")
    parser.add_argument("--seq", default="", help="Número secuencial nnnn de archivo del día (opcional)")
    parser.add_argument("--out-file", default="", help="Nombre personalizado del archivo de salida")

    args = parser.parse_args()

    cuit_clean = "".join(filter(str.isdigit, str(args.cuit)))
    if not cuit_clean:
        cuit_clean = DEFAULT_CUIT

    # Determinar nombre del archivo según formato especificado en ANEXO SETI PROVINCIAS.PDF:
    # F6500.XXXXXXXXXXX.txt o F6500.XXXXXXXXXXX.AAAAMMDD.nnnn.txt
    if args.out_file:
        out_filename = args.out_file
    elif args.date and args.seq:
        out_filename = f"F6500.{cuit_clean}.{args.date}.{args.seq.zfill(4)}.txt"
    else:
        out_filename = f"F6500.{cuit_clean}.txt"

    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, out_filename)

    cabecera_line, titulares_lines = process_data(args.csv, year=args.year)

    print(f"Escribiendo archivo unificado SETI F6500 en: {out_path}")
    with open(out_path, "w", encoding="iso-8859-1", newline="") as f:
        # Línea 1: Rótulo Cabecera (31 posiciones)
        f.write(cabecera_line + "\r\n")
        # Líneas 2..N+1: Propiedades Titulares (344 posiciones c/u)
        for line in titulares_lines:
            f.write(line + "\r\n")

    print("\n==================================================")
    print("PROCESO COMPLETADO EXITOSAMENTE!")
    print(f"- Archivo Unificado: {out_path}")
    print(f"- Cabecera (Línea 1): 1 registro de Tipo 01 ({len(cabecera_line)} pos)")
    print(f"- Cuerpo (Líneas 2..{len(titulares_lines)+1}): {len(titulares_lines)} registros de Tipo 02 (344 pos c/u)")
    print("==================================================")


if __name__ == "__main__":
    main()

