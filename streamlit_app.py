import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"  # Update this if your FastAPI app is running on a different address or port

# Function to authenticate user
def authenticate(email, password):
    response = requests.post(f"{API_URL}/token", data={"username": email, "password": password})
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        st.error("Invalid credentials")
        return None

# Function to add a new employee
def add_employee(token, first_name, last_name, email, password, role):
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "FirstName": first_name,
        "LastName": last_name,
        "Email": email,
        "Password": password,
        "Role": role,
    }
    response = requests.post(f"{API_URL}/employees", json=data, headers=headers)
    if response.status_code == 200:
        st.success("Employee added successfully!")
    else:
        st.error("Failed to add employee")

# Function to view orders
def view_orders(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/orders", headers=headers)
    return response.json()

# Function to add a product
def add_product(token, name, description, price):
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "ProductName": name,
        "Description": description,
        "Price": price,
        "StockQuantity": 0,  # Default quantity
    }
    response = requests.post(f"{API_URL}/products", json=data, headers=headers)
    if response.status_code == 200:
        st.success("Product added successfully!")
    else:
        st.error("Failed to add product")

# Function to view products
def view_products(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/products", headers=headers)
    return response.json()

# Streamlit UI
st.title("Clothing Store Management")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    token = authenticate(email, password)
    if token:
        st.success("Logged in successfully!")
        st.session_state.token = token
    else:
        st.error("Login failed. Check your credentials.")

if "token" in st.session_state:
    st.subheader("Manage Employees")
    with st.expander("Add Employee"):
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        employee_email = st.text_input("Employee Email")
        employee_password = st.text_input("Employee Password", type="password")
        role = st.selectbox("Role", ["Admin", "Employee"])

        if st.button("Add Employee"):
            add_employee(st.session_state.token, first_name, last_name, employee_email, employee_password, role)

    st.subheader("View Orders")
    if st.button("Load Orders"):
        orders = view_orders(st.session_state.token)
        for order in orders:
            st.write(order)

    st.subheader("Manage Products")
    with st.expander("Add Product"):
        product_name = st.text_input("Product Name")
        product_description = st.text_area("Product Description")
        product_price = st.number_input("Price", min_value=0.0, step=0.01)

        if st.button("Add Product"):
            add_product(st.session_state.token, product_name, product_description, product_price)

    st.subheader("View Products")
    if st.button("Load Products"):
        products = view_products(st.session_state.token)
        for product in products:
            st.write(product)
