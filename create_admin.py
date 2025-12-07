"""
Script simple para generar hash de contraseña de admin
"""

import bcrypt

# Datos del administrador
admin_email = "admin@neotaxi.com"
admin_password = "admin123"

# Generar hash de la contraseña
hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

print("=" * 60)
print("CREAR USUARIO ADMINISTRADOR")
print("=" * 60)
print(f"\nEmail: {admin_email}")
print(f"Password: {admin_password}")
print(f"Hash: {hashed_password}")
print("\n" + "=" * 60)
print("SQL para insertar en Supabase:")
print("=" * 60)
print(f"""
INSERT INTO "user" (email, password)
VALUES ('{admin_email}', '{hashed_password}');
""")
print("=" * 60)
print("\nCopia y ejecuta el SQL en Supabase SQL Editor")
print("=" * 60)
