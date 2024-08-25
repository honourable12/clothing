import streamlit as st
import requests

# API URL
API_URL = "http://127.0.0.1:8000"

# Utility functions
def authenticate(username, password):
    response = requests.post(f"{API_URL}/authenticate", data={"username": username, "password": password})
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Authentication failed.")
        return None

def get_customers(token):
    response = requests.get(f"{API_URL}/customers", headers={"Authorization": f"Bearer {token}"})
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch customers.")
        return []

def create_customer(data, token):
    response = requests.post(f"{API_URL}/customers", json=data, headers={"Authorization": f"Bearer {token}"})
    if response.status_code == 200:
        st.success("Customer created successfully.")
    else:
        st.error("Failed to create customer.")

def get_products(token):
    response = requests.get(f"{API_URL}/products", headers={"Authorization": f"Bearer {token}"})
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch products.")
        return []

def create_product(data, token):
    response = requests.post(f"{API_URL}/products", json=data, headers={"Authorization": f"Bearer {token}"})
    if response.status_code == 200:
        st.success("Product created successfully.")
    else:
        st.error("Failed to create product.")

st.title("Clothing Business Management")

st.header("Login")
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user = authenticate(username, password)
    if user:
        st.session_state.token = user['token']
        st.session_state.user = user

        st.success(f"Welcome, {user['FirstName']} {user['LastName']}!")

        # Customers
        st.header("Manage Customers")
        if st.button("Load Customers"):
            customers = get_customers(st.session_state.token)
            st.write(customers)

        st.subheader("Add Customer")
        with st.form("add_customer"):
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            email = st.text_input("Email")
            phone_number = st.text_input("Phone Number")
            submitted = st.form_submit_button("Add Customer")
            if submitted:
                create_customer({
                    "FirstName": first_name,
                    "LastName": last_name,
                    "Email": email,
                    "PhoneNumber": phone_number
                }, st.session_state.token)

        # Products
        st.header("Manage Products")
        if st.button("Load Products"):
            products = get_products(st.session_state.token)
            st.write(products)

        st.subheader("Add Product")
        with st.form("add_product"):
            name = st.text_input("Product Name")
            description = st.text_area("Description")
            price = st.number_input("Price", min_value=0.0, format="%.2f")
            stock = st.number_input("Stock", min_value=0)
            submitted = st.form_submit_button("Add Product")
            if submitted:
                create_product({
                    "Name": name,
                    "Description": description,
                    "Price": price,
                    "Stock": stock
                }, st.session_state.token)
    else:
        st.error("Invalid credentials.")
