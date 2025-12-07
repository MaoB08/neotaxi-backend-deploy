-- ============================================
-- SCRIPT SQL: Asignar Barrios Aleatorios a Viajes
-- ============================================
-- Este script asigna barrios aleatorios DIFERENTES
-- para origen y destino de cada viaje

-- PASO 1: Crear función temporal para asignar barrios aleatorios
CREATE OR REPLACE FUNCTION assign_random_neighborhoods()
RETURNS void AS $$
DECLARE
    trip_record RECORD;
    origin_id INTEGER;
    destination_id INTEGER;
    neighborhood_ids INTEGER[];
BEGIN
    -- Obtener todos los IDs de barrios disponibles
    SELECT ARRAY_AGG(neighborhood_id) INTO neighborhood_ids
    FROM neighborhood;
    
    -- Iterar sobre cada viaje
    FOR trip_record IN 
        SELECT trip_id FROM trip 
        WHERE origin_neighborhood_id IS NULL 
           OR destination_neighborhood_id IS NULL
    LOOP
        -- Seleccionar origen aleatorio
        origin_id := neighborhood_ids[1 + floor(random() * array_length(neighborhood_ids, 1))::int];
        
        -- Seleccionar destino aleatorio diferente al origen
        LOOP
            destination_id := neighborhood_ids[1 + floor(random() * array_length(neighborhood_ids, 1))::int];
            EXIT WHEN destination_id != origin_id;
        END LOOP;
        
        -- Actualizar el viaje
        UPDATE trip 
        SET origin_neighborhood_id = origin_id,
            destination_neighborhood_id = destination_id
        WHERE trip_id = trip_record.trip_id;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- PASO 2: Ejecutar la función
SELECT assign_random_neighborhoods();

-- PASO 3: Eliminar la función temporal
DROP FUNCTION assign_random_neighborhoods();

-- PASO 4: Eliminar la columna antigua neighborhood_id
ALTER TABLE trip 
DROP COLUMN IF EXISTS neighborhood_id;

-- ============================================
-- VERIFICACIÓN
-- ============================================

-- Ver algunos viajes con sus barrios
SELECT 
    t.trip_id,
    t.client_document,
    t.driver_document,
    o.name as origen,
    d.name as destino,
    t.start_time,
    t.status
FROM trip t
LEFT JOIN neighborhood o ON t.origin_neighborhood_id = o.neighborhood_id
LEFT JOIN neighborhood d ON t.destination_neighborhood_id = d.neighborhood_id
LIMIT 10;

-- Verificar que todos los viajes tienen origen y destino diferentes
SELECT 
    COUNT(*) as total_trips,
    COUNT(CASE WHEN origin_neighborhood_id = destination_neighborhood_id THEN 1 END) as same_origin_destination,
    COUNT(CASE WHEN origin_neighborhood_id IS NULL OR destination_neighborhood_id IS NULL THEN 1 END) as missing_neighborhoods
FROM trip;

-- Verificar distribución de barrios
SELECT 
    'Origen' as tipo,
    n.name as barrio,
    COUNT(*) as cantidad
FROM trip t
JOIN neighborhood n ON t.origin_neighborhood_id = n.neighborhood_id
GROUP BY n.name
UNION ALL
SELECT 
    'Destino' as tipo,
    n.name as barrio,
    COUNT(*) as cantidad
FROM trip t
JOIN neighborhood n ON t.destination_neighborhood_id = n.neighborhood_id
GROUP BY n.name
ORDER BY tipo, cantidad DESC;
