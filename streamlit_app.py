import streamlit as st
import requests

# URL of your FastAPI backend
API_URL = "http://127.0.0.1:8000/authenticate"


# Function to handle authentication
def authenticate(username, password):
	# Send a GET request with query parameters
	response = requests.get(API_URL, params = {"username": username, "password": password})

	# Check for successful authentication
	if response.status_code == 200:
		return response.json()  # Return the JSON response from the API
	else:
		st.error("Authentication failed.")
		return None


# Streamlit app
def main():
	st.title("Authentication App")

	# User input for username and password
	username = st.text_input("Username")
	password = st.text_input("Password", type = "password")

	# Authenticate button
	if st.button("Authenticate"):
		if username and password:
			result = authenticate(username, password)
			if result:
				st.success(f"Authentication successful! Token: {result['token']}")
				st.write(f"First Name: {result['FirstName']}")
				st.write(f"Last Name: {result['LastName']}")
		else:
			st.error("Please enter both username and password.")


if __name__ == "__main__":
	main()
