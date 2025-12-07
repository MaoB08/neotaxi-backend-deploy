import asyncio
from core.database import supabase
import sys

async def main():
    try:
        print("--- DRIVER STATUSES ---")
        drivers = supabase.table("driver").select("status").execute()
        status_counts = {}
        for d in drivers.data:
            s = d.get('status', 'NULL')
            status_counts[s] = status_counts.get(s, 0) + 1
        
        for s, count in status_counts.items():
            print(f"Status '{s}': {count}")

        print("\n--- TRIP STATUSES ---")
        trips = supabase.table("trip").select("status").execute()
        trip_counts = {}
        for t in trips.data:
            s = t.get('status', 'NULL')
            trip_counts[s] = trip_counts.get(s, 0) + 1
            
        for s, count in trip_counts.items():
            print(f"Status '{s}': {count}")

        print("\n--- CLIENT COUNT ---")
        clients = supabase.table("client").select("count", count="exact").execute()
        print(f"Total clients via count: {clients.count}")
        
        clients_data = supabase.table("client").select("document").execute()
        print(f"Total clients via data length: {len(clients_data.data)}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
