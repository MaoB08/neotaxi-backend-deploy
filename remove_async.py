import os
import glob

# Path to the api directory
api_dir = "c:/Users/USUARIO/Desktop/NeoTaxi/NeoTaxiProyect/neotaxi-backend/api"

for filepath in glob.glob(os.path.join(api_dir, "*.py")):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple replace
    new_content = content.replace('async def ', 'def ')
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {os.path.basename(filepath)}")
