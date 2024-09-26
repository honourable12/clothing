Clothing Management System

This project is a Clothing Management System built using FastAPI, designed to handle various operations such as user authentication, managing products, and displaying data via a dashboard. It utilizes SQLite for the database, JWT for authentication, and bcrypt for secure password hashing.
Features

  FastAPI Framework: High-performance web framework for developing APIs and backend services.
  SQLite Database: Lightweight, self-contained database used for storing data.
  JWT Authentication: Secure token-based authentication for managing user sessions.
  Bcrypt: Password hashing to enhance security.
  Dashboard: User-friendly interface to view and manage multiple tables such as users, products, and orders.

Tech Stack

  Backend: FastAPI
  Database: SQLite
  Authentication: JWT (JSON Web Token), Bcrypt (for password hashing)
  Dashboard: FastAPI integrated admin/dashboard

Installation

Clone the repository:

    bash

    git clone https://github.com/honourable12/clothing.git
    cd clothing

Create a virtual environment and activate it:

    bash

      python -m venv venv
      source venv/bin/activate  # On Windows: venv\Scripts\activate

Install the required dependencies:

    bash

    pip install -r requirements.txt

Run the application:

    bash

    uvicorn main:app --reload

    The server will start on http://127.0.0.1:8000/.

Usage
Authentication

  JWT Tokens: The application uses JWT for handling secure user authentication.
  Password Security: User passwords are hashed using bcrypt to ensure a high level of security.

Dashboard

  Access the dashboard by navigating to http://127.0.0.1:8000/dashboard after running the application.
  Manage multiple tables including users, clothing items, and orders.

Database

This project uses SQLite as its primary database. You can interact with it directly through the FastAPI endpoints or by connecting via the admin dashboard.
