from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models.attribute_category import Category
from models.attribute_value import Value

router = APIRouter()


class CategoryInput(BaseModel):
    name: str


class ValueInput(BaseModel):
    category_id: int
    value: str


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    cats = db.query(Category).all()
    return [{"id": c.id, "name": c.name, "created_at": c.created_at.isoformat() if c.created_at else None} for c in cats]


@router.post("/categories")
def create_category(data: CategoryInput, db: Session = Depends(get_db)):
    existing = db.query(Category).filter(Category.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"La categoria '{data.name}' ya existe")
    cat = Category(name=data.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return {"id": cat.id, "name": cat.name, "created_at": cat.created_at.isoformat() if cat.created_at else None}


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    db.query(Value).filter(Value.category_id == category_id).delete()
    db.delete(cat)
    db.commit()
    return {"message": "Categoria eliminada"}


@router.get("/values")
def get_values(category_id: int = Query(None), db: Session = Depends(get_db)):
    q = db.query(Value)
    if category_id:
        q = q.filter(Value.category_id == category_id)
    vals = q.all()
    return [{"id": v.id, "category_id": v.category_id, "value": v.value, "created_at": v.created_at.isoformat() if v.created_at else None} for v in vals]


@router.post("/values")
def create_value(data: ValueInput, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == data.category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    existing = db.query(Value).filter(
        Value.category_id == data.category_id,
        Value.value == data.value
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El valor '{data.value}' ya existe en esta categoria")
    av = Value(category_id=data.category_id, value=data.value)
    db.add(av)
    db.commit()
    db.refresh(av)
    return {"id": av.id, "category_id": av.category_id, "value": av.value, "created_at": av.created_at.isoformat() if av.created_at else None}



def get_or_create_category(db: Session, name: str):
    category = db.query(AttributeCategory).filter_by(name=name.lower()).first()
    if not category:
        category = AttributeCategory(name=name.lower())
        db.add(category)
        db.commit()
        db.refresh(category)
    return category

def get_or_create_attribute_value(db: Session, category_id: int, value: str):
    attr_value = db.query(AttributeValue).filter_by(category_id=category_id, value=value).first()
    if not attr_value:
        attr_value = AttributeValue(category_id=category_id, value=value)
        db.add(attr_value)
        db.commit()
        db.refresh(attr_value)
    return attr_value