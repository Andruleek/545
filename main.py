from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Конфігурація бази даних
SQLALCHEMY_DATABASE_URL = "sqlite:///contacts.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Декларативна база даних
Base = declarative_base()

# Модель контакту
class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    phone = Column(String)
    birthday = Column(String)
    additional_data = Column(String)

# Клас для роботи з сесією
class ContactDB:
    def __init__(self, session):
        self.session = session

    def create_contact(self, contact: Contact):
        self.session.add(contact)
        self.session.commit()

    def get_contacts(self):
        return self.session.query(Contact).all()

    def get_contact(self, contact_id: int):
        return self.session.query(Contact).filter(Contact.id == contact_id).first()

    def update_contact(self, contact_id: int, contact: Contact):
        contact_to_update = self.get_contact(contact_id)
        if contact_to_update is None:
            raise HTTPException(status_code=404, detail="Contact not found")
        contact_to_update.first_name = contact.first_name
        contact_to_update.last_name = contact.last_name
        contact_to_update.email = contact.email
        contact_to_update.phone = contact.phone
        contact_to_update.birthday = contact.birthday
        contact_to_update.additional_data = contact.additional_data
        self.session.commit()

    def delete_contact(self, contact_id: int):
        contact_to_delete = self.get_contact(contact_id)
        if contact_to_delete is None:
            raise HTTPException(status_code=404, detail="Contact not found")
        self.session.delete(contact_to_delete)
        self.session.commit()

# Функція для створення сесії
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

# Роут для створення контакту
@app.post("/contacts")
async def create_contact(contact: Contact):
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

# Роут для відображення списку контактів
@app.get("/contacts")
async def get_contacts():
    db = next(get_db())
    contacts = db.get_contacts()
    return JSONResponse(content={"contacts": [contact.__dict__ for contact in contacts]}, media_type="application/json")

# Роут для відображення контакту за ідентифікатором
@app.get("/contacts/{contact_id}")
async def get_contact(contact_id: int):
    db = next(get_db())
    contact = db.get_contact(contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return JSONResponse(content={"contact": contact.__dict__}, media_type="application/json")

# Роут для оновлення контакту
@app.put("/contacts/{contact_id}")
async def update_contact(contact_id: int, contact: Contact):
    db = next(get_db())
    db.update_contact(contact_id, contact)
    return JSONResponse(content={"message": "Contact updated"}, media_type="application/json")

# Роут для відображення всіх контактів
@app.get("/contacts/all")
async def get_all_contacts():
    db = next(get_db())
    contacts = db.get_contacts()
    return JSONResponse(content={"contacts": [contact.__dict__ for contact in contacts]}, media_type="application/json")

# Роут для видалення контакту
@app.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: int):
    db = next(get_db())
    db.delete_contact(contact_id)
    return JSONResponse(content={"message": "Contact deleted"}, media_type="application/json")

@app.route('/contacts/search', methods=['GET'])
def search_contacts():
    name = request.args.get('name')
    surname = request.args.get('surname')
    email = request.args.get('email')

    contacts = Contact.query.filter(
        (Contact.name.like('%' + name + '%')) |
        (Contact.surname.like('%' + surname + '%')) |
        (Contact.email.like('%' + email + '%'))
    ).all()

    return jsonify([contact.json() for contact in contacts])

from datetime import date, timedelta

@app.route('/contacts/upcoming_birthdays', methods=['GET'])
def upcoming_birthdays():
    today = date.today()
    next_week = today + timedelta(days=7)

    contacts = Contact.query.filter(
        Contact.birthday >= today,
        Contact.birthday <= next_week
    ).all()

    return jsonify([contact.json() for contact in contacts])

