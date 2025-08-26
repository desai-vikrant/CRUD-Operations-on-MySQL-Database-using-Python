
import pandas as pd
from sqlalchemy import create_engine, text
import mysql.connector
import streamlit as st

db_user = "root"         
db_password = "1111"  
db_host = "localhost"    
db_name = "pass_db" 

engine = create_engine(f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}")  # creates a bridge between python and mySQL using SQLAlchemy

def get_existing_usernames():
    return pd.read_sql("SELECT username FROM accounts", con=engine)["username"].tolist()

def signup(username, password, confirm_password):
    specials = "!@#$%^&*=<>?/,.~"
    existing_usernames = get_existing_usernames()

    if len(username) < 5:
        return "Username must be at least 5 characters long"
    if username in existing_usernames:
        return "Username already exists, please choose another"

    if len(password) < 8:
        return "Password must contain at least 8 characters"
    if " " in password:
        return "Password must not contain any spaces"
    if not any(ch.isdigit() for ch in password):
        return "Password must contain at least one number"
    if not any(ch.isupper() for ch in password):
        return "Password must contain at least one uppercase letter"
    if not any(ch.islower() for ch in password):
        return "Password must contain at least one lowercase letter"
    if not any(ch in specials for ch in password):
        return "Password must contain at least one special character"
    if password != confirm_password:
        return "Password and confirm password are not matching"

    new_user = pd.DataFrame([{
        "username": username,
        "password": password,
        "confirm_password": confirm_password
    }])
    new_user.to_sql("accounts", con=engine, if_exists="append", index=False)
    return f"New User '{username}' registered successfully"

def login(username, password):
    accounts = pd.read_sql("SELECT username, password FROM accounts", con=engine)

    if username not in accounts["username"].tolist():
        return False, "Username does not exist. Please sign up first."
    
    user_data = accounts[accounts["username"] == username]
    if user_data["password"].values[0] == password:
        return True, f"Log in successful, welcome {username}."
    else:
        return False, "Invalid password, Please try again."

def update_password(username, new_password, new_confirm_password):
    if new_password != new_confirm_password:
        return "Passwords are not matching"
    
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE accounts SET password = :pwd, confirm_password = :cpwd WHERE username = :usr"),
            {"pwd": new_password, "cpwd": new_confirm_password, "usr": username}
        )
    return "Password updated successfully"

def delete_account(username):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM accounts WHERE username = :usr"), {"usr": username})
    return f"Account '{username}' deleted successfully."


# ---------------- Streamlit UI ----------------
st.title("User Management System")

# keep login persistent
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "logout_confirm" not in st.session_state:
    st.session_state.logout_confirm = False

menu = ["Signup", "Login"]
choice = st.sidebar.radio("Menu", menu)

# -------- Signup Page --------
if choice == "Signup" and not st.session_state.logged_in:
    st.subheader("Create a New Account")

    username = st.text_input("Enter Username")
    password = st.text_input("Enter Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Signup"):
        msg = signup(username, password, confirm_password)
        if "successfully" in msg:
            st.success(msg)
        else:
            st.error(msg)

# -------- Login Page --------
elif choice == "Login":
    if not st.session_state.logged_in:
        st.subheader("Login to Your Account")
        username = st.text_input("Enter Username")
        password = st.text_input("Enter Password", type="password")

        if st.button("Login"):
            success, msg = login(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(msg)
            else:
                st.error(msg)

    # If logged in
    if st.session_state.logged_in:
        st.subheader(f"Welcome, {st.session_state.username}")
        option = st.radio("Choose an action:", ["Update Password", "Delete Account", "Logout"])

        # ---- Update Password ----
        if option == "Update Password":
            new_pass = st.text_input("New Password", type="password")
            confirm_new_pass = st.text_input("Confirm New Password", type="password")
            if st.button("Update Password"):
                result = update_password(st.session_state.username, new_pass, confirm_new_pass)
                if "successfully" in result:
                    st.success(result)
                else:
                    st.error(result)

        # ---- Delete Account ----
        elif option == "Delete Account":
            if st.button("Delete Account"):
                result = delete_account(st.session_state.username)
                st.warning(result)
                st.session_state.logged_in = False
                st.session_state.username = ""

        # ---- Logout ----
        elif option == "Logout":
            if not st.session_state.logout_confirm:
                if st.button("logout"):
                    st.session_state.logged_in = False
                    st.session_state.username = ""
                    st.session_state.logout_confirm = False
                    st.info("You have been logged out.")
            else:
                st.session_state.logout_confirm = True

