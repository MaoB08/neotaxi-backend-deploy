from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Generar hashes para las contraseñas
passwords = ["123456", "password123", "admin123"]

print("=" * 60)
print("HASHES GENERADOS:")
print("=" * 60)

for pwd in passwords:
    hashed = pwd_context.hash(pwd)
    print(f"\nContraseña: {pwd}")
    print(f"Hash: {hashed}")
    print(f"Longitud: {len(hashed)} caracteres")
    
    # Verificar que funciona
    is_valid = pwd_context.verify(pwd, hashed)
    print(f"Verificación: {'✅ OK' if is_valid else '❌ FAIL'}")

print("\n" + "=" * 60)