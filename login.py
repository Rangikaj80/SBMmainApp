import streamlit as st
import sqlite3
import re
import bcrypt  # Import bcrypt for password hashing

# Connect to SQLite database (or create it)
conn = sqlite3.connect('password.db', check_same_thread=False)
c = conn.cursor()

# Create table for login information
c.execute('''
    CREATE TABLE IF NOT EXISTS password (
        email TEXT UNIQUE,
        username TEXT UNIQUE,
        password TEXT
    )
''')
conn.commit()

# Function to insert data into the table
def insert_user(email, username, password):
    c.execute('''
        INSERT INTO password (email, username, password)
        VALUES (?, ?, ?)
    ''', (email, username, password))
    conn.commit()

# Function to fetch all users from the database
def fetch_users():
    c.execute('SELECT * FROM password')
    return c.fetchall()

# Function to fetch user emails
def get_user_emails():
    c.execute('SELECT email FROM password')
    users = c.fetchall()
    emails = [user[0] for user in users]
    return emails

# Function to fetch usernames
def get_usernames():
    c.execute('SELECT username FROM password')
    users = c.fetchall()
    usernames = [user[0] for user in users]
    return usernames

# Function to fetch user password (hashed)
def get_user_password(username):
    c.execute('SELECT password FROM password WHERE username = ?', (username,))
    result = c.fetchone()
    return result[0] if result else None

# Function to validate email
def validate_email(email):
    pattern = "^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+\.[a-z]{1,3}$"
    return re.match(pattern, email) is not None

# Function to validate username
def validate_username(username):
    pattern = "^[a-zA-Z0-9]*$"
    return re.match(pattern, username) is not None

# Signup form
def sign_up():
    with st.form(key='sign_up', clear_on_submit=True):
        st.subheader('Sign Up')
        email = st.text_input('Email', placeholder='Enter your Email')
        username = st.text_input('User Name', placeholder='Enter your User Name')
        password1 = st.text_input('Password', placeholder='Enter your Password', type='password')
        password2 = st.text_input('Confirm Password', placeholder='Confirm your password', type='password')

        submit_button = st.form_submit_button('Sign Up')

        if submit_button:
            if validate_email(email):
                if email not in get_user_emails():
                    if validate_username(username):
                        if username not in get_usernames():
                            if len(username) >= 2:
                                if len(password1) >= 6:
                                    if password1 == password2:
                                        # Hash the password using bcrypt before storing it
                                        hashed_password = bcrypt.hashpw(password1.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                                        
                                        # Insert the user with hashed password into the database
                                        insert_user(email, username, hashed_password)

                                        st.success('Account created successfully!!')
                                        st.balloons()
                                    else:
                                        st.warning('Passwords do not match')
                                else:
                                    st.warning('Password is too short')
                            else:
                                st.warning('Username too short')
                        else:
                            st.warning('Username already exists')
                    else:
                        st.warning('Invalid username')
                else:
                    st.warning('Email already exists')
            else:
                st.warning('Invalid email')

# Login form
def login():
    st.subheader('Login')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')

    if st.button('Login'):
        if username in get_usernames():
            # Get the stored hashed password
            hashed_password = get_user_password(username)
            if hashed_password and bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                # Set session state to track logged-in user
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success(f'Welcome {username}!')
            else:
                st.error('Invalid username or password')
        else:
            st.error('User not found. Please sign up first.')

# Main pages (only accessible after login)
def main_page():
    st.title("Business Management System")

    pages = ["Cash Deposit", "Sales Entry", "Pass Cheque"]
    page = st.sidebar.selectbox("Select a page", pages)

    if page == "Cash Deposit":
        st.subheader("Cash Deposit Page")
        # Add your Cash Deposit logic here
    elif page == "Sales Entry":
        st.subheader("Sales Entry Page")
        # Add your Sales Entry logic here
    elif page == "Pass Cheque":
        st.subheader("Pass Cheque Page")
        # Add your Pass Cheque logic here

# Authentication and Navigation Handler
def app():
    st.sidebar.title('Authentication')
    
    # Initialize session state for login
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    # Enforce login to access other pages
    if st.session_state['logged_in']:
        main_page()  # If logged in, show the main page
    else:
        st.sidebar.warning("Please log in to access other pages.")
        auth_option = st.sidebar.selectbox('Choose an option', ['Login', 'Sign Up'])
        if auth_option == 'Sign Up':
            sign_up()
        elif auth_option == 'Login':
            login()

# Run the app
app()

# Close the database connection
conn.close()
