# 🐝 SplitBee – Smart Shared Expense Management System

🔗 **Live Demo:** [https://your-streamlit-app-url.streamlit.app/](https://splitbee-expense.streamlit.app/)

SplitBee is a Streamlit-based expense management platform designed to simplify shared expenses among friends, roommates, families, travel groups, and teams.

The application provides intelligent bill splitting, balance tracking, settlement optimization, CSV-based expense imports, anomaly detection, approval workflows, and reporting — all through a modern and interactive dashboard.

---

# 📌 Problem Statement

Managing group expenses manually often leads to:

* Confusion about who paid what
* Difficulty calculating balances
* Unequal expense sharing requirements
* Duplicate or incorrect expense records
* Time-consuming settlement calculations
* Lack of transparency in imported financial data

SplitBee solves these problems by automating expense tracking, split calculations, settlement generation, and data validation in a single platform.

---

# ✨ Features

### 👤 Authentication & User Management

* User Registration
* Secure Login System
* Password Hashing
* Session Management

### 👥 Group Management

* Create Groups
* Manage Multiple Expense Groups
* Add or Remove Members
* View Group Summaries

### 💰 Expense Tracking

* Add Expenses Manually
* Update Existing Expenses
* Delete Expenses
* View Expense History

### ⚖️ Multiple Splitting Methods

* Equal Split
* Percentage-Based Split
* Exact Amount Split
* Share-Based Split

### 📊 Balance Calculation

* Member-wise Balance Tracking
* Group Balance Summary
* Net Payable & Receivable Amounts

### 🤝 Settlement Optimization

* Smart Debt Simplification
* Minimized Transactions
* Settlement Recommendations

### 📂 CSV Import System

* Upload Expense Data
* Automatic Validation
* Review Before Import
* Bulk Expense Processing

### 🔍 Anomaly Detection

Automatically identifies:

* Duplicate Records
* Missing Values
* Negative Expenses
* Invalid Dates
* Future Dates
* Currency Errors
* Outlier Transactions
* Corrupted Entries

### ✅ Approval Workflow

* Review Flagged Records
* Approve or Reject Changes
* Maintain Import History

### 📈 Reporting & Analytics

Generate:

* Expense Reports
* Settlement Reports
* Balance Reports
* Audit Reports

---

# 🖥️ Tech Stack

### Frontend

* Streamlit
* HTML
* CSS

### Backend

* Python

### Database

* SQLite

### Data Processing

* Pandas
* NumPy

### Reporting

* CSV Export
* Data Analytics

### Authentication

* Password Hashing
* Session State Management

---

# 📂 Project Structure

```text
📁 SplitBee
│
├── app.py                     # Main Streamlit Application
├── requirements.txt           # Project Dependencies
├── README.md                  # Documentation
│
├── 📁 assets
│   ├── styles.css             # Custom Styling
│   └── images                 # Application Assets
│
├── 📁 database
│   ├── db.py                  # Database Operations
│   └── schema.sql             # Database Schema
│
├── 📁 modules
│   ├── auth.py                # Authentication Module
│   ├── groups.py              # Group Management
│   ├── members.py             # Member Management
│   ├── expenses.py            # Expense Operations
│   ├── balances.py            # Balance Calculations
│   ├── settlements.py         # Settlement Engine
│   ├── csv_import.py          # CSV Import Processing
│   ├── anomaly_detector.py    # Anomaly Detection
│   ├── approval.py            # Approval Workflow
│   ├── reports.py             # Report Generation
│   ├── import_logs.py         # Audit Logs
│   └── currency.py            # Currency Utilities
│
└── 📁 reports                 # Generated Reports
```

---

# ⚙️ System Workflow

```text
Expense Added
      │
      ▼
Select Split Method
      │
      ▼
Calculate Member Shares
      │
      ▼
Update Balances
      │
      ▼
Generate Settlements
      │
      ▼
Create Reports
```

### CSV Import Workflow

```text
Upload CSV
      │
      ▼
Validate Data
      │
      ▼
Detect Anomalies
      │
      ▼
Review Records
      │
      ▼
Approve Import
      │
      ▼
Store in Database
      │
      ▼
Update Expenses & Balances
```

---

# 🚀 Installation & Run Locally

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/SplitBee.git

cd SplitBee
```

### 2️⃣ Create Virtual Environment

#### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

#### Linux / macOS

```bash
python -m venv venv

source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Run the Application

```bash
streamlit run app.py
```

The application will be available at:

```text
http://localhost:8501
```

---

# 📋 Requirements

```text
streamlit
pandas
numpy
bcrypt
python-dateutil
sqlite3
```

Install all dependencies using:

```bash
pip install -r requirements.txt
```

---

# 📊 How It Works

### Manual Expense Entry

1. Create or select a group
2. Add members
3. Record expenses
4. Select a splitting method
5. Calculate balances
6. Generate settlements

### CSV Import

1. Upload expense file
2. Validate records
3. Detect anomalies
4. Review flagged entries
5. Approve import
6. Generate reports

---

# 📈 Reports Generated

* Expense Summary Report
* Group Balance Report
* Settlement Report
* Import Audit Report
* Anomaly Detection Report

---

# 🔮 Future Enhancements

* AI Expense Categorization
* Receipt OCR Scanning
* Real-Time Currency Conversion
* Email Notifications
* Cloud Database Support
* Interactive Analytics Dashboard
* Mobile Responsive Design
* Group Collaboration Features

---

# 💼 Use Cases

* Roommate Expense Tracking
* Travel Expense Management
* Event Budget Management
* Family Expense Sharing
* Student Group Projects
* Team Expense Tracking

---

# 👨‍💻 Author

**Anchal Shukla**

Built as a modern expense-sharing solution that combines automation, data validation, and intelligent settlement calculations into a simple and user-friendly interface.

---

# ⭐ Support

If you found this project useful:

* Give it a ⭐ on GitHub
* Fork and improve it
* Share it with your network
* Contribute new features and improvements

Your support helps improve the project and encourages further development.
