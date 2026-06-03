from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from Backend.database import get_db
from Backend.models.category import Category
from Backend.models.attribute import Attribute

router = APIRouter()


class CategoryInput(BaseModel):
    name: str


class AttributeInput(BaseModel):
    category_id: int
    name: str


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
    db.query(Attribute).filter(Attribute.category_id == category_id).delete()
    db.delete(cat)
    db.commit()
    return {"message": "Categoria eliminada"}


@router.get("/attributes")
def get_attributes(category_id: int = Query(None), db: Session = Depends(get_db)):
    q = db.query(Attribute)
    if category_id:
        q = q.filter(Attribute.category_id == category_id)
    attrs = q.all()
    return [{"id": a.id, "category_id": a.category_id, "name": a.name, "created_at": a.created_at.isoformat() if a.created_at else None} for a in attrs]


@router.post("/attributes")
def create_attribute(data: AttributeInput, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == data.category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    existing = db.query(Attribute).filter(
        Attribute.category_id == data.category_id,
        Attribute.name == data.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El atributo '{data.name}' ya existe en esta categoria")
    av = Attribute(category_id=data.category_id, name=data.name)
    db.add(av)
    db.commit()
    db.refresh(av)
    return {"id": av.id, "category_id": av.category_id, "name": av.name, "created_at": av.created_at.isoformat() if av.created_at else None}
