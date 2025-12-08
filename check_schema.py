import asyncio
from core.database import supabase
import json

async def check_columns():
    try:
        # Fetch one row to see keys
        response = supabase.table("alert").select("*").limit(1).execute()
        if response.data:
            print("Columns in 'alert' table:")
            print(json.dumps(list(response.data[0].keys()), indent=2))
        else:
            print("No data in 'alert' table to infer columns.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_columns())
