from datetime import datetime
from typing import Optional, List
import databases
import pydantic
import sqlalchemy
import timestamp as timestamp
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sqlalchemy import ForeignKey, create_engine, func, DateTime

DATABASE_URL = "sqlite:///mydatabase5.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

app = FastAPI()

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("first_name", sqlalchemy.String(32)),
    sqlalchemy.Column("last_name", sqlalchemy.String(32)),
    sqlalchemy.Column("email", sqlalchemy.String(128)),
    sqlalchemy.Column("password", sqlalchemy.String(25))
)

items = sqlalchemy.Table(
    "items",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String(32)),
    sqlalchemy.Column("description", sqlalchemy.String(1000), default="Описание отсутствует"),
    sqlalchemy.Column("price", sqlalchemy.DECIMAL)
)

orders = sqlalchemy.Table(
    "orders",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, ForeignKey('users.id')),
    sqlalchemy.Column("item_id", sqlalchemy.Integer, ForeignKey('items.id')),
    sqlalchemy.Column("status", sqlalchemy.String, default="active"),
    sqlalchemy.Column("created_at", DateTime(timezone=True), server_default=func.now())
)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata.create_all(engine)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


class UserCreate(BaseModel):
    first_name: str = Field(..., max_length=32)
    last_name: str = Field(..., max_length=32)
    email: pydantic.EmailStr | str = Field(default="email введен некорректно или не введен")
    password: str = pydantic.SecretStr


class User(UserCreate):
    id: int
    first_name: str = Field(..., max_length=32)
    last_name: str = Field(..., max_length=32)
    email: str = pydantic.EmailStr
    password: str = pydantic.SecretStr


class ItemCreate(BaseModel):
    name: str = Field(..., max_length=32)
    description: Optional[str] = Field("Описание отсутствует", max_length=1000)
    price: float


class Item(ItemCreate):
    id: int
    name: str = Field(..., max_length=32)
    description: Optional[str] = Field("Описание отсутствует", max_length=1000)
    price: float


class OrderCreate(BaseModel):
    user_id: int
    item_id: int
    status: Optional[str] = "active"
    created_at: Optional[datetime]


class Order(OrderCreate):
    id: int
    user_id: int
    item_id: int
    status: Optional[str] = "active"
    created_at: Optional[datetime]


@app.post("/users/", response_model=User)
async def create_user(user: UserCreate):
    query = users.insert().values(
        **user.dict())  # ЛУЧШЕ ИСПОЛЬЗОВАТЬ НЕ dict(), а user.model_dump, но я уже не успеваю переписать((
    last_record_id = await database.execute(query)  # model_dump - более современная версия dict()
    return {**user.dict(), "id": last_record_id}


@app.get("/users/", response_model=List[User])
async def read_users():
    query = users.select()
    return await database.fetch_all(query)


@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: int):
    query = users.select().where(users.c.id == user_id)
    return await database.fetch_one(query)


@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, new_user: UserCreate):
    query = users.update().where(users.c.id == user_id).values(**new_user.dict())
    await database.execute(query)
    return {**new_user.dict(), "id": user_id}


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    query = users.delete().where(users.c.id == user_id)
    await database.execute(query)
    return {'message': 'User deleted'}


@app.get("/users/", response_model=List[User])
async def read_users():
    query = users.select()
    return await database.fetch_all(query)


@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: int):
    query = users.select().where(users.c.id == user_id)
    return await database.fetch_one(query)


@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, new_user: UserCreate):
    query = users.update().where(users.c.id == user_id).values(**new_user.dict())
    await database.execute(query)
    return {**new_user.dict(), "id": user_id}


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    query = users.delete().where(users.c.id == user_id)
    await database.execute(query)
    return {'message': 'User deleted'}


@app.post("/items/", response_model=Item)
async def create_item(item: ItemCreate):
    query = items.insert().values(**item.dict())
    last_record_id = await database.execute(query)
    return {**item.dict(), "id": last_record_id}


@app.get("/items/", response_model=List[Item])
async def read_items():
    query = items.select()
    return await database.fetch_all(query)


@app.get("/items/{_id}", response_model=Item)
async def read_item(_id: int):
    query = items.select().where(items.c.id == _id)
    return await database.fetch_one(query)


@app.put("/items/{_id}", response_model=Item)
async def update_item(_id: int, new_item: ItemCreate):
    query = items.update().where(items.c.id == _id).values(**new_item.dict())
    await database.execute(query)
    return {**new_item.dict(), "id": _id}


@app.delete("/items/{_id}")
async def delete_item(_id: int):
    query = items.delete().where(items.c.id == _id)
    await database.execute(query)
    return {'message': 'Item deleted'}


@app.post("/orders/", response_model=Order)
async def create_order(order: OrderCreate):
    query = orders.insert().values(**order.dict())
    last_record_id = await database.execute(query)
    return {**order.dict(), "id": last_record_id}


@app.get("/orders/", response_model=list[Order])  # Так тоже можно, без typing.List
async def read_orders():
    query = orders.select()
    return await database.fetch_all(query)


@app.get("/orders/{_id}", response_model=Order)
async def read_order(_id: int):
    query = orders.select().where(orders.c.id == _id)
    return await database.fetch_one(query)


@app.put("/orders/{_id}", response_model=Order)
async def update_order(_id: int, _order: OrderCreate):
    query = orders.update().where(orders.c.id == _id).values(**_order.dict())
    await database.execute(query)
    return {**_order.dict(), "id": _id}


@app.delete("/orders/{_id}")
async def delete_order(_id: int):
    query = orders.delete().where(orders.c.id == _id)
    await database.execute(query)
    return {'message': 'Order deleted'}


if __name__ == "__main__":
    uvicorn.run("S6_HW:app", host='127.0.0.1', port=8000, reload=True)
