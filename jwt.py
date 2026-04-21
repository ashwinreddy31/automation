from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, text
from jose import jwt, JWTError
from datetime import datetime, timedelta
from pydantic import BaseModel

# ---------------- DB ----------------
DATABASE_URL = "postgresql://postgres:mom123@localhost:5432/postgres"
engine = create_engine(DATABASE_URL)

# ---------------- APP ----------------
app = FastAPI()

# ---------------- JWT CONFIG ----------------
SECRET_KEY = "mysecretkey123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ---------------- SCHEMA ----------------
class CustomerCreate(BaseModel):
    customer_id: int
    customer: str
    customer_age: int


# ---------------- JWT CREATE ----------------
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ---------------- VERIFY TOKEN ----------------
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        customer_id = payload.get("customer_id")

        if customer_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return customer_id

    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")


# ---------------- LOGIN (FIXED PROPER WAY) ----------------
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with engine.connect() as conn:

        query = text("""
            SELECT * FROM ashwin
            WHERE customer_id = :id AND customer = :name
        """)

        result = conn.execute(query, {
            "id": int(form_data.username),   # username used as customer_id
            "name": form_data.password       # password used as customer name (demo only)
        }).fetchone()

        if not result:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token(
            data={"customer_id": result.customer_id},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {
            "access_token": token,
            "token_type": "bearer"
        }


# ---------------- CREATE ----------------
@app.post("/customers")
def create_customer(data: CustomerCreate, user_id: int = Depends(verify_token)):
    with engine.connect() as conn:
        query = text("""
            INSERT INTO ashwin (customer_id, customer, customer_age)
            VALUES (:customer_id, :customer, :customer_age)
            RETURNING customer_id, customer, customer_age
        """)

        result = conn.execute(query, {
            "customer_id": data.customer_id,
            "customer": data.customer,
            "customer_age": data.customer_age
        })

        conn.commit()
        return dict(result.fetchone()._mapping)


# ---------------- READ ALL ----------------
@app.get("/customers")
def get_customers(user_id: int = Depends(verify_token)):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM ashwin"))
        return [dict(row._mapping) for row in result]


# ---------------- READ ONE ----------------
@app.get("/customers/{id}")
def get_customer(id: int, user_id: int = Depends(verify_token)):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM ashwin WHERE customer_id = :id"),
            {"id": id}
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Customer not found")

        return dict(result._mapping)


# ---------------- UPDATE ----------------
@app.put("/customers/{id}")
def update_customer(id: int, data: CustomerCreate, user_id: int = Depends(verify_token)):
    with engine.connect() as conn:
        result = conn.execute(text("""
            UPDATE ashwin
            SET customer = :customer,
                customer_age = :customer_age
            WHERE customer_id = :id
        """), {
            "customer": data.customer,
            "customer_age": data.customer_age,
            "id": id
        })

        conn.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {"message": "Updated successfully"}


# ---------------- DELETE ----------------
@app.delete("/customers/{id}")
def delete_customer(id: int, user_id: int = Depends(verify_token)):
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM ashwin WHERE customer_id = :id"),
            {"id": id}
        )

        conn.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {"message": "Deleted successfully"}