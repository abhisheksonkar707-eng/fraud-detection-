import os
import streamlit as st
import pandas as pd
import joblib
from auth_db import (
    verify_user,
    create_user,
    save_prediction,
    get_prediction_history,
    format_mongo_uri,
    test_mongo_connection
)

# Page configuration
st.set_page_config(
    page_title="Credit Card Fraud Detection App",
    page_icon="💳",
    layout="wide"
)

# Load machine learning model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "fraud_detection_pipeline.pkl")

@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)

model = load_model()

# Initialize session state variables
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'db_password' not in st.session_state:
    st.session_state['db_password'] = ""
if 'mongo_uri' not in st.session_state:
    st.session_state['mongo_uri'] = format_mongo_uri() or ""
if 'db_mode' not in st.session_state:
    st.session_state['db_mode'] = "Auto (MongoDB with Local Fallback)"

# Sidebar: Database & Configuration Settings
st.sidebar.title("🛠️ Storage & Settings")

db_mode = st.sidebar.selectbox(
    "Database Storage Mode",
    [
        "Auto (MongoDB with Local Fallback)",
        "Local Database (Offline-ready)",
        "MongoDB Atlas (Cloud Only)"
    ],
    index=0
)
st.session_state['db_mode'] = db_mode

st.sidebar.markdown("---")
st.sidebar.subheader("☁️ MongoDB Atlas Settings")

entered_password = st.sidebar.text_input(
    "MongoDB Password",
    value=st.session_state['db_password'],
    type="password",
    help="Enter password for abhisheksonkar707_db_user"
)

if entered_password != st.session_state['db_password']:
    st.session_state['db_password'] = entered_password
    st.session_state['mongo_uri'] = format_mongo_uri(raw_password=entered_password)

if st.sidebar.button("🔌 Test MongoDB Connection"):
    current_uri = format_mongo_uri(raw_password=st.session_state['db_password'])
    if not current_uri or "<db_password>" in current_uri:
        st.sidebar.warning("Please enter your MongoDB database password first.")
    else:
        with st.sidebar.status("Testing connection to MongoDB Atlas..."):
            is_ok, msg = test_mongo_connection(current_uri)
            if is_ok:
                st.sidebar.success("✅ Connected to MongoDB Atlas successfully!")
            else:
                st.sidebar.error(f"❌ Connection failed: {msg}")
                st.sidebar.caption("Tip: Ensure your IP is whitelisted (0.0.0.0/0) in MongoDB Atlas Network Access.")

# Display Active Storage Badge
active_uri = format_mongo_uri(raw_password=st.session_state['db_password'])
if db_mode == "Local Database (Offline-ready)":
    st.sidebar.info("📦 Storage: **Local SQLite Database**")
elif db_mode == "MongoDB Atlas (Cloud Only)":
    st.sidebar.info("☁️ Storage: **MongoDB Atlas (Strict)**")
else:
    st.sidebar.success("⚡ Storage: **Auto (MongoDB / Local SQLite)**")

st.sidebar.markdown("---")

# Main Header
st.title("💳 Credit Card Fraud Detection System")

# ==========================================
# AUTHENTICATION SCREEN (LOGIN / SIGN UP)
# ==========================================
if not st.session_state['authenticated']:
    st.markdown("Welcome! Please **Log In** or **Register a New Account** to access the fraud detection analytics.")
    
    col_auth, _ = st.columns([2, 1])
    with col_auth:
        tab_login, tab_signup = st.tabs(["🔑 Log In", "📝 Sign Up"])
        
        # LOGIN TAB
        with tab_login:
            st.subheader("Login to Your Account")
            with st.form("login_form"):
                login_user = st.text_input("Username")
                login_pass = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Log In", type="primary", use_container_width=True)
                
                if submit_login:
                    if not login_user or not login_pass:
                        st.error("Please enter both username and password.")
                    else:
                        force_mode = "mongodb" if db_mode == "MongoDB Atlas (Cloud Only)" else "auto"
                        success, message = verify_user(
                            login_user,
                            login_pass,
                            uri=active_uri,
                            force_mode=force_mode
                        )
                        if success:
                            st.session_state['authenticated'] = True
                            st.session_state['username'] = login_user.strip()
                            st.success(f"Welcome back, {login_user}!")
                            st.rerun()
                        else:
                            st.error(f"Login failed: {message}")

        # SIGNUP TAB
        with tab_signup:
            st.subheader("Create a New Account")
            with st.form("signup_form"):
                reg_user = st.text_input("Choose Username")
                reg_email = st.text_input("Email Address")
                reg_pass = st.text_input("Choose Password", type="password")
                reg_confirm = st.text_input("Confirm Password", type="password")
                submit_signup = st.form_submit_button("Register Account", use_container_width=True)
                
                if submit_signup:
                    if not reg_user or not reg_email or not reg_pass:
                        st.error("Please fill out all fields.")
                    elif reg_pass != reg_confirm:
                        st.error("Passwords do not match!")
                    elif len(reg_pass) < 6:
                        st.warning("Password should be at least 6 characters.")
                    else:
                        force_mode = "mongodb" if db_mode == "MongoDB Atlas (Cloud Only)" else "auto"
                        success, message = create_user(
                            reg_user,
                            reg_email,
                            reg_pass,
                            uri=active_uri,
                            force_mode=force_mode
                        )
                        if success:
                            st.success(f"🎉 {message}")
                            st.info("You can now switch to the **Log In** tab to access your account.")
                        else:
                            st.error(f"Registration failed: {message}")

# ==========================================
# AUTHENTICATED USER DASHBOARD
# ==========================================
else:
    st.sidebar.markdown(f"👤 Logged in as: **{st.session_state['username']}**")
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state['authenticated'] = False
        st.session_state['username'] = None
        st.rerun()

    tab_predict, tab_history = st.tabs(["🔍 Transaction Prediction", "📜 Prediction History"])

    # PREDICTION TAB
    with tab_predict:
        st.subheader("Input Transaction Information")
        st.caption("Provide transaction parameters to run real-time machine learning fraud analysis.")

        with st.form("prediction_form"):
            col1, col2 = st.columns(2)
            with col1:
                transaction_type = st.selectbox(
                    "Transaction Type",
                    ["PAYMENT", "TRANSFER", "CASH_OUT", "DEPOSIT"]
                )
                amount = st.number_input("Transaction Amount ($)", min_value=0.0, value=1500.0, step=50.0)
                oldbalanceOrg = st.number_input("Origin Account Initial Balance ($)", min_value=0.0, value=10000.0, step=100.0)

            with col2:
                newbalanceOrig = st.number_input("Origin Account New Balance ($)", min_value=0.0, value=8500.0, step=100.0)
                oldbalanceDest = st.number_input("Destination Account Initial Balance ($)", min_value=0.0, value=0.0, step=100.0)
                newbalanceDest = st.number_input("Destination Account New Balance ($)", min_value=0.0, value=0.0, step=100.0)

            predict_btn = st.form_submit_button("Analyze & Predict Transaction", type="primary", use_container_width=True)

        if predict_btn:
            t_type = "DEPOSITE" if transaction_type == "DEPOSIT" else transaction_type
            input_data = pd.DataFrame([{
                "type": t_type,
                "amount": amount,
                "oldbalanceOrg": oldbalanceOrg,
                "newbalanceOrig": newbalanceOrig,
                "oldbalanceDest": oldbalanceDest,
                "newbalanceDest": newbalanceDest
            }])

            try:
                prediction = int(model.predict(input_data)[0])

                st.markdown("### Analysis Result")
                if prediction == 1:
                    st.error("🚨 **HIGH RISK TRANSACTION**: Flagged as **POTENTIAL FRAUD**!")
                else:
                    st.success("✅ **SAFE TRANSACTION**: Transaction is classified as **LEGITIMATE**.")

                # Save record to database
                tx_record = {
                    "type": transaction_type,
                    "amount": amount,
                    "oldbalanceOrg": oldbalanceOrg,
                    "newbalanceOrig": newbalanceOrig,
                    "oldbalanceDest": oldbalanceDest,
                    "newbalanceDest": newbalanceDest
                }

                save_prediction(
                    username=st.session_state['username'],
                    transaction_data=tx_record,
                    prediction=prediction,
                    uri=active_uri
                )
                st.toast("Transaction logged successfully!", icon="💾")

            except Exception as e:
                st.error(f"Model prediction error: {e}")

    # HISTORY TAB
    with tab_history:
        st.subheader("Your Transaction Prediction Logs")
        if st.button("🔄 Refresh Logs"):
            st.rerun()

        records = get_prediction_history(st.session_state['username'], uri=active_uri)
        if not records:
            st.info("No transaction predictions recorded yet.")
        else:
            table_rows = []
            for item in records:
                tx = item.get("transaction", {})
                table_rows.append({
                    "Timestamp": item.get("timestamp"),
                    "Type": tx.get("type"),
                    "Amount": f"${tx.get('amount', 0):,.2f}",
                    "Sender Old Bal": f"${tx.get('oldbalanceOrg', 0):,.2f}",
                    "Sender New Bal": f"${tx.get('newbalanceOrig', 0):,.2f}",
                    "Receiver Old Bal": f"${tx.get('oldbalanceDest', 0):,.2f}",
                    "Receiver New Bal": f"${tx.get('newbalanceDest', 0):,.2f}",
                    "Status": "🚨 FRAUD" if item.get("is_fraud") else "✅ SAFE"
                })

            df_history = pd.DataFrame(table_rows)
            st.dataframe(df_history, use_container_width=True)