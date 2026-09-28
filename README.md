# Credit Card Fraud Detection Web Application

A machine learning-powered web application built with Streamlit, scikit-learn, and MongoDB Atlas to predict credit card transaction fraud in real-time.

## Features
- **Real-Time Fraud Detection**: Machine learning classification pipeline (`fraud_detection_pipeline.pkl`).
- **User Authentication**: Secure Sign Up & Log In with `bcrypt` password hashing.
- **Dual-Mode Database Storage**:
  - **MongoDB Atlas Cloud Database**: Syncs users and transaction prediction history to the cloud.
  - **Local SQLite Database**: Resilient offline fallback so registration and predictions always work.
- **Transaction History**: Audit logs of all predictions for logged-in accounts.

---

## 🚀 Deployment Guide

### Option 1: Streamlit Community Cloud (Recommended & 100% Free)
1. Push this project repository to **GitHub**.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
3. Click **"New app"**.
4. Select your repository, branch (`main`), and set the main file path:
   ```text
   fraud_detection.py
   ```
5. Click **"Advanced settings..."** and configure your secrets:
   ```toml
   MONGO_URI = "mongodb://abhisheksonkar707_db_user:<YOUR_PASSWORD>@ac-uxpr2iy-shard-00-00.dmzepa5.mongodb.net:27017,ac-uxpr2iy-shard-00-01.dmzepa5.mongodb.net:27017,ac-uxpr2iy-shard-00-02.dmzepa5.mongodb.net:27017/?ssl=true&replicaSet=atlas-nprrlv-shard-0&authSource=admin&appName=Cluster0&compressors=zlib"
   ```
6. Click **"Deploy!"**. Your app will be live with a public HTTPS URL.

> **MongoDB Atlas Note**: Ensure your MongoDB Atlas cluster has Network Access configured to allow connections from anywhere (`0.0.0.0/0`) under **Network Access** > **IP Access List**.

---

### Option 2: Render / Railway (Procfile)
1. Link your GitHub repository to [Render](https://render.com/) or [Railway](https://railway.app/).
2. Select **Web Service** with Python environment.
3. Build command:
   ```bash
   pip install -r requirements.txt
   ```
4. Start command:
   ```bash
   streamlit run fraud_detection.py --server.port=$PORT --server.address=0.0.0.0
   ```
5. Add the environment variable `MONGO_URI` under Service Environment Variables.

---

### Option 3: Docker Container
1. Build the Docker image:
   ```bash
   docker build -t fraud-detection-app .
   ```
2. Run the container:
   ```bash
   docker run -p 8501:8501 -e MONGO_URI="<YOUR_MONGO_URI>" fraud-detection-app
   ```
3. Visit `http://localhost:8501`.

---

## 💻 Local Development Setup
1. Clone the repository and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create or configure `.env`:
   ```env
   MONGO_URI=mongodb://abhisheksonkar707_db_user:<YOUR_PASSWORD>@ac-uxpr2iy-shard-00-00.dmzepa5.mongodb.net:27017,ac-uxpr2iy-shard-00-01.dmzepa5.mongodb.net:27017,ac-uxpr2iy-shard-00-02.dmzepa5.mongodb.net:27017/?ssl=true&replicaSet=atlas-nprrlv-shard-0&authSource=admin&appName=Cluster0&compressors=zlib
   ```
3. Run the application:
   ```bash
   streamlit run fraud_detection.py
   ```
