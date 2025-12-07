-- ============================================
-- SCRIPT SQL: Actualizar Tabla TRIP
-- ============================================
-- Este script actualiza la tabla trip para soportar
-- origen y destino como dos barrios diferentes

-- PASO 1: Agregar nuevas columnas
ALTER TABLE trip 
ADD COLUMN origin_neighborhood_id INTEGER,
ADD COLUMN destination_neighborhood_id INTEGER;

-- PASO 2: Migrar datos existentes
-- Copiar neighborhood_id existente a destination_neighborhood_id
UPDATE trip 
SET destination_neighborhood_id = neighborhood_id
WHERE neighborhood_id IS NOT NULL;

-- PASO 3: Agregar foreign keys
ALTER TABLE trip
ADD CONSTRAINT fk_origin_neighborhood 
FOREIGN KEY (origin_neighborhood_id) 
REFERENCES neighborhood(neighborhood_id);

ALTER TABLE trip
ADD CONSTRAINT fk_destination_neighborhood 
FOREIGN KEY (destination_neighborhood_id) 
REFERENCES neighborhood(neighborhood_id);

-- PASO 4 (OPCIONAL): Eliminar columna antigua
-- Solo ejecutar esto si estás seguro de que ya no la necesitas
-- ALTER TABLE trip DROP COLUMN neighborhood_id;

-- ============================================
-- VERIFICACIÓN
-- ============================================
-- Ejecuta esto para verificar que la estructura es correcta
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'trip'
ORDER BY ordinal_position;
