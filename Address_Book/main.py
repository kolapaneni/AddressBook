from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from geopy.distance import geodesic
import aiosqlite

app = FastAPI()


# Define Pydantic models
class Address(BaseModel):
    name: str
    latitude: float
    longitude: float


class AddressInDB(Address):
    id: int


# API routes
# Create a new address
@app.post("/addresses/", response_model=AddressInDB)
async def create_address(address: Address):
    async with aiosqlite.connect('address_book.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("INSERT INTO addresses (name, latitude, longitude) VALUES (?, ?, ?)",
                             (address.name, address.latitude, address.longitude))
        address_id = cursor.lastrowid
        await conn.commit()
        return {"id": address_id, **address.dict()}


# Update an existing address
@app.put("/addresses/{address_id}/", response_model=AddressInDB)
async def update_address(address_id: int, address: Address):
    async with aiosqlite.connect('address_book.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("UPDATE addresses SET name=?, latitude=?, longitude=? WHERE id=?",
                             (address.name, address.latitude, address.longitude, address_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Address not found")
        await conn.commit()
        return {"id": address_id, **address.dict()}


# Delete an address
@app.delete("/addresses/{address_id}/", response_model=dict)
async def delete_address(address_id: int):
    async with aiosqlite.connect('address_book.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("DELETE FROM addresses WHERE id=?", (address_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Address not found")
        await conn.commit()
        return {"message": "Address deleted successfully"}


# Get addresses, either all addresses or a single address by ID
@app.get("/addresses/", response_model=List[AddressInDB])
async def get_addresses(address_id: Optional[int] = None):
    async with aiosqlite.connect('address_book.db') as conn:
        cursor = await conn.cursor()
        if address_id is None:
            await cursor.execute("SELECT * FROM addresses")
        else:
            await cursor.execute("SELECT * FROM addresses WHERE id=?", (address_id,))
            address = await cursor.fetchone()
            if not address:
                raise HTTPException(status_code=404, detail="Address not found")
            addresses = [{"id": address[0], "name": address[1], "latitude": address[2], "longitude": address[3]}]
        return addresses


# Get nearby addresses based on given latitude, longitude, and distance
@app.get("/addresses/nearby/")
async def get_addresses_nearby(latitude: float, longitude: float, distance: Optional[float] = 1.0):
    async with aiosqlite.connect('address_book.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM addresses")
        addresses = [{"id": row[0], "name": row[1], "latitude": row[2], "longitude": row[3]} for row in await cursor.fetchall()]
        print(addresses)
        nearby_addresses = []
        for address in addresses:
            if geodesic((latitude, longitude), (address['latitude'], address['longitude'])).kilometers <= distance:
                nearby_addresses.append(address)
        return nearby_addresses
