import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
from io import BytesIO
import mysql.connector

conn = mysql.connector.connect(
    host = 'srv1674.hstgr.io',
    user = 'u410375047_jayanath',
    password = 'Rangika@_123',
    database = 'u410375047_SBMLogin'
    )
# Connect to SQLite database (or create it)
#conn = sqlite3.connect('sales_data.db', check_same_thread=False)
c = conn.cursor()

# Create table for daily sales if it doesn't exist
#c.execute('''CREATE TABLE IF NOT EXISTS sales (
#        id INTEGER PRIMARY KEY AUTOINCREMENT,
#        shop_name TEXT,
#        date TEXT,
#        sales REAL,
#        cashout REAL,
#        expense_type TEXT,
#        other_expenses REAL,
#        description TEXT,
#        bank_deposit REAL  
#    )''')
#conn.commit()

# Create transactions table for handling deposits and cheques
#c.execute('''CREATE TABLE IF NOT EXISTS transactions (
#                id INTEGER PRIMARY KEY AUTOINCREMENT,
#               date TEXT,
#                type TEXT,
#                amount REAL,
#                balance REAL,
#                location TEXT,
#                company_name TEXT
#            )''')
#conn.commit()

# Helper functions
def get_latest_balance():
    try:
        c.execute("SELECT balance FROM transactions ORDER BY id DESC LIMIT 1")
        result = c.fetchone()
        return float(result[0]) if result else 0.0    
    except Exception as e:
        st.error(f"Error fetching the latest balance: {e}")
        return 0.0

def insert_transaction(transaction):
    try:
        c.execute('''INSERT INTO transactions (date, type, amount, balance, location, company_name) 
                     VALUES (%s, %s, %s, %s, %s, %s)''', 
                  (transaction['date'], transaction['type'], transaction['amount'], 
                   transaction['balance'], transaction['location'], transaction['company_name']))
        conn.commit()
    except Exception as e:
        st.error(f"Error inserting transaction: {e}")

# Sales entry functions
def insert_sales_data(shop_name, sales_date, sales, cashout, expense_type, other_expenses, description, bank_deposit):
    c.execute('''INSERT INTO sales (shop_name, date, sales, cashout, expense_type, other_expenses, description, bank_deposit)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''', 
              (shop_name, sales_date, sales, cashout, expense_type, other_expenses, description, bank_deposit))




def fetch_transaction_history():
    try:
        c.execute("SELECT * FROM transactions")
        rows = c.fetchall()
        columns = ['ID', 'Date', 'Type', 'Amount', 'Balance', 'Location', 'Company Name']
        df = pd.DataFrame(rows, columns=columns)
        return df
    except Exception as e:
        print(f"Error fetching transaction history: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error


def fetch_sales_data():
    c.execute("SELECT * FROM sales")
    rows = c.fetchall()
    columns = ['ID', 'Shop Name', 'Date', 'Sales', 'Cashout', 'Expense Type', 'Other Expenses', 'Description', 'Bank Deposit']
    df = pd.DataFrame(rows, columns=columns)
    return df

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='SalesData')
        writer.close()
    processed_data = output.getvalue()
    return processed_data

# Function to handle Cash Deposit form
def handle_cash_deposit():
    st.subheader("Cash Deposit")
    with st.form(key="cash_deposit_form"):
        transaction_date = st.date_input("Transaction Date", datetime.now().date())
        location = st.selectbox("Deposit Location", ("Gampaha", "Nittambuwa"))
        amount = st.number_input("Deposit Amount", min_value=0.0, format="%.2f")
        submit = st.form_submit_button(label="Submit Cash Deposit")

        if submit:
            balance = get_latest_balance() + amount
            transaction_entry = {
                "date": transaction_date.strftime("%Y-%m-%d"),
                "type": f"Deposit ({location})",
                "amount": amount,
                "balance": balance,
                "location": location,
                "company_name": None
            }
            insert_transaction(transaction_entry)
            st.success(f"Cash Deposit of LKR {amount:.2f} at {location} added.")

# Function to handle Pass Cheque form
def handle_pass_cheque():
    st.subheader("Pass Cheque")
    with st.form(key="pass_cheque_form"):
        transaction_date = st.date_input("Transaction Date", datetime.now().date())
        company_name = st.text_input("Company Name on Cheque", "")
        amount = st.number_input("Cheque Amount", min_value=0.0, format="%.2f")
        submit = st.form_submit_button(label="Submit Cheque")

        if submit:
            balance = get_latest_balance() - amount
            transaction_entry = {
                "date": transaction_date.strftime("%Y-%m-%d"),
                "type": f"Cheque Passed (Company: {company_name})",
                "amount": -amount,
                "balance": balance,
                "location": None,
                "company_name": company_name
            }
            insert_transaction(transaction_entry)
            st.success(f"Cheque of LKR {amount:.2f} from {company_name} added.")

# Sales entry form
def handle_sales_entry():
    st.subheader("Daily Sales Data Entry")
    shop_name = st.radio("Select Shop Name", options=["Gampaha", "Nittambuwa"])
    sales_date = st.date_input("Date", value=date.today())
    sales = st.number_input("Sales (in LKR)", min_value=0.0, format="%.2f")
    cashout = st.number_input("Cashout (in LKR)", min_value=0.0, format="%.2f")
    add_expenses = st.checkbox("Add Expenses?")
    if add_expenses:
        expense_type = st.selectbox("Select Expense Type", options=["Salary", "Rent", "Petty Cash", "Light Bill", "Water Bill", "Phone Bill", "Other Expenses"])
        other_expenses = st.number_input("Other Expenses (in LKR)", min_value=0.0, format="%.2f")
        description = st.text_area("Description", help="Details about expenses, etc.")
    else:
        expense_type = ""
        other_expenses = 0.0
        description = ""
    bank_deposit = st.number_input("Bank Deposit (in LKR)", min_value=0.0, format="%.2f")

    if st.button("Submit"):
        if shop_name and sales and cashout and bank_deposit:
            # Insert sales data
            insert_sales_data(shop_name, sales_date, sales, cashout, expense_type, other_expenses, description, bank_deposit)

            # Automatically record the bank deposit into transactions table
            balance = get_latest_balance() + bank_deposit
            transaction_entry = {
                "date": sales_date.strftime("%Y-%m-%d"),
                "type": f"Deposit (Sales from {shop_name})",
                "amount": bank_deposit,
                "balance": balance,
                "location": shop_name,
                "company_name": None
            }
            insert_transaction(transaction_entry)
            st.success("Sales data and bank deposit have been saved successfully!")

# Main app
st.title("Business Management System")

# Navigation
pages = ["Cash Deposit", "Pass Cheque", "Sales Entry"]
page = st.sidebar.selectbox("Select a page", pages)

# Page handling
if page == "Cash Deposit":
    handle_cash_deposit()
elif page == "Pass Cheque":
    handle_pass_cheque()
elif page == "Sales Entry":
    handle_sales_entry()

# Show sales data (optional)
if st.checkbox("Show sales data"):
    sales_data = fetch_sales_data()
    if not sales_data.empty:
        st.dataframe(sales_data)
        excel_data = to_excel(sales_data)
        st.download_button(label="Download Sales Data as Excel", data=excel_data, file_name="sales_data.xlsx")
    else:
        st.write("No sales data available.")

# Close the database connection
conn.close()
