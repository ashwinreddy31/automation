from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:mom123@localhost:5432/postgres"

engine = create_engine(DATABASE_URL)

app = FastAPI()

# Request schema
class CustomerCreate(BaseModel):
    customer: str
    customer_age: int
    customer_id: int


# ------------------- CRUD (RAW SQL) -------------------

# ✅ CREATE
@app.post("/customers")
def create_customer(data: CustomerCreate):
    with engine.connect() as conn:
        query = text("""
            INSERT INTO ashwin (customer_id, customer, customer_age)
            VALUES (:customer_id, :customer, :customer_age)
            RETURNING customer_id, customer, customer_age
        """)
        result = conn.execute(query, {
            "customer_id": data.customer_id,
            "customer": data.customer,
            "customer_age": data.customer_age,
            
        })
        conn.commit()
        new_customer = result.fetchone()
        return dict(new_customer._mapping)


# ✅ READ ALL
@app.get("/customers")
def get_customers():
    with engine.connect() as conn:
        query = text("SELECT * FROM ashwin")
        result = conn.execute(query)
        return [dict(row._mapping) for row in result]


# ✅ READ ONE
@app.get("/customers/{id}")
def get_customer(id: int):
    with engine.connect() as conn:
        query = text("SELECT * FROM ashwin WHERE customer_id = :id")
        result = conn.execute(query, {"id": id}).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Customer not found")

        return dict(result._mapping)


# ✅ UPDATE
@app.put("/customers/{id}")
def update_customer(id: int, data: CustomerCreate):
    with engine.connect() as conn:
        query = text("""
            UPDATE ashwin
            SET customer = :customer,
                customer_age = :customer_age
            WHERE customer_id = :id
            RETURNING customer_id
        """)
        result = conn.execute(query, {
            "customer": data.customer,
            "customer_age": data.customer_age,
            "id": id
        })
        conn.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {"message": "Updated successfully"}


# ✅ DELETE
@app.delete("/customers/{id}")
def delete_customer(id: int):
    with engine.connect() as conn:
        query = text("DELETE FROM ashwin WHERE customer_id = :id")
        result = conn.execute(query, {"id": id})
        conn.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {"message": "Deleted successfully"}