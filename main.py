from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import date, timedelta

app = FastAPI()

class Contact(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    birthday: str
    additional_data: str

class ContactCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=1, max_length=20)
    birthday: str
    additional_data: str = Field(max_length=500)

engine = create_engine('sqlite:///contacts.db')
Base = declarative_base()

class Contact(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    phone = Column(String)
    birthday = Column(String)
    additional_data = Column(String)


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
db = Session()

@app.post("/contacts", status_code=201)
async def create_contact(contact: ContactCreate):
    contact_to_create = Contact(
        first_name=contact.first_name,
        last_name=contact.last_name,
        email=contact.email,
        phone=contact.phone,
        birthday=contact.birthday,
        additional_data=contact.additional_data
    )
    db.add(contact_to_create)
    db.commit()
    return JSONResponse(content={"message": "Contact created"}, media_type="application/json")

@app.get("/contacts")
async def get_contacts(page: int = 1, page_size: int = 10, sort_by: str = "first_name", sort_order: str = "asc"):
    contacts = db.query(Contact).all()
    if sort_by == "first_name":
        contacts.sort(key=lambda x: x.first_name, reverse=sort_order == "desc")
    elif sort_by == "last_name":
        contacts.sort(key=lambda x: x.last_name, reverse=sort_order == "desc")
    elif sort_by == "email":
        contacts.sort(key=lambda x: x.email, reverse=sort_order == "desc")
    start = (page - 1) * page_size
    end = start + page_size
    return JSONResponse(content={"contacts": [contact.__dict__ for contact in contacts[start:end]]}, media_type="application/json")

@app.get("/contacts/{contact_id}")
async def get_contact(contact_id: int):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return JSONResponse(content={"contact": contact.__dict__}, media_type="application/json")

@app.put("/contacts/{contact_id}")
async def update_contact(contact_id: int, contact: ContactCreate):
    contact_to_update = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact_to_update is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact_to_update.first_name = contact.first_name
    contact_to_update.last_name = contact.last_name
    contact_to_update.email = contact.email
    contact_to_update.phone = contact.phone
    contact_to_update.birthday = contact.birthday
    contact_to_update.additional_data = contact.additional_data
    db.commit()
    return JSONResponse(content={"message": "Contact updated"}, media_type="application/json")

@app.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: int):
    contact_to_delete = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact_to_delete is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact_to_delete)
    db.commit()
    return JSONResponse(content={"message": "Contact deleted"}, media_type="application/json")

@app.get("/contacts/search")
async def search_contacts(name: str = "", surname: str = "", email: str = ""):
    contacts = db.query(Contact).filter(
        (Contact.first_name.like('%' + name + '%')) |
        (Contact.last_name.like('%' + surname + '%')) |
        (Contact.email.like('%' + email + '%'))
    ).all()
    return JSONResponse(content={"contacts": [contact.__dict__ for contact in contacts]}, media_type="application/json")

@app.get("/contacts/upcoming_birthdays")
async def upcoming_birthdays():
    today = date.today()
    next_week = today + timedelta(days=7)
    contacts = db.query(Contact).filter(
        func.strftime('%m-%d', Contact.birthday) >= func.strftime('%m-%d', today),
        func.strftime('%m-%d', Contact.birthday) <= func.strftime('%m-%d', next_week)
    ).all()
    return JSONResponse(content={"contacts": [contact.__dict__ for contact in contacts]}, media_type="application/json")

def get_db():
    try:
        db = Session()
        yield db
    finally:
        db.close()