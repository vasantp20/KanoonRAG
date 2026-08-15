import asyncio
import sys
from pathlib import Path

# Add project root to python path to allow imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db.database import init_db

async def main():
    print("Initializing database tables...")
    await init_db()
    print("Database tables created successfully.")

if __name__ == "__main__":
    asyncio.run(main())
