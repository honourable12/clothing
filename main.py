from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import sqlite3
from datetime import datetime, date
import secrets

app = FastAPI(title="Clothing Business Management API")
security = HTTPBasic()

DATABASE = 'clothing_business.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Enhanced Model Definitions
class Customer(BaseModel):
    CustomerID: Optional[int] = None
    FirstName: str = Field(..., min_length=1, max_length=50)
    LastName: str = Field(..., min_length=1, max_length=50)
    Email: EmailStr
    PhoneNumber: str = Field(..., pattern="^\\+?\\d{10,14}$")

class Product(BaseModel):
    ProductID: Optional[int] = None
    Name: str = Field(..., min_length=1, max_length=100)
    Description: str = Field(..., min_length=1, max_length=500)
    Price: float = Field(..., gt=0)
    Stock: int = Field(..., ge=0)

class Order(BaseModel):
    OrderID: Optional[int] = None
    CustomerID: int
    OrderDate: date
    TotalAmount: float = Field(..., gt=0)
    ShippingAddress: str
    City: str
    State: str
    ZipCode: str
    Country: str
    Status: str = Field(..., pattern="^(Pending|Processing|Shipped|Delivered|Cancelled)$")
    PaymentStatus: str = Field(..., pattern="^(Pending|Paid|Refunded)$")

class OrderDetail(BaseModel):
    OrderDetailID: Optional[int] = None
    OrderID: int
    ProductID: int
    Quantity: int = Field(..., gt=0)
    Price: float = Field(..., gt=0)

class Employee(BaseModel):
    EmployeeID: Optional[int] = None
    FirstName: str = Field(..., min_length=1, max_length=50)
    LastName: str = Field(..., min_length=1, max_length=50)
    Email: EmailStr
    Password: str = Field(..., min_length=8)
    Role: str = Field(..., pattern="^(Admin|Manager|Staff)$")

class Shipping(BaseModel):
    ShippingID: Optional[int] = None
    OrderID: int
    EmployeeID: int
    ShippingDate: date
    ShippingMethod: str
    TrackingNumber: str

class InventoryLog(BaseModel):
    LogID: Optional[int] = None
    ProductID: int
    EmployeeID: int
    ChangeType: str = Field(..., pattern="^(Restock|Sale|Return|Adjustment)$")
    QuantityChange: int
    ChangeDate: date

class Payment(BaseModel):
    PaymentID: Optional[int] = None
    OrderID: int
    Amount: float = Field(..., gt=0)
    PaymentDate: date
    PaymentMethod: str = Field(..., pattern="^(Credit Card|Debit Card|PayPal|Bank Transfer)$")

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    conn = get_db_connection()
    employee = conn.execute('SELECT * FROM Employees WHERE Email = ?', (credentials.username,)).fetchone()
    conn.close()
    if employee and secrets.compare_digest(employee['Password'], credentials.password):
        return dict(employee)
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/login")
def login(employee: dict = Depends(authenticate)):
    return {"message": "Login successful", "employee": employee}

# Create Tables
def create_tables():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Customers (
            CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
            FirstName TEXT NOT NULL,
            LastName TEXT NOT NULL,
            Email TEXT NOT NULL UNIQUE,
            PhoneNumber TEXT NOT NULL
        );
    ''')
    # ... (rest of the table creation statements)
    conn.commit()
    conn.close()

create_tables()

def create_default_admin():
    conn = get_db_connection()
    admin = conn.execute('SELECT * FROM Employees WHERE Role = "Admin"').fetchone()
    if not admin:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO Employees (FirstName, LastName, Email, Password, Role) '
            'VALUES (?, ?, ?, ?, ?)',
            ('Admin', 'User', 'admin@example.com', 'adminpassword', 'Admin')
        )
        conn.commit()
    conn.close()

create_default_admin()

# Enhanced CRUD operations with pagination and search
@app.post("/customers", response_model=Customer)
def create_customer(customer: Customer, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO Customers (FirstName, LastName, Email, PhoneNumber) '
            'VALUES (?, ?, ?, ?)',
            (customer.FirstName, customer.LastName, customer.Email, customer.PhoneNumber)
        )
        conn.commit()
        customer_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already exists")
    conn.close()
    return {**customer.dict(), "CustomerID": customer_id}

@app.get("/customers", response_model=List[Customer])
def read_customers(
    employee: dict = Depends(authenticate),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=3)
):
    conn = get_db_connection()
    query = 'SELECT * FROM Customers'
    params = []
    if search:
        query += ' WHERE FirstName LIKE ? OR LastName LIKE ? OR Email LIKE ?'
        search_param = f'%{search}%'
        params = [search_param, search_param, search_param]
    query += ' LIMIT ? OFFSET ?'
    params.extend([limit, skip])
    customers = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(customer) for customer in customers]

# ... (rest of the CRUD operations for other models)

# Additional features

@app.get("/dashboard")
def get_dashboard_data(employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    total_customers = conn.execute('SELECT COUNT(*) FROM Customers').fetchone()[0]
    total_products = conn.execute('SELECT COUNT(*) FROM Products').fetchone()[0]
    total_orders = conn.execute('SELECT COUNT(*) FROM Orders').fetchone()[0]
    total_revenue = conn.execute('SELECT SUM(TotalAmount) FROM Orders').fetchone()[0] or 0
    conn.close()
    return {
        "total_customers": total_customers,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": total_revenue
    }

@app.get("/best-selling-products")
def get_best_selling_products(
    employee: dict = Depends(authenticate),
    limit: int = Query(5, ge=1, le=20)
):
    conn = get_db_connection()
    query = '''
    SELECT p.ProductID, p.Name, SUM(od.Quantity) as TotalSold
    FROM Products p
    JOIN OrderDetails od ON p.ProductID = od.ProductID
    GROUP BY p.ProductID
    ORDER BY TotalSold DESC
    LIMIT ?
    '''
    best_sellers = conn.execute(query, (limit,)).fetchall()
    conn.close()
    return [dict(product) for product in best_sellers]

@app.get("/revenue-by-month")
def get_revenue_by_month(
    employee: dict = Depends(authenticate),
    year: int = Query(default=datetime.now().year, ge=2000, le=datetime.now().year)
):
    conn = get_db_connection()
    query = '''
    SELECT strftime('%m', OrderDate) as Month, SUM(TotalAmount) as Revenue
    FROM Orders
    WHERE strftime('%Y', OrderDate) = ?
    GROUP BY Month
    ORDER BY Month
    '''
    monthly_revenue = conn.execute(query, (str(year),)).fetchall()
    conn.close()
    return [dict(row) for row in monthly_revenue]

@app.put("/update-stock/{product_id}")
def update_stock(
    product_id: int,
    quantity_change: int,
    employee: dict = Depends(authenticate)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('BEGIN TRANSACTION')
        cursor.execute('UPDATE Products SET Stock = Stock + ? WHERE ProductID = ?', (quantity_change, product_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        cursor.execute(
            'INSERT INTO InventoryLog (ProductID, EmployeeID, ChangeType, QuantityChange, ChangeDate) '
            'VALUES (?, ?, ?, ?, ?)',
            (product_id, employee['EmployeeID'], 'Adjustment', quantity_change, date.today())
        )
        cursor.execute('COMMIT')
    except Exception as e:
        cursor.execute('ROLLBACK')
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    return {"message": "Stock updated successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.1", port=8000, reload=True)