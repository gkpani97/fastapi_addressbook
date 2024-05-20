from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float
from sqlalchemy.orm import sessionmaker
from math import sin, cos, sqrt, atan2, radians

SQLALCHEMY_DATABASE_URL = "sqlite:///db.sqlite3"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Address(Base):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

class AddressTransit(BaseModel):
    latitude: float
    longitude: float

class AddressList(BaseModel):
    data: list[AddressTransit] = []


@app.post("/postAddress/", response_model=AddressTransit, status_code=status.HTTP_200_OK)
def post_address(addr: AddressTransit, db: Session = Depends(get_db)):
    new_addr = Address(longitude = addr.longitude, latitude = addr.latitude)
    db.add(new_addr)
    db.commit()
    return new_addr

@app.put("/updateAddress/{id}", response_model=AddressTransit, status_code=status.HTTP_200_OK)
def update_address(id:int, updatedAddress: AddressTransit, db: Session = Depends(get_db)):
    addr = db.query(Address).filter(Address.id == id).first()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    addr.latitude = updatedAddress.latitude
    addr.longitude = updatedAddress.longitude
    db.add(addr)
    db.commit()
    return addr

@app.delete("/deleteAddress/{id}", status_code=status.HTTP_200_OK)
def delete_address(id:int, db: Session = Depends(get_db)):
    addr = db.query(Address).filter(Address.id == id).first()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(addr)
    db.commit()
    return

@app.get("/nearestAddresses/", status_code=status.HTTP_200_OK)
def find_nearest(id:int, radius=int, db: Session = Depends(get_db)):
    user_addr = db.query(Address).filter(Address.id == id).first()
    if not user_addr:
        raise HTTPException(status_code=404, detail="Address not found")
    
    user_coord = (user_addr.latitude, user_addr.longitude)

    addresses = db.query(Address).filter(Address.id != id)
    res = []

    for address in addresses:
        trgt_coord = (address.latitude, address.longitude)
        if dist_between(user_coord, trgt_coord) <= float(radius):
            res.append(AddressTransit(latitude=trgt_coord[0], longitude=trgt_coord[1]))
    
    return res

def dist_between(c1, c2):
    R = 6373.0

    lat1 = radians(c1[0])
    lon1 = radians(c1[1])
    lat2 = radians(c2[0])
    lon2 = radians(c2[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c