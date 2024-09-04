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
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Products (
            ProductID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Description TEXT,
            Price REAL NOT NULL,
            Stock INTEGER NOT NULL
        );
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Orders (
            OrderID INTEGER PRIMARY KEY AUTOINCREMENT,
            CustomerID INTEGER NOT NULL,
            OrderDate DATE NOT NULL,
            TotalAmount REAL NOT NULL,
            ShippingAddress TEXT NOT NULL,
            City TEXT NOT NULL,
            State TEXT NOT NULL,
            ZipCode TEXT NOT NULL,
            Country TEXT NOT NULL,
            Status TEXT NOT NULL,
            PaymentStatus TEXT NOT NULL,
            FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
        );
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS OrderDetails (
            OrderDetailID INTEGER PRIMARY KEY AUTOINCREMENT,
            OrderID INTEGER NOT NULL,
            ProductID INTEGER NOT NULL,
            Quantity INTEGER NOT NULL,
            Price REAL NOT NULL,
            FOREIGN KEY (OrderID) REFERENCES Orders(OrderID),
            FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
        );
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Employees (
            EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT,
            FirstName TEXT NOT NULL,
            LastName TEXT NOT NULL,
            Email TEXT NOT NULL UNIQUE,
            Password TEXT NOT NULL,
            Role TEXT NOT NULL
        );
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Shipping (
            ShippingID INTEGER PRIMARY KEY AUTOINCREMENT,
            OrderID INTEGER NOT NULL,
            EmployeeID INTEGER NOT NULL,
            ShippingDate DATE NOT NULL,
            ShippingMethod TEXT NOT NULL,
            TrackingNumber TEXT NOT NULL,
            FOREIGN KEY (OrderID) REFERENCES Orders(OrderID),
            FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
        );
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS InventoryLog (
            LogID INTEGER PRIMARY KEY AUTOINCREMENT,
            ProductID INTEGER NOT NULL,
            EmployeeID INTEGER NOT NULL,
            ChangeType TEXT NOT NULL,
            QuantityChange INTEGER NOT NULL,
            ChangeDate DATE NOT NULL,
            FOREIGN KEY (ProductID) REFERENCES Products(ProductID),
            FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
        );
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Payments (
            PaymentID INTEGER PRIMARY KEY AUTOINCREMENT,
            OrderID INTEGER NOT NULL,
            Amount REAL NOT NULL,
            PaymentDate DATE NOT NULL,
            PaymentMethod TEXT NOT NULL,
            FOREIGN KEY (OrderID) REFERENCES Orders(OrderID)
        );
    ''')
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


@app.post("/products", response_model=Product)
def create_product(product: Product, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO Products (Name, Description, Price, Stock) VALUES (?, ?, ?, ?)',
        (product.Name, product.Description, product.Price, product.Stock)
    )
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    return {**product.dict(), "ProductID": product_id}

@app.get("/products", response_model=List[Product])
def read_products(
    employee: dict = Depends(authenticate),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=3)
):
    conn = get_db_connection()
    query = 'SELECT * FROM Products'
    params = []
    if search:
        query += ' WHERE Name LIKE ? OR Description LIKE ?'
        search_param = f'%{search}%'
        params = [search_param, search_param]
    query += ' LIMIT ? OFFSET ?'
    params.extend([limit, skip])
    products = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(product) for product in products]


@app.get("/products/{product_id}", response_model=Product)
def read_product(product_id: int, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM Products WHERE ProductID = ?', (product_id,)).fetchone()
    conn.close()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(product)

@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, product: Product, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE Products SET Name = ?, Description = ?, Price = ?, Stock = ? WHERE ProductID = ?',
        (product.Name, product.Description, product.Price, product.Stock, product_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")
    conn.commit()
    conn.close()
    return {**product.dict(), "ProductID": product_id}

@app.delete("/products/{product_id}")
def delete_product(product_id: int, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Products WHERE ProductID = ?', (product_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")
    conn.commit()
    conn.close()
    return {"message": "Product deleted successfully"}

# CRUD Operations for Orders
@app.post("/orders", response_model=Order)
def create_order(order: Order, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO Orders (CustomerID, OrderDate, TotalAmount, ShippingAddress, City, State, ZipCode, Country, Status, PaymentStatus) '
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (order.CustomerID, order.OrderDate, order.TotalAmount, order.ShippingAddress, order.City, order.State, order.ZipCode, order.Country, order.Status, order.PaymentStatus)
    )
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    return {**order.dict(), "OrderID": order_id}

@app.get("/orders", response_model=List[Order])
def read_orders(
    employee: dict = Depends(authenticate),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    customer_id: Optional[int] = Query(None)
):
    conn = get_db_connection()
    query = 'SELECT * FROM Orders'
    params = []
    if customer_id is not None:
        query += ' WHERE CustomerID = ?'
        params.append(customer_id)
    query += ' LIMIT ? OFFSET ?'
    params.extend([limit, skip])
    orders = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(order) for order in orders]

@app.get("/orders/{order_id}", response_model=Order)
def read_order(order_id: int, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM Orders WHERE OrderID = ?', (order_id,)).fetchone()
    conn.close()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return dict(order)

@app.put("/orders/{order_id}", response_model=Order)
def update_order(order_id: int, order: Order, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE Orders SET CustomerID = ?, OrderDate = ?, TotalAmount = ?, ShippingAddress = ?, City = ?, State = ?, ZipCode = ?, Country = ?, Status = ?, PaymentStatus = ? '
        'WHERE OrderID = ?',
        (order.CustomerID, order.OrderDate, order.TotalAmount, order.ShippingAddress, order.City, order.State, order.ZipCode, order.Country, order.Status, order.PaymentStatus, order_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Order not found")
    conn.commit()
    conn.close()
    return {**order.dict(), "OrderID": order_id}

@app.delete("/orders/{order_id}")
def delete_order(order_id: int, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Orders WHERE OrderID = ?', (order_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Order not found")
    conn.commit()
    conn.close()
    return {"message": "Order deleted successfully"}

# CRUD Operations for Order Details
@app.post("/order-details", response_model=OrderDetail)
def create_order_detail(order_detail: OrderDetail, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO OrderDetails (OrderID, ProductID, Quantity, Price) VALUES (?, ?, ?, ?)',
        (order_detail.OrderID, order_detail.ProductID, order_detail.Quantity, order_detail.Price)
    )
    conn.commit()
    order_detail_id = cursor.lastrowid
    conn.close()
    return {**order_detail.dict(), "OrderDetailID": order_detail_id}

@app.get("/order-details", response_model=List[OrderDetail])
def read_order_details(
    employee: dict = Depends(authenticate),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    order_id: Optional[int] = Query(None)
):
    conn = get_db_connection()
    query = 'SELECT * FROM OrderDetails'
    params = []
    if order_id is not None:
        query += ' WHERE OrderID = ?'
        params.append(order_id)
    query += ' LIMIT ? OFFSET ?'
    params.extend([limit, skip])
    order_details = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(order_detail) for order_detail in order_details]

@app.get("/order-details/{order_detail_id}", response_model=OrderDetail)
def read_order_detail(order_detail_id: int, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    order_detail = conn.execute('SELECT * FROM OrderDetails WHERE OrderDetailID = ?', (order_detail_id,)).fetchone()
    conn.close()
    if not order_detail:
        raise HTTPException(status_code=404, detail="Order Detail not found")
    return dict(order_detail)

@app.put("/order-details/{order_detail_id}", response_model=OrderDetail)
def update_order_detail(order_detail_id: int, order_detail: OrderDetail, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE OrderDetails SET OrderID = ?, ProductID = ?, Quantity = ?, Price = ? WHERE OrderDetailID = ?',
        (order_detail.OrderID, order_detail.ProductID, order_detail.Quantity, order_detail.Price, order_detail_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Order Detail not found")
    conn.commit()
    conn.close()
    return {**order_detail.dict(), "OrderDetailID": order_detail_id}

@app.delete("/order-details/{order_detail_id}")
def delete_order_detail(order_detail_id: int, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM OrderDetails WHERE OrderDetailID = ?', (order_detail_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Order Detail not found")
    conn.commit()
    conn.close()
    return {"message": "Order Detail deleted successfully"}

# CRUD Operations for Employees
@app.post("/employees", response_model=Employee)
def create_employee(employee: Employee, current_employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO Employees (FirstName, LastName, Email, Password, Role) VALUES (?, ?, ?, ?, ?)',
        (employee.FirstName, employee.LastName, employee.Email, employee.Password, employee.Role)
    )
    conn.commit()
    employee_id = cursor.lastrowid
    conn.close()
    return {**employee.dict(), "EmployeeID": employee_id}

@app.get("/employees", response_model=List[Employee])
def read_employees(
    current_employee: dict = Depends(authenticate),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    conn = get_db_connection()
    query = 'SELECT * FROM Employees LIMIT ? OFFSET ?'
    employees = conn.execute(query, (limit, skip)).fetchall()
    conn.close()
    return [dict(employee) for employee in employees]

@app.get("/employees/{employee_id}", response_model=Employee)
def read_employee(employee_id: int, current_employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    employee = conn.execute('SELECT * FROM Employees WHERE EmployeeID = ?', (employee_id,)).fetchone()
    conn.close()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return dict(employee)

@app.put("/employees/{employee_id}", response_model=Employee)
def update_employee(employee_id: int, employee: Employee, current_employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE Employees SET FirstName = ?, LastName = ?, Email = ?, Password = ?, Role = ? WHERE EmployeeID = ?',
        (employee.FirstName, employee.LastName, employee.Email, employee.Password, employee.Role, employee_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Employee not found")
    conn.commit()
    conn.close()
    return {**employee.dict(), "EmployeeID": employee_id}

@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, current_employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Employees WHERE EmployeeID = ?', (employee_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Employee not found")
    conn.commit()
    conn.close()
    return {"message": "Employee deleted successfully"}

# CRUD Operations for Shipping
@app.post("/shipping", response_model=Shipping)
def create_shipping(shipping: Shipping, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO Shipping (OrderID, EmployeeID, ShippingDate, ShippingMethod, TrackingNumber) VALUES (?, ?, ?, ?, ?)',
        (shipping.OrderID, shipping.EmployeeID, shipping.ShippingDate, shipping.ShippingMethod, shipping.TrackingNumber)
    )
    conn.commit()
    shipping_id = cursor.lastrowid
    conn.close()
    return {**shipping.dict(), "ShippingID": shipping_id}

@app.get("/shipping", response_model=List[Shipping])
def read_shipping(
    employee: dict = Depends(authenticate),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    order_id: Optional[int] = Query(None)
):
    conn = get_db_connection()
    query = 'SELECT * FROM Shipping'
    params = []
    if order_id is not None:
        query += ' WHERE OrderID = ?'
        params.append(order_id)
    query += ' LIMIT ? OFFSET ?'
    params.extend([limit, skip])
    shipping_records = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(shipping) for shipping in shipping_records]

@app.get("/shipping/{shipping_id}", response_model=Shipping)
def read_shipping_record(shipping_id: int, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    shipping = conn.execute('SELECT * FROM Shipping WHERE ShippingID = ?', (shipping_id,)).fetchone()
    conn.close()
    if not shipping:
        raise HTTPException(status_code=404, detail="Shipping record not found")
    return dict(shipping)

@app.put("/shipping/{shipping_id}", response_model=Shipping)
def update_shipping(shipping_id: int, shipping: Shipping, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE Shipping SET OrderID = ?, EmployeeID = ?, ShippingDate = ?, ShippingMethod = ?, TrackingNumber = ? WHERE ShippingID = ?',
        (shipping.OrderID, shipping.EmployeeID, shipping.ShippingDate, shipping.ShippingMethod, shipping.TrackingNumber, shipping_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Shipping record not found")
    conn.commit()
    conn.close()
    return {**shipping.dict(), "ShippingID": shipping_id}

@app.delete("/shipping/{shipping_id}")
def delete_shipping(shipping_id: int, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Shipping WHERE ShippingID = ?', (shipping_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Shipping record not found")
    conn.commit()
    conn.close()
    return {"message": "Shipping record deleted successfully"}

# CRUD Operations for Inventory Log
@app.post("/inventory-log", response_model=InventoryLog)
def create_inventory_log(inventory_log: InventoryLog, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO InventoryLog (ProductID, EmployeeID, ChangeType, QuantityChange, ChangeDate) VALUES (?, ?, ?, ?, ?)',
        (inventory_log.ProductID, inventory_log.EmployeeID, inventory_log.ChangeType, inventory_log.QuantityChange, inventory_log.ChangeDate)
    )
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return {**inventory_log.dict(), "LogID": log_id}

@app.get("/inventory-log", response_model=List[InventoryLog])
def read_inventory_logs(
    employee: dict = Depends(authenticate),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    product_id: Optional[int] = Query(None)
):
    conn = get_db_connection()
    query = 'SELECT * FROM InventoryLog'
    params = []
    if product_id is not None:
        query += ' WHERE ProductID = ?'
        params.append(product_id)
    query += ' LIMIT ? OFFSET ?'
    params.extend([limit, skip])
    inventory_logs = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(log) for log in inventory_logs]

@app.get("/inventory-log/{log_id}", response_model=InventoryLog)
def read_inventory_log(log_id: int, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    log = conn.execute('SELECT * FROM InventoryLog WHERE LogID = ?', (log_id,)).fetchone()
    conn.close()
    if not log:
        raise HTTPException(status_code=404, detail="Inventory Log not found")
    return dict(log)

@app.put("/inventory-log/{log_id}", response_model=InventoryLog)
def update_inventory_log(log_id: int, inventory_log: InventoryLog, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE InventoryLog SET ProductID = ?, EmployeeID = ?, ChangeType = ?, QuantityChange = ?, ChangeDate = ? WHERE LogID = ?',
        (inventory_log.ProductID, inventory_log.EmployeeID, inventory_log.ChangeType, inventory_log.QuantityChange, inventory_log.ChangeDate, log_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Inventory Log not found")
    conn.commit()
    conn.close()
    return {**inventory_log.dict(), "LogID": log_id}

@app.delete("/inventory-log/{log_id}")
def delete_inventory_log(log_id: int, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM InventoryLog WHERE LogID = ?', (log_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Inventory Log not found")
    conn.commit()
    conn.close()
    return {"message": "Inventory Log deleted successfully"}

# CRUD Operations for Payments
@app.post("/payments", response_model=Payment)
def create_payment(payment: Payment, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO Payments (OrderID, Amount, PaymentDate, PaymentMethod) VALUES (?, ?, ?, ?)',
        (payment.OrderID, payment.Amount, payment.PaymentDate, payment.PaymentMethod)
    )
    conn.commit()
    payment_id = cursor.lastrowid
    conn.close()
    return {**payment.dict(), "PaymentID": payment_id}

@app.get("/payments", response_model=List[Payment])
def read_payments(
    employee: dict = Depends(authenticate),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    order_id: Optional[int] = Query(None)
):
    conn = get_db_connection()
    query = 'SELECT * FROM Payments'
    params = []
    if order_id is not None:
        query += ' WHERE OrderID = ?'
        params.append(order_id)
    query += ' LIMIT ? OFFSET ?'
    params.extend([limit, skip])
    payments = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(payment) for payment in payments]

@app.get("/payments/{payment_id}", response_model=Payment)
def read_payment(payment_id: int, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    payment = conn.execute('SELECT * FROM Payments WHERE PaymentID = ?', (payment_id,)).fetchone()
    conn.close()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return dict(payment)

@app.put("/payments/{payment_id}", response_model=Payment)
def update_payment(payment_id: int, payment: Payment, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE Payments SET OrderID = ?, Amount = ?, PaymentDate = ?, PaymentMethod = ? WHERE PaymentID = ?',
        (payment.OrderID, payment.Amount, payment.PaymentDate, payment.PaymentMethod, payment_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Payment not found")
    conn.commit()
    conn.close()
    return {**payment.dict(), "PaymentID": payment_id}

@app.delete("/payments/{payment_id}")
def delete_payment(payment_id: int, employee: dict = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Payments WHERE PaymentID = ?', (payment_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Payment not found")
    conn.commit()
    conn.close()
    return {"message": "Payment deleted successfully"}

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