# 📋 Decision Log

This document records the major technical and product decisions made during the development of SplitBee, including alternatives considered, trade-offs evaluated, and the reasoning behind final choices.

---

# 🎯 Project Goal

The original goal was to build a simple shared expense tracker capable of recording expenses and calculating balances between group members.

During development, the scope expanded to include:

* Multiple expense splitting methods
* Settlement optimization
* CSV imports
* Anomaly detection
* Approval workflows
* Reporting and audit logs

As requirements evolved, several technical and architectural decisions were revisited and refined.

---

# Decision 1: Choosing Streamlit for the Frontend

## Options Considered

### Option A

* React + FastAPI
* Separate frontend and backend

### Option B

* Django
* Full-stack web framework

### Option C ✅ (Chosen)

* Streamlit

## Why Streamlit?

The project focused primarily on:

* Expense logic
* Data processing
* User workflows
* Reporting

rather than building a production-grade frontend.

Streamlit enabled:

* Faster prototyping
* Rapid UI development
* Direct integration with Python
* Easier deployment
* Reduced development overhead

## Trade-Off

Accepted less frontend flexibility in exchange for significantly faster development.

---

# Decision 2: Database Selection

## Initial Thought

A more scalable database such as:

* MySQL
* PostgreSQL

was considered.

## Final Choice ✅

SQLite

## Why?

The application requirements involved:

* Lightweight storage
* Local deployment
* Simple setup
* Minimal configuration

SQLite provided:

* Zero server setup
* Easy portability
* Sufficient performance for project requirements

## Trade-Off

Less scalability than enterprise databases but significantly easier deployment.

---

# Decision 3: CSV Import Support

## Initial Version

The project initially supported only manual expense entry.

## Problem

Manual entry became inefficient for:

* Large expense datasets
* Existing expense records
* Bulk imports

## Final Decision ✅

Add CSV import capability.

## Benefits

* Faster onboarding
* Bulk data processing
* Improved usability

---

# Decision 4: Introducing Anomaly Detection

## Initial Approach

Imported data was inserted directly into the database.

## Problem

Potential issues included:

* Duplicate records
* Invalid dates
* Negative amounts
* Missing values

## Final Decision ✅

Create an anomaly detection layer before database insertion.

## Why?

Improves:

* Data quality
* Reliability
* User trust

This transformed the application from a simple tracker into a data-aware expense management platform.

---

# Decision 5: Approval Workflow Before Import

## Initial Design

Detected anomalies were displayed but had no review process.

## Problem

Users needed control over import decisions.

## Final Decision ✅

Introduce an approval workflow.

## Benefits

* Human validation
* Better transparency
* Auditability

---

# Decision 6: Expense Splitting Strategy

## Initial Version

Only equal expense splitting was supported.

## Problem

Real-world expense sharing is rarely equal.

Examples:

* One member pays a larger share.
* Expenses are divided by percentage.
* Costs are distributed by weighted participation.

## Final Decision ✅

Support multiple splitting methods.

### Implemented

* Equal Split
* Percentage Split
* Exact Amount Split
* Share-Based Split

## Result

The application became flexible enough for real-world scenarios.

---

# Decision 7: Settlement Optimization

## Initial Version

The application only displayed balances.

## Problem

Users still had to manually determine settlements.

## Example

Instead of:

* A pays B
* B pays C
* C pays D

there may be a simpler settlement path.

## Final Decision ✅

Implement settlement optimization.

## Outcome

Reduced transaction complexity and improved user experience.

---

# Decision 8: Workflow Redesign (Iteration 1)

## Original Flow

```text
Add Expense
      ↓
View Expenses
      ↓
Calculate Balance
```

## Problem

The workflow felt disconnected.

Users could not easily understand how expenses affected settlements.

## Revised Flow

```text
Add Expense
      ↓
Calculate Shares
      ↓
Update Balances
      ↓
Generate Settlements
```

## Result

Improved clarity and user understanding.

---

# Decision 9: Workflow Redesign (Iteration 2)

## Original Import Flow

```text
Upload CSV
      ↓
Insert into Database
```

## Problem

Invalid data could enter the system.

## Revised Flow

```text
Upload CSV
      ↓
Validate Data
      ↓
Detect Anomalies
      ↓
Review Records
      ↓
Approve Import
      ↓
Store in Database
```

## Result

Significantly improved reliability and data quality.

---

# Decision 10: Workflow Redesign (Iteration 3)

## Earlier Structure

Modules operated independently.

## Problem

Expense tracking, settlements, and reporting felt disconnected.

## Final Structure

```text
Expense Added
      ↓
Split Calculation
      ↓
Balance Engine
      ↓
Settlement Engine
      ↓
Reports
```

## Result

Created a complete end-to-end workflow.

---

# Decision 11: Development Environment

## Initial Environment

Visual Studio Code

## Challenges Encountered

During rapid feature expansion:

* Frequent context switching
* Repeated explanation of project state
* Manual tracking of architectural changes
* Multiple workflow redesigns

## Final Choice ✅

ChatGPT Antigravity-assisted development workflow.

## Why?

Antigravity provided:

* Better long-form project reasoning
* Faster iteration cycles
* Context-aware design discussions
* Documentation generation
* Architecture refinement support

## Impact

Development became more focused on problem-solving and system design rather than repetitive setup and context reconstruction.

---

# Decision 12: Documentation Strategy

## Initial Approach

Basic README only.

## Problem

The growing scope made the project harder to understand.

## Final Decision ✅

Create dedicated documentation:

* README.md
* AI_USAGE.md
* DECISIONS.md

## Benefits

* Improved maintainability
* Better project transparency
* Easier onboarding for reviewers and contributors

---

# Lessons Learned

Throughout development, several assumptions changed:

1. The project evolved from a simple expense tracker into a workflow-driven expense management platform.

2. Data validation became as important as expense tracking.

3. User experience depended heavily on workflow clarity.

4. Settlement optimization provided significantly more value than balance display alone.

5. Multiple design iterations were necessary before arriving at the current architecture.

6. Documentation and decision tracking became critical as project complexity increased.

---

# Final Outcome

The final architecture balances:

* Simplicity
* Usability
* Data reliability
* Transparency
* Maintainability

while remaining lightweight enough to deploy and operate using Streamlit and SQLite.

The project evolved through multiple iterations, with each major decision driven by usability, reliability, and development efficiency considerations.
