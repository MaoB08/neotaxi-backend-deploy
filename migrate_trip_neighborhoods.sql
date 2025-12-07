-- ============================================
-- SCRIPT SQL: Migrar y Limpiar Tabla TRIP
-- ============================================
-- Este script asigna valores aleatorios de origen y destino
-- a los viajes existentes y elimina la columna antigua

-- PASO 1: Asignar valores aleatorios de barrios a los viajes existentes
-- Esto asigna un barrio aleatorio de la tabla neighborhood a cada viaje

-- Para origin_neighborhood_id
UPDATE trip
SET origin_neighborhood_id = (
    SELECT neighborhood_id 
    FROM neighborhood 
    ORDER BY RANDOM() 
    LIMIT 1
)
WHERE origin_neighborhood_id IS NULL;

-- Para destination_neighborhood_id
UPDATE trip
SET destination_neighborhood_id = (
    SELECT neighborhood_id 
    FROM neighborhood 
    ORDER BY RANDOM() 
    LIMIT 1
)
WHERE destination_neighborhood_id IS NULL;

-- PASO 2: Eliminar la columna antigua neighborhood_id
ALTER TABLE trip 
DROP COLUMN IF EXISTS neighborhood_id;

-- ============================================
-- VERIFICACIÓN
-- ============================================
-- Ejecuta esto para verificar que todo está correcto

-- Ver estructura de la tabla
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'trip'
ORDER BY ordinal_position;

-- Ver algunos viajes con sus barrios
SELECT 
    trip_id,
    client_document,
    driver_document,
    origin_neighborhood_id,
    destination_neighborhood_id,
    start_time,
    status
FROM trip
LIMIT 10;

-- Verificar que todos los viajes tienen origen y destino
SELECT 
    COUNT(*) as total_trips,
    COUNT(origin_neighborhood_id) as with_origin,
    COUNT(destination_neighborhood_id) as with_destination
FROM trip;
