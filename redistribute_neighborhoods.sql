-- ============================================
-- SCRIPT SQL: REDISTRIBUIR Barrios Aleatorios
-- ============================================
-- Este script ACTUALIZA todos los viajes existentes
-- asignando barrios aleatorios DIFERENTES para cada uno

-- PASO 1: Crear función para redistribuir barrios
CREATE OR REPLACE FUNCTION redistribute_neighborhoods()
RETURNS void AS $$
DECLARE
    trip_record RECORD;
    origin_id INTEGER;
    destination_id INTEGER;
    neighborhood_ids INTEGER[];
    total_neighborhoods INTEGER;
BEGIN
    -- Obtener todos los IDs de barrios disponibles
    SELECT ARRAY_AGG(neighborhood_id) INTO neighborhood_ids
    FROM neighborhood;
    
    total_neighborhoods := array_length(neighborhood_ids, 1);
    
    RAISE NOTICE 'Total de barrios disponibles: %', total_neighborhoods;
    
    -- Iterar sobre TODOS los viajes (no solo los NULL)
    FOR trip_record IN 
        SELECT trip_id FROM trip
    LOOP
        -- Seleccionar origen aleatorio (índice entre 1 y total_neighborhoods)
        origin_id := neighborhood_ids[1 + floor(random() * total_neighborhoods)::int];
        
        -- Seleccionar destino aleatorio diferente al origen
        LOOP
            destination_id := neighborhood_ids[1 + floor(random() * total_neighborhoods)::int];
            EXIT WHEN destination_id != origin_id OR total_neighborhoods = 1;
        END LOOP;
        
        -- Actualizar el viaje
        UPDATE trip 
        SET origin_neighborhood_id = origin_id,
            destination_neighborhood_id = destination_id
        WHERE trip_id = trip_record.trip_id;
        
        -- Log cada 100 viajes
        IF trip_record.trip_id % 100 = 0 THEN
            RAISE NOTICE 'Procesados % viajes...', trip_record.trip_id;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Redistribución completada!';
END;
$$ LANGUAGE plpgsql;

-- PASO 2: Ejecutar la función
SELECT redistribute_neighborhoods();

-- PASO 3: Eliminar la función temporal
DROP FUNCTION redistribute_neighborhoods();

-- ============================================
-- VERIFICACIÓN DETALLADA
-- ============================================

-- 1. Ver distribución de barrios de ORIGEN
SELECT 
    n.neighborhood_id,
    n.name as barrio_origen,
    COUNT(*) as cantidad_como_origen,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM trip), 2) as porcentaje
FROM trip t
JOIN neighborhood n ON t.origin_neighborhood_id = n.neighborhood_id
GROUP BY n.neighborhood_id, n.name
ORDER BY cantidad_como_origen DESC;

-- 2. Ver distribución de barrios de DESTINO
SELECT 
    n.neighborhood_id,
    n.name as barrio_destino,
    COUNT(*) as cantidad_como_destino,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM trip), 2) as porcentaje
FROM trip t
JOIN neighborhood n ON t.destination_neighborhood_id = n.neighborhood_id
GROUP BY n.neighborhood_id, n.name
ORDER BY cantidad_como_destino DESC;

-- 3. Verificar que origen != destino
SELECT 
    COUNT(*) as total_viajes,
    COUNT(CASE WHEN origin_neighborhood_id = destination_neighborhood_id THEN 1 END) as mismo_origen_destino,
    COUNT(CASE WHEN origin_neighborhood_id IS NULL OR destination_neighborhood_id IS NULL THEN 1 END) as con_nulos
FROM trip;

-- 4. Ver algunos ejemplos de viajes
SELECT 
    t.trip_id,
    o.name as origen,
    d.name as destino,
    t.status
FROM trip t
LEFT JOIN neighborhood o ON t.origin_neighborhood_id = o.neighborhood_id
LEFT JOIN neighborhood d ON t.destination_neighborhood_id = d.neighborhood_id
ORDER BY t.trip_id
LIMIT 20;

-- 5. Contar cuántos barrios hay en total
SELECT COUNT(*) as total_barrios FROM neighborhood;
