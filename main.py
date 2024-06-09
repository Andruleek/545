from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import date, timedelta

app = FastAPI()

class ContactCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=1, max_length=20)
    birthday: str
    additional_data: str = Field(max_length=500)

@app.post("/contacts", status_code=201)
async def create_contact(contact: ContactCreate):
    db = next(get_db())
    contact_to_create = Contact(
        first_name=contact.first_name,
        last_name=contact.last_name,
        email=contact.email,
        phone=contact.phone,
        birthday=contact.birthday,
        additional_data=contact.additional_data
    )
    db.create_contact(contact_to_create)
    return JSONResponse(content={"message": "Contact created"}, media_type="application/json")

@app.get("/contacts")
async def get_contacts(page: int = 1, page_size: int = 10, sort_by: str = "first_name", sort_order: str = "asc"):
    db = next(get_db())
    contacts = db.get_contacts()
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
    db = next(get_db())
    contact = db.get_contact(contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return JSONResponse(content={"contact": contact.__dict__}, media_type="application/json")

@app.put("/contacts/{contact_id}")
async def update_contact(contact_id: int, contact: ContactCreate):
    db = next(get_db())
    contact_to_update = db.get_contact(contact_id)
    if contact_to_update is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact_to_update.first_name = contact.first_name
    contact_to_update.last_name = contact.last_name
    contact_to_update.email = contact.email
    contact_to_update.phone = contact.phone
    contact_to_update.birthday = contact.birthday
    contact_to_update.additional_data = contact.additional_data
    db.update_contact(contact_id, contact_to_update)
    return JSONResponse(content={"message": "Contact updated"}, media_type="application/json")

@app.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: int):
    db = next(get_db())
    contact_to_delete = db.get_contact(contact_id)
    if contact_to_delete is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete_contact(contact_id)
    return JSONResponse(content={"message": "Contact deleted"}, media_type="application/json")

@app.get("/contacts/search")
async def search_contacts(name: str = "", surname: str = "", email: str = ""):
    db = next(get_db())
    contacts = db.session.query(Contact).filter(
        (Contact.first_name.like('%' + name + '%')) |
        (Contact.last_name.like('%' + surname + '%')) |
        (Contact.email.like('%' + email + '%'))
    ).all()
    return JSONResponse(content={"contacts": [contact.__dict__ for contact in contacts]}, media_type="application/json")

@app.get("/contacts/upcoming_birthdays")
async def upcoming_birthdays():
    today = date.today()
    next_week = today + timedelta(days=7)
    db = next(get_db())
    contacts = db.session.query(Contact).filter(
        func.strftime('%m-%d', Contact.birthday) >= func.strftime('%m-%d', today),
        func.strftime('%m-%d', Contact.birthday) <= func.strftime('%m-%d', next_week)
    ).all()
    return JSONResponse(content={"contacts": [contact.__dict__ for contact in contacts]}, media_type="application/json")
