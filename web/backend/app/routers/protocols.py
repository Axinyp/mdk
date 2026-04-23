from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.protocol import Protocol
from ..services.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/protocols", tags=["protocols"])


class ProtocolCreate(BaseModel):
    category: str
    brand_model: str
    comm_type: str
    content: str
    filename: str | None = None


class ProtocolUpdate(BaseModel):
    category: str | None = None
    brand_model: str | None = None
    comm_type: str | None = None
    content: str | None = None


class ProtocolResponse(BaseModel):
    id: int
    category: str
    brand_model: str
    comm_type: str
    filename: str | None
    content: str
    model_config = {"from_attributes": True}


class ProtocolListItem(BaseModel):
    id: int
    category: str
    brand_model: str
    comm_type: str
    filename: str | None
    model_config = {"from_attributes": True}


@router.get("", response_model=list[ProtocolListItem])
async def list_protocols(
    category: str = "",
    keyword: str = "",
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = select(Protocol).order_by(Protocol.category, Protocol.brand_model)
    if category:
        query = query.where(Protocol.category == category)
    if keyword:
        query = query.where(
            Protocol.brand_model.ilike(f"%{keyword}%")
            | Protocol.content.ilike(f"%{keyword}%")
        )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{protocol_id}", response_model=ProtocolResponse)
async def get_protocol(protocol_id: int, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    proto = await db.get(Protocol, protocol_id)
    if not proto:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return proto


@router.post("", response_model=ProtocolResponse, status_code=201)
async def create_protocol(req: ProtocolCreate, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    proto = Protocol(**req.model_dump())
    db.add(proto)
    await db.commit()
    await db.refresh(proto)
    return proto


@router.put("/{protocol_id}", response_model=ProtocolResponse)
async def update_protocol(
    protocol_id: int, req: ProtocolUpdate, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin),
):
    proto = await db.get(Protocol, protocol_id)
    if not proto:
        raise HTTPException(status_code=404, detail="Protocol not found")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(proto, k, v)
    await db.commit()
    await db.refresh(proto)
    return proto


@router.delete("/{protocol_id}")
async def delete_protocol(protocol_id: int, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    proto = await db.get(Protocol, protocol_id)
    if not proto:
        raise HTTPException(status_code=404, detail="Protocol not found")
    await db.delete(proto)
    await db.commit()
    return {"message": "Deleted"}
