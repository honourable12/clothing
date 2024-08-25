from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import sqlite3

app = FastAPI()

DATABASE = 'clothing_business.db'


# Database connection
def get_db_connection():
  conn = sqlite3.connect(DATABASE)
  conn.row_factory = sqlite3.Row
  return conn


# Model Definitions
class Customer(BaseModel):
  CustomerID: Optional[int]
  FirstName: str
  LastName: str
  Email: str
  PhoneNumber: str


class Product(BaseModel):
  ProductID: Optional[int]
  Name: str
  Description: str
  Price: float
  Stock: int


class Order(BaseModel):
  OrderID: Optional[int]
  CustomerID: int
  OrderDate: str
  TotalAmount: float
  ShippingAddress: str
  City: str
  State: str
  ZipCode: str
  Country: str
  Status: str
  PaymentStatus: str


class OrderDetail(BaseModel):
  OrderDetailID: Optional[int]
  OrderID: int
  ProductID: int
  Quantity: int
  Price: float


class Employee(BaseModel):
  EmployeeID: Optional[int]
  FirstName: str
  LastName: str
  Email: str
  Password: str
  Role: str


class Shipping(BaseModel):
  ShippingID: Optional[int]
  OrderID: int
  EmployeeID: int
  ShippingDate: str
  ShippingMethod: str
  TrackingNumber: str


class InventoryLog(BaseModel):
  LogID: Optional[int]
  ProductID: int
  EmployeeID: int
  ChangeType: str
  QuantityChange: int
  ChangeDate: str


class Payment(BaseModel):
  PaymentID: Optional[int]
  OrderID: int
  Amount: float
  PaymentDate: str
  PaymentStatus: str


def authenticate(username: str = "admin", password: str = "admin"):
  conn = get_db_connection()
  employee = conn.execute('SELECT * FROM Employees WHERE Email = ? AND Password = ?', (username, password)).fetchone()
  conn.close()
  if employee:
    return dict(employee)
  else:
    raise HTTPException(status_code=401, detail="Unauthorized")


# Create Tables
def create_tables():
  conn = get_db_connection()
  conn.execute('''
    CREATE TABLE IF NOT EXISTS Customers (
        CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
        FirstName TEXT NOT NULL,
        LastName TEXT NOT NULL,
        Email TEXT NOT NULL,
        PhoneNumber TEXT NOT NULL
    );
    ''')
  conn.execute('''
    CREATE TABLE IF NOT EXISTS Products (
        ProductID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Description TEXT NOT NULL,
        Price REAL NOT NULL,
        Stock INTEGER NOT NULL
    );
    ''')
  conn.execute('''
    CREATE TABLE IF NOT EXISTS Orders (
        OrderID INTEGER PRIMARY KEY AUTOINCREMENT,
        CustomerID INTEGER NOT NULL,
        OrderDate TEXT NOT NULL,
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
        Email TEXT UNIQUE NOT NULL,
        Password TEXT NOT NULL,
        Role TEXT NOT NULL
    );
    ''')
  conn.execute('''
    CREATE TABLE IF NOT EXISTS Shipping (
        ShippingID INTEGER PRIMARY KEY AUTOINCREMENT,
        OrderID INTEGER NOT NULL,
        EmployeeID INTEGER NOT NULL,
        ShippingDate TEXT NOT NULL,
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
        ChangeDate TEXT NOT NULL,
        FOREIGN KEY (ProductID) REFERENCES Products(ProductID),
        FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
    );
    ''')
  conn.execute('''
    CREATE TABLE IF NOT EXISTS Payments (
        PaymentID INTEGER PRIMARY KEY AUTOINCREMENT,
        OrderID INTEGER NOT NULL,
        Amount REAL NOT NULL,
        PaymentDate TEXT NOT NULL,
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


# Secured CRUD operations for Customers
@app.post("/customers", response_model=Customer)
def create_customer(customer: Customer):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'INSERT INTO Customers (FirstName, LastName, Email, PhoneNumber) '
    'VALUES (?, ?, ?, ?)',
    (customer.FirstName, customer.LastName, customer.Email, customer.PhoneNumber)
  )
  conn.commit()
  customer_id = cursor.lastrowid
  conn.close()
  return {**customer.model_dump(), "CustomerID": customer_id}


@app.get("/customers", response_model=List[Customer])
def read_customers(username: str = Depends(authenticate)):
  conn = get_db_connection()
  customers = conn.execute('SELECT * FROM Customers').fetchall()
  conn.close()
  return [dict(customer) for customer in customers]


@app.get("/customers/{customer_id}", response_model=Customer)
def read_customer(customer_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  customer = conn.execute('SELECT * FROM Customers WHERE CustomerID = ?', (customer_id,)).fetchone()
  conn.close()
  if customer is None:
    raise HTTPException(status_code=404, detail="Customer not found")
  return dict(customer)


@app.put("/customers/{customer_id}", response_model=Customer)
def update_customer(customer_id: int, customer: Customer, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'UPDATE Customers SET FirstName = ?, LastName = ?, Email = ?, PhoneNumber = ? '
    'WHERE CustomerID = ?',
    (customer.FirstName, customer.LastName, customer.Email, customer.PhoneNumber, customer_id)
  )
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Customer not found")
  conn.close()
  return {**customer.dict(), "CustomerID": customer_id}


@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('DELETE FROM Customers WHERE CustomerID = ?', (customer_id,))
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Customer not found")
  conn.close()
  return {"detail": "Customer deleted successfully"}


# Secured CRUD operations for Products
@app.post("/products", response_model=Product)
def create_product(product: Product, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'INSERT INTO Products (Name, Description, Price, Stock) '
    'VALUES (?, ?, ?, ?)',
    (product.Name, product.Description, product.Price, product.Stock)
  )
  conn.commit()
  product_id = cursor.lastrowid
  conn.close()
  return {**product.dict(), "ProductID": product_id}


@app.get("/products", response_model=List[Product])
def read_products(username: str = Depends(authenticate)):
  conn = get_db_connection()
  products = conn.execute('SELECT * FROM Products').fetchall()
  conn.close()
  return [dict(product) for product in products]


@app.get("/products/{product_id}", response_model=Product)
def read_product(product_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  product = conn.execute('SELECT * FROM Products WHERE ProductID = ?', (product_id,)).fetchone()
  conn.close()
  if product is None:
    raise HTTPException(status_code=404, detail="Product not found")
  return dict(product)


@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, product: Product, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'UPDATE Products SET Name = ?, Description = ?, Price = ?, Stock = ? '
    'WHERE ProductID = ?',
    (product.Name, product.Description, product.Price, product.Stock, product_id)
  )
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Product not found")
  conn.close()
  return {**product.model_dump(), "ProductID": product_id}


@app.delete("/products/{product_id}")
def delete_product(product_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('DELETE FROM Products WHERE ProductID = ?', (product_id,))
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Product not found")
  conn.close()
  return {"detail": "Product deleted successfully"}


# Secured CRUD operations for Orders
@app.post("/orders", response_model=Order)
def create_order(order: Order, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'INSERT INTO Orders (CustomerID, OrderDate, TotalAmount, ShippingAddress, City, State, ZipCode, Country, Status, PaymentStatus) '
    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
    (
    order.CustomerID, order.OrderDate, order.TotalAmount, order.ShippingAddress, order.City, order.State, order.ZipCode,
    order.Country, order.Status, order.PaymentStatus)
  )
  conn.commit()
  order_id = cursor.lastrowid
  conn.close()
  return {**order.dict(), "OrderID": order_id}


@app.get("/orders", response_model=List[Order])
def read_orders(username: str = Depends(authenticate)):
  conn = get_db_connection()
  orders = conn.execute('SELECT * FROM Orders').fetchall()
  conn.close()
  return [dict(order) for order in orders]


@app.get("/orders/{order_id}", response_model=Order)
def read_order(order_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  order = conn.execute('SELECT * FROM Orders WHERE OrderID = ?', (order_id,)).fetchone()
  conn.close()
  if order is None:
    raise HTTPException(status_code=404, detail="Order not found")
  return dict(order)


@app.put("/orders/{order_id}", response_model=Order)
def update_order(order_id: int, order: Order, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'UPDATE Orders SET CustomerID = ?, OrderDate = ?, TotalAmount = ?, ShippingAddress = ?, City = ?, State = ?, ZipCode = ?, Country = ?, Status = ?, PaymentStatus = ? '
    'WHERE OrderID = ?',
    (
    order.CustomerID, order.OrderDate, order.TotalAmount, order.ShippingAddress, order.City, order.State, order.ZipCode,
    order.Country, order.Status, order.PaymentStatus, order_id)
  )
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Order not found")
  conn.close()
  return {**order.dict(), "OrderID": order_id}


@app.delete("/orders/{order_id}")
def delete_order(order_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('DELETE FROM Orders WHERE OrderID = ?', (order_id,))
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Order not found")
  conn.close()
  return {"detail": "Order deleted successfully"}


# Secured CRUD operations for OrderDetails
@app.post("/orderdetails", response_model=OrderDetail)
def create_order_detail(order_detail: OrderDetail, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'INSERT INTO OrderDetails (OrderID, ProductID, Quantity, Price) '
    'VALUES (?, ?, ?, ?)',
    (order_detail.OrderID, order_detail.ProductID, order_detail.Quantity, order_detail.Price)
  )
  conn.commit()
  order_detail_id = cursor.lastrowid
  conn.close()
  return {**order_detail.dict(), "OrderDetailID": order_detail_id}


@app.get("/orderdetails/{order_id}", response_model=List[OrderDetail])
def read_order_details(order_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  order_details = conn.execute('SELECT * FROM OrderDetails WHERE OrderID = ?', (order_id,)).fetchall()
  conn.close()
  return [dict(order_detail) for order_detail in order_details]


@app.put("/orderdetails/{order_detail_id}", response_model=OrderDetail)
def update_order_detail(order_detail_id: int, order_detail: OrderDetail, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'UPDATE OrderDetails SET OrderID = ?, ProductID = ?, Quantity = ?, Price = ? '
    'WHERE OrderDetailID = ?',
    (order_detail.OrderID, order_detail.ProductID, order_detail.Quantity, order_detail.Price, order_detail_id)
  )
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Order detail not found")
  conn.close()
  return {**order_detail.dict(), "OrderDetailID": order_detail_id}


@app.delete("/orderdetails/{order_detail_id}")
def delete_order_detail(order_detail_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('DELETE FROM OrderDetails WHERE OrderDetailID = ?', (order_detail_id,))
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Order detail not found")
  conn.close()
  return {"detail": "Order detail deleted successfully"}


# Secured CRUD operations for Employees
@app.post("/employees", response_model=Employee)
def create_employee(employee: Employee, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'INSERT INTO Employees (FirstName, LastName, Email, Password, Role) '
    'VALUES (?, ?, ?, ?, ?)',
    (employee.FirstName, employee.LastName, employee.Email, employee.Password, employee.Role)
  )
  conn.commit()
  employee_id = cursor.lastrowid
  conn.close()
  return {**employee.dict(), "EmployeeID": employee_id}


@app.get("/employees", response_model=List[Employee])
def read_employees(username: str = Depends(authenticate)):
  conn = get_db_connection()
  employees = conn.execute('SELECT * FROM Employees').fetchall()
  conn.close()
  return [dict(employee) for employee in employees]


@app.get("/employees/{employee_id}", response_model=Employee)
def read_employee(employee_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  employee = conn.execute('SELECT * FROM Employees WHERE EmployeeID = ?', (employee_id,)).fetchone()
  conn.close()
  if employee is None:
    raise HTTPException(status_code=404, detail="Employee not found")
  return dict(employee)


@app.put("/employees/{employee_id}", response_model=Employee)
def update_employee(employee_id: int, employee: Employee, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'UPDATE Employees SET FirstName = ?, LastName = ?, Email = ?, Password = ?, Role = ? '
    'WHERE EmployeeID = ?',
    (employee.FirstName, employee.LastName, employee.Email, employee.Password, employee.Role, employee_id)
  )
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Employee not found")
  conn.close()
  return {**employee.dict(), "EmployeeID": employee_id}


@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('DELETE FROM Employees WHERE EmployeeID = ?', (employee_id,))
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Employee not found")
  conn.close()
  return {"detail": "Employee deleted successfully"}


# Secured CRUD operations for Shipping
@app.post("/shipping", response_model=Shipping)
def create_shipping(shipping: Shipping, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'INSERT INTO Shipping (OrderID, EmployeeID, ShippingDate, ShippingMethod, TrackingNumber) '
    'VALUES (?, ?, ?, ?, ?)',
    (shipping.OrderID, shipping.EmployeeID, shipping.ShippingDate, shipping.ShippingMethod, shipping.TrackingNumber)
  )
  conn.commit()
  shipping_id = cursor.lastrowid
  conn.close()
  return {**shipping.dict(), "ShippingID": shipping_id}


@app.get("/shipping", response_model=List[Shipping])
def read_shipping(username: str = Depends(authenticate)):
  conn = get_db_connection()
  shippings = conn.execute('SELECT * FROM Shipping').fetchall()
  conn.close()
  return [dict(shipping) for shipping in shippings]


@app.get("/shipping/{shipping_id}", response_model=Shipping)
def read_shipping_by_id(shipping_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  shipping = conn.execute('SELECT * FROM Shipping WHERE ShippingID = ?', (shipping_id,)).fetchone()
  conn.close()
  if shipping is None:
    raise HTTPException(status_code=404, detail="Shipping record not found")
  return dict(shipping)


@app.put("/shipping/{shipping_id}", response_model=Shipping)
def update_shipping(shipping_id: int, shipping: Shipping, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'UPDATE Shipping SET OrderID = ?, EmployeeID = ?, ShippingDate = ?, ShippingMethod = ?, TrackingNumber = ? '
    'WHERE ShippingID = ?',
    (shipping.OrderID, shipping.EmployeeID, shipping.ShippingDate, shipping.ShippingMethod, shipping.TrackingNumber,
     shipping_id)
  )
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Shipping record not found")
  conn.close()
  return {**shipping.dict(), "ShippingID": shipping_id}


@app.delete("/shipping/{shipping_id}")
def delete_shipping(shipping_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('DELETE FROM Shipping WHERE ShippingID = ?', (shipping_id,))
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Shipping record not found")
  conn.close()
  return {"detail": "Shipping record deleted successfully"}


# Secured CRUD operations for Inventory Logs
@app.post("/inventorylogs", response_model=InventoryLog)
def create_inventory_log(inventory_log: InventoryLog, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'INSERT INTO InventoryLog (ProductID, EmployeeID, ChangeType, QuantityChange, ChangeDate) '
    'VALUES (?, ?, ?, ?, ?)',
    (inventory_log.ProductID, inventory_log.EmployeeID, inventory_log.ChangeType, inventory_log.QuantityChange,
     inventory_log.ChangeDate)
  )
  conn.commit()
  log_id = cursor.lastrowid
  conn.close()
  return {**inventory_log.dict(), "LogID": log_id}


@app.get("/inventorylogs", response_model=List[InventoryLog])
def read_inventory_logs(username: str = Depends(authenticate)):
  conn = get_db_connection()
  logs = conn.execute('SELECT * FROM InventoryLog').fetchall()
  conn.close()
  return [dict(log) for log in logs]


@app.get("/inventorylogs/{log_id}", response_model=InventoryLog)
def read_inventory_log(log_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  log = conn.execute('SELECT * FROM InventoryLog WHERE LogID = ?', (log_id,)).fetchone()
  conn.close()
  if log is None:
    raise HTTPException(status_code=404, detail="Inventory log not found")
  return dict(log)


@app.put("/inventorylogs/{log_id}", response_model=InventoryLog)
def update_inventory_log(log_id: int, inventory_log: InventoryLog, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'UPDATE InventoryLog SET ProductID = ?, EmployeeID = ?, ChangeType = ?, QuantityChange = ?, ChangeDate = ? '
    'WHERE LogID = ?',
    (inventory_log.ProductID, inventory_log.EmployeeID, inventory_log.ChangeType, inventory_log.QuantityChange,
     inventory_log.ChangeDate, log_id)
  )
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Inventory log not found")
  conn.close()
  return {**inventory_log.dict(), "LogID": log_id}


@app.delete("/inventorylogs/{log_id}")
def delete_inventory_log(log_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('DELETE FROM InventoryLog WHERE LogID = ?', (log_id,))
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Inventory log not found")
  conn.close()
  return {"detail": "Inventory log deleted successfully"}


# Secured CRUD operations for Payments
@app.post("/payments", response_model=Payment)
def create_payment(payment: Payment, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'INSERT INTO Payments (OrderID, Amount, PaymentDate, PaymentMethod) '
    'VALUES (?, ?, ?, ?)',
    (payment.OrderID, payment.Amount, payment.PaymentDate, payment.PaymentMethod)
  )
  conn.commit()
  payment_id = cursor.lastrowid
  conn.close()
  return {**payment.dict(), "PaymentID": payment_id}


@app.get("/payments", response_model=List[Payment])
def read_payments(username: str = Depends(authenticate)):
  conn = get_db_connection()
  payments = conn.execute('SELECT * FROM Payments').fetchall()
  conn.close()
  return [dict(payment) for payment in payments]


@app.get("/payments/{payment_id}", response_model=Payment)
def read_payment(payment_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  payment = conn.execute('SELECT * FROM Payments WHERE PaymentID = ?', (payment_id,)).fetchone()
  conn.close()
  if payment is None:
    raise HTTPException(status_code=404, detail="Payment not found")
  return dict(payment)


@app.put("/payments/{payment_id}", response_model=Payment)
def update_payment(payment_id: int, payment: Payment, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    'UPDATE Payments SET OrderID = ?, Amount = ?, PaymentDate = ?, PaymentMethod = ? '
    'WHERE PaymentID = ?',
    (payment.OrderID, payment.Amount, payment.PaymentDate, payment.PaymentMethod, payment_id)
  )
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Payment not found")
  conn.close()
  return {**payment.dict(), "PaymentID": payment_id}


@app.delete("/payments/{payment_id}")
def delete_payment(payment_id: int, username: str = Depends(authenticate)):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('DELETE FROM Payments WHERE PaymentID = ?', (payment_id,))
  conn.commit()
  if cursor.rowcount == 0:
    conn.close()
    raise HTTPException(status_code=404, detail="Payment not found")
  conn.close()
  return {"detail": "Payment deleted successfully"}


if __name__ == "__main__":
  import uvicorn

  uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)