# SCOPE.md

# SplitBee – Project Scope, Data Quality Analysis & Database Design

---

# 📌 Project Scope

SplitBee is designed as a shared expense management system that allows users to:

* Create expense groups
* Manage members
* Record expenses
* Split expenses using different strategies
* Calculate balances
* Generate settlements
* Import expenses through CSV files
* Detect and handle invalid data
* Generate reports and audit logs

The project focuses on ensuring **data correctness before financial calculations are performed**.

---

# 🎯 Scope Objectives

The system aims to:

* Simplify group expense tracking
* Improve transparency of shared expenses
* Reduce manual settlement effort
* Support bulk expense imports
* Prevent invalid records from entering the database
* Maintain auditability of imported data

---

# ✅ Included in Scope

### Expense Management

* Add expenses
* Edit expenses
* Delete expenses
* View expenses

### Group Management

* Create groups
* Manage members
* Track participation

### Settlement Management

* Calculate balances
* Generate optimized settlements

### CSV Processing

* Upload CSV files
* Validate imported data
* Detect anomalies
* Review flagged records

### Reporting

* Expense reports
* Balance reports
* Settlement reports
* Import audit reports

---

# ❌ Out of Scope

The following features are intentionally excluded:

* Online payments
* Bank account integration
* UPI integration
* Real-time transaction processing
* Mobile application
* Multi-tenant cloud architecture
* Machine learning predictions
* Cryptocurrency support

---

# 🔍 Data Quality Analysis

During CSV processing, several categories of anomalies were identified.

The anomaly detection system validates records before insertion into the database.

---

# 1️⃣ Duplicate Records

## Problem

Multiple rows represent the same expense.

### Example

```csv
ExpenseID,Member,Amount
101,Aisha,500
101,Aisha,500
```

## Risk

* Double counting
* Incorrect balances
* Settlement errors

## Handling Strategy

* Detect duplicate rows
* Flag for review
* Require user approval before removal

---

# 2️⃣ Missing Values

## Problem

Required fields are empty.

### Example

```csv
Member,Amount,Date
,500,2026-06-01
```

## Risk

* Incomplete transactions
* Reporting failures

## Handling Strategy

* Mark record invalid
* Prevent import until corrected

---

# 3️⃣ Negative Expense Amounts

## Problem

Expense amount is negative.

### Example

```csv
Member,Amount
Rahul,-250
```

## Risk

Financial calculations become invalid.

## Handling Strategy

* Flag anomaly
* Block automatic insertion

---

# 4️⃣ Zero Value Expenses

## Problem

Expense amount equals zero.

### Example

```csv
Member,Amount
Aisha,0
```

## Risk

Non-meaningful transaction

## Handling Strategy

* Flag for review
* Allow user decision

---

# 5️⃣ Invalid Date Format

## Problem

Date format cannot be parsed.

### Example

```csv
32/15/2026
```

## Risk

Reporting inaccuracies

## Handling Strategy

* Reject record
* Request correction

---

# 6️⃣ Future Dates

## Problem

Expense date occurs in the future.

### Example

```csv
2027-12-10
```

## Risk

Potential data entry mistake

## Handling Strategy

* Flag as suspicious
* Require approval

---

# 7️⃣ Invalid Currency Codes

## Problem

Currency does not match supported formats.

### Example

```csv
XYZ123
```

## Risk

Currency conversion errors

## Handling Strategy

* Flag record
* Prevent automatic import

---

# 8️⃣ Orphan Members

## Problem

Expense references a member that does not exist.

### Example

```csv
Member = John
```

but John is not registered in the selected group.

## Risk

Broken relationships

## Handling Strategy

* Reject record
* Request member mapping

---

# 9️⃣ Inactive Members

## Problem

Expense assigned to inactive users.

## Risk

Incorrect balance calculations

## Handling Strategy

* Flag record
* Require validation

---

# 🔟 Outlier Expenses

## Problem

Expense amount significantly differs from normal values.

### Example

```csv
20
30
25
18
50000
```

## Risk

Potential typing errors

## Handling Strategy

* Statistical outlier detection
* User review before approval

---

# 1️⃣1️⃣ Corrupted Records

## Problem

Malformed CSV structure.

### Example

```csv
Aisha,500
Rahul
```

## Risk

Import failure

## Handling Strategy

* Reject record
* Log parsing error

---

# 1️⃣2️⃣ Special Character Validation

## Problem

Unexpected symbols in names.

### Example

```csv
A!sh@#
```

## Risk

Data consistency issues

## Handling Strategy

* Validation before insertion

---

# 📊 Anomaly Handling Workflow

```text
CSV Upload
     │
     ▼
Schema Validation
     │
     ▼
Data Validation
     │
     ▼
Anomaly Detection
     │
     ▼
Review Queue
     │
     ▼
Approve / Reject
     │
     ▼
Database Storage
```

---

# 🗄️ Database Schema

The application uses SQLite as its primary storage layer.

---

## Users Table

Stores authentication information.

| Column        | Type    | Description        |
| ------------- | ------- | ------------------ |
| user_id       | INTEGER | Primary Key        |
| username      | TEXT    | Login username     |
| password_hash | TEXT    | Encrypted password |

---

## Groups Table

Stores expense groups.

| Column     | Type    |
| ---------- | ------- |
| group_id   | INTEGER |
| group_name | TEXT    |
| created_by | INTEGER |

---

## Members Table

Stores group participants.

| Column      | Type    |
| ----------- | ------- |
| member_id   | INTEGER |
| group_id    | INTEGER |
| member_name | TEXT    |

---

## Expenses Table

Stores all recorded expenses.

| Column     | Type    |
| ---------- | ------- |
| expense_id | INTEGER |
| group_id   | INTEGER |
| paid_by    | INTEGER |
| amount     | REAL    |
| category   | TEXT    |
| date       | DATE    |

---

## Settlements Table

Stores generated settlement transactions.

| Column        | Type    |
| ------------- | ------- |
| settlement_id | INTEGER |
| payer_id      | INTEGER |
| receiver_id   | INTEGER |
| amount        | REAL    |

---

## Import Logs Table

Stores CSV import history.

| Column        | Type      |
| ------------- | --------- |
| log_id        | INTEGER   |
| file_name     | TEXT      |
| import_time   | TIMESTAMP |
| anomaly_count | INTEGER   |

---

# 🔄 Database Relationships

```text
Users
  │
  └── Groups
          │
          └── Members
                  │
                  └── Expenses
                          │
                          └── Settlements

CSV Imports
      │
      └── Import Logs
```

---

# 📈 Expected Outcomes

By validating imported data before storage, SplitBee aims to:

* Improve financial accuracy
* Reduce duplicate transactions
* Prevent corrupted records
* Increase user trust
* Maintain transparent audit trails

The anomaly detection and approval workflow ensure that only validated expense records are used for balance calculations and settlement generation.
