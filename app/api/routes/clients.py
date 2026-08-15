from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.db.models import User, Client, Case
from app.api.schemas import ClientCreate, ClientUpdate, ClientResponse, CaseResponse
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/clients", tags=["clients"])

@router.post("/", response_model=ClientResponse)
async def create_client(client_data: ClientCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new client for the current user."""
    client = Client(
        user_id=current_user.id,
        name=client_data.name,
        age=client_data.age,
        gender=client_data.gender,
        place_of_stay=client_data.place_of_stay,
        contact_info=client_data.contact_info
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client

@router.get("/", response_model=list[ClientResponse])
async def list_clients(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all clients belonging to the current user."""
    result = await db.execute(select(Client).where(Client.user_id == current_user.id))
    return result.scalars().all()

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get a specific client by ID."""
    result = await db.execute(select(Client).where(Client.id == client_id, Client.user_id == current_user.id))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(client_id: int, client_data: ClientUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update a specific client."""
    result = await db.execute(select(Client).where(Client.id == client_id, Client.user_id == current_user.id))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    for key, value in client_data.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
        
    await db.commit()
    await db.refresh(client)
    return client

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(client_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete a specific client."""
    result = await db.execute(select(Client).where(Client.id == client_id, Client.user_id == current_user.id))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    await db.delete(client)
    await db.commit()

@router.get("/{client_id}/cases", response_model=list[CaseResponse])
async def get_client_cases(client_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all cases for a specific client."""
    result = await db.execute(select(Client).where(Client.id == client_id, Client.user_id == current_user.id))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    result = await db.execute(select(Case).where(Case.client_id == client_id))
    return result.scalars().all()
