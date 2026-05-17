from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models.attribute_category import AttributeCategory
from models.attribute_value import AttributeValue

router = APIRouter()


class CategoryInput(BaseModel):
    name: str


class ValueInput(BaseModel):
    category_id: int
    value: str


@router.get("/attribute_categories")
def get_attribute_categories(db: Session = Depends(get_db)):
    cats = db.query(AttributeCategory).all()
    return [{"id": c.id, "name": c.name, "created_at": c.created_at.isoformat() if c.created_at else None} for c in cats]


@router.post("/attribute_categories")
def create_attribute_category(data: CategoryInput, db: Session = Depends(get_db)):
    existing = db.query(AttributeCategory).filter(AttributeCategory.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"La categoria '{data.name}' ya existe")
    cat = AttributeCategory(name=data.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return {"id": cat.id, "name": cat.name, "created_at": cat.created_at.isoformat() if cat.created_at else None}


@router.delete("/attribute_categories/{category_id}")
def delete_attribute_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(AttributeCategory).filter(AttributeCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    db.query(AttributeValue).filter(AttributeValue.category_id == category_id).delete()
    db.delete(cat)
    db.commit()
    return {"message": "Categoria eliminada"}


@router.get("/attribute_values")
def get_attribute_values(category_id: int = Query(None), db: Session = Depends(get_db)):
    q = db.query(AttributeValue)
    if category_id:
        q = q.filter(AttributeValue.category_id == category_id)
    vals = q.all()
    return [{"id": v.id, "category_id": v.category_id, "value": v.value, "created_at": v.created_at.isoformat() if v.created_at else None} for v in vals]


@router.post("/attribute_values")
def create_attribute_value(data: ValueInput, db: Session = Depends(get_db)):
    cat = db.query(AttributeCategory).filter(AttributeCategory.id == data.category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    existing = db.query(AttributeValue).filter(
        AttributeValue.category_id == data.category_id,
        AttributeValue.value == data.value
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El valor '{data.value}' ya existe en esta categoria")
    av = AttributeValue(category_id=data.category_id, value=data.value)
    db.add(av)
    db.commit()
    db.refresh(av)
    return {"id": av.id, "category_id": av.category_id, "value": av.value, "created_at": av.created_at.isoformat() if av.created_at else None}
