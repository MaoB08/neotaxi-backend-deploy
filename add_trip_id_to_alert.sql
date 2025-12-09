-- ============================================
-- ARCHIVO: add_trip_id_to_alert.sql
-- DESCRIPCIÓN: Agregar columna trip_id a la tabla alert
-- FECHA: 2025-12-08
-- ============================================

-- OPCIÓN 1: Si la tabla alert está VACÍA o NO tiene datos importantes
-- ============================================
ALTER TABLE alert
ADD COLUMN trip_id INTEGER NOT NULL;

-- Agregar foreign key constraint
ALTER TABLE alert
ADD CONSTRAINT fk_alert_trip
FOREIGN KEY (trip_id) REFERENCES trip(trip_id)
ON DELETE CASCADE;

-- Crear índice para mejorar rendimiento
CREATE INDEX idx_alert_trip_id ON alert(trip_id);


-- ============================================
-- OPCIÓN 2: Si la tabla alert YA TIENE DATOS
-- ============================================

-- Paso 1: Agregar columna como nullable primero
ALTER TABLE alert
ADD COLUMN trip_id INTEGER;

-- Paso 2: Actualizar registros existentes (OPCIONAL)
-- Si quieres asignar un trip_id por defecto a alertas antiguas
-- UPDATE alert SET trip_id = 1 WHERE trip_id IS NULL;

-- Paso 3: Hacer la columna NOT NULL
ALTER TABLE alert
ALTER COLUMN trip_id SET NOT NULL;

-- Paso 4: Agregar foreign key constraint
ALTER TABLE alert
ADD CONSTRAINT fk_alert_trip
FOREIGN KEY (trip_id) REFERENCES trip(trip_id)
ON DELETE CASCADE;

-- Paso 5: Crear índice
CREATE INDEX idx_alert_trip_id ON alert(trip_id);


-- ============================================
-- VERIFICACIÓN
-- ============================================

-- Ver la estructura de la tabla alert
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'alert'
ORDER BY ordinal_position;

-- Ver las constraints
SELECT
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
LEFT JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'alert';

-- Ver los índices
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'alert';


-- ============================================
-- ROLLBACK (Si necesitas deshacer los cambios)
-- ============================================

-- Eliminar foreign key constraint
-- ALTER TABLE alert DROP CONSTRAINT fk_alert_trip;

-- Eliminar índice
-- DROP INDEX idx_alert_trip_id;

-- Eliminar columna
-- ALTER TABLE alert DROP COLUMN trip_id;
