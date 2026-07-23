SELECT 
    pa.parcela_partida,
    '02' as tipo_registro, 
    CASE 
        WHEN p.tipo_persona_id = 1 THEN CONCAT(p.persona_nombre, ', ', p.persona_apellido) /* Personas humanas devuelve el nombre y apellido */
        WHEN p.tipo_persona_id = 2 THEN p.persona_denominacion /* Personas juridicas devuelve denominación */
        ELSE NULL
    END AS razon_social_apellido_nombre, 
    CASE 
        WHEN p.tipo_persona_id = 2 AND p.tipo_documento_id = 8 THEN p.persona_nro_doc
        WHEN p.tipo_persona_id = 2 THEN p.persona_cuit
        ELSE NULL
    END AS CUIT_CUIL_CDI, 
    CASE 
        WHEN p.tipo_persona_id = 2 AND p.tipo_documento_id = 8 THEN 86 /* CUIL */
        WHEN p.tipo_persona_id = 2 THEN 80 /* CUIT */
	    WHEN p.tipo_documento_id = 1 THEN 90 /* LE */
        WHEN p.tipo_documento_id = 2 THEN 89 /* LC */
        WHEN p.tipo_documento_id IN (3, 4) THEN 96 /* DNI */
        WHEN p.tipo_documento_id = 6 THEN 24 /* CI Tierra del Fuego */
        WHEN p.tipo_documento_id IN (0, 5, 7) THEN NULL 
        ELSE NULL
    END AS tipo_de_documento, 
    CASE 
        WHEN tipo_persona_id = 1 THEN p.persona_nro_doc /* Personas humanas devuelve el número de documento */
        ELSE NULL
    END AS numero_de_documento, 
    pp.persona_parcela_dominio AS porcentaje_de_titularidad, /* OPCIONAL (puede contener null) */
    (
        SELECT SUM(persona_parcela_dominio)
        FROM personas_parcelas AS sub
        WHERE sub.parcela_id = pp.parcela_id
          AND sub.persona_parcela_id <= pp.persona_parcela_id
    ) AS acumulado_persona_parcela_dominio, /* Esta columna se puede omitir es sólo a los efectos de control el 100% de dominio */
    CASE 
        WHEN d.tipo_direccion_id IN (1, 2) THEN 'I'
        WHEN d.tipo_direccion_id = 3 THEN 'P'
        ELSE NULL
    END AS marca_tipo_de_domicilio, 
    CASE 
        WHEN d.calle_nombre IS NULL THEN TRIM(CONCAT(pa.parcela_calle, ' ',pa.parcela_nro))
        ELSE TRIM(CONCAT(d.calle_nombre, ' ', d.direccion_numeracion)) 
    END AS domicilio_calle_numero_km, 
    TRIM(CONCAT(d.direccion_area, ' ', d.direccion_torre, ' ', d.direccion_piso, ' ',d.direccion_depto, ' ',d.direccion_manzana, ' ',d.barrio_nombre)) AS direccion_sector_torre_piso_depto__manzana_barrio, /* OPCIONAL (puede contener null) */ 
    CASE 
        WHEN d.localidad_nombre IS NULL THEN pa.parcela_localidad
        ELSE d.localidad_nombre
    END AS localidad,     
    d.direccion_cp AS codigo_postal, 
    CASE 
       WHEN d.provincia_id = 23 THEN 24
        ELSE NULL
    END AS codigo_de_provincia,
    CASE 
        WHEN pa.tipo_ubica_parcela_nw_id IN (1 and 7)  THEN 'U' /* Urbana */
        WHEN pa.tipo_ubica_parcela_nw_id IN (8 and 13)  THEN 'R' /* Rural */
        ELSE NULL
    END AS zona_del_inmueble, 
    pa.parcela_nomenclatura AS nomenclatura_catastral, 
    pa.parcela_p_municipal AS matricula_del_inmueble,
    pa.parcela_val_total AS valuacion_fiscal,
    pa.parcela_val_tierra AS base_imponible,
    CASE 
        WHEN tmd.tipo_mejora_destino_id = 1 THEN 1 /* CASA */
        WHEN tmd.tipo_mejora_destino_id = 2 THEN 5 /* LOCAL */
        WHEN tmd.tipo_mejora_destino_id = 3 THEN 99
        ELSE 99
    END AS tipo_de_inmueble,
    pa.parcela_super_mensura AS superficie,
    um.unidades_medidas_descrip AS unidad_de_medida,
    (SELECT COUNT(DISTINCT pp2.persona_id) 
     FROM personas_parcelas pp2 
     WHERE pp2.parcela_id = pa.parcela_id) AS cantidad_de_titulares,
    (SELECT pl_tmp.plano_f_registro
	  FROM parcelas p_tmp
      JOIN planos_parc_prov pp_tmp ON p_tmp.parcela_id = pp_tmp.parcela_id
      JOIN planos pl_tmp ON pp_tmp.plano_id = pl_tmp.plano_id
      WHERE p_tmp.parcela_id = pa.parcela_id 
        AND pl_tmp.tipo_estado_plano_id = 4) as fecha_registro_plano
FROM 
    parcelas pa
JOIN 
    personas_parcelas pp ON pa.parcela_id = pp.parcela_id
LEFT JOIN
    personas p ON pp.persona_id = p.persona_id
LEFT JOIN 
    direcciones d ON p.persona_id = d.persona_id
LEFT JOIN 
    tipos_documentos td ON p.tipo_documento_id = td.tipo_documento_id
LEFT JOIN
	mejoras m ON m.parcela_id = pa.parcela_id 
LEFT JOIN	
    tipos_mejoras_destinos tmd ON tmd.tipo_mejora_destino_id = m.tipo_mejora_destino_id
LEFT JOIN 
    unidades_medidas um ON pa.unidades_medidas_id = um.unidades_medidas_id
WHERE 
	pa.parcela_id <> 3698 and pa.parcela_id <> 38988 and /* duplicados para fecha de plano*/
	pp.tipo_estado_id = 1
	
ORDER BY
    pp.parcela_id, p.persona_nro_doc;
