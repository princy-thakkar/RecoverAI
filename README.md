# RecoverAI 🚀

### AI-Powered Revenue Recovery Platform for Failed Payments

RecoverAI is an intelligent payment recovery platform designed to help businesses recover revenue from failed payments without blindly retrying every transaction.

It combines **machine learning, AI-powered decision making, recovery policies, analytics, and automated recovery workflows** to determine which failed payments are worth recovering, what action should be taken, and when recovery should stop.

🔗 **Live Demo:** https://recoverai-platform.vercel.app/

---

## 📌 Why RecoverAI?

Failed payments can result in significant revenue leakage for businesses.

Traditional recovery systems often rely on fixed retry schedules:

> Payment fails → Retry → Retry again → Retry again

This approach can lead to:

* Unnecessary payment attempts
* Poor customer experience
* Increased payment processing costs
* Repeated retries for non-recoverable failures
* Lost revenue due to ineffective recovery strategies

**RecoverAI takes a smarter approach.**

Instead of retrying every failed payment, RecoverAI evaluates payment context and recovery probability before recommending the most appropriate recovery action.

---

## 💡 What RecoverAI Does

RecoverAI analyzes failed payments and determines the best recovery strategy using a combination of:

* 🤖 AI-powered recovery reasoning
* 📊 Machine-learning-based recovery probability
* 💳 Payment and customer context
* 🛡️ Recovery policies and safety guardrails
* 📈 Revenue and recovery analytics
* 📝 Audit logging
* 🔄 Automated recovery workflows

The system is designed around a simple principle:

### **AI recommends. Policy authorizes.**

The AI can recommend an action, but the policy layer controls whether that action is actually allowed.

---

## ✨ Key Features

### 📊 Revenue Recovery Dashboard

Monitor important recovery metrics such as:

* Revenue at risk
* Recovered revenue
* Failed payments
* Recovery rate
* Recovery attempts
* Recovery opportunities

---

### 💳 Payment Management

RecoverAI provides payment management capabilities including:

* Payment creation
* Payment history
* Payment details
* Payment status tracking
* Failure reason tracking
* Payment attempt tracking

---

### 👥 Customer Management

Manage customer information associated with payment transactions.

Customer records can include:

* Name
* Email
* Phone
* Risk score
* Associated payments

---

### 🧠 ML-Based Recovery Prediction

RecoverAI predicts the probability that a failed payment can be successfully recovered.

The prediction is then used as an input into the recovery decision process.

Example:

```text
Payment
   ↓
Payment & customer context
   ↓
ML recovery probability
   ↓
Recovery decision
   ↓
Recommended action
```

---

### 🤖 AI Recovery Assistant

RecoverAI includes an AI assistant that can help merchants understand their payment recovery data.

The assistant can answer questions related to:

* Failed payments
* Revenue at risk
* Recovery probability
* Recovery opportunities
* Recovery performance
* Recovery strategies
* Payment recovery decisions
* Recovery actions

It also maintains conversation context for payment-related discussions.

---

### 🔄 Intelligent Recovery Actions

RecoverAI can recommend different recovery actions depending on the payment situation:

| Action                      | Purpose                                                       |
| --------------------------- | ------------------------------------------------------------- |
| `SMART_RETRY`               | Retry a payment when recovery is likely                       |
| `PAYMENT_METHOD_SUGGESTION` | Encourage the customer to use another payment method          |
| `REMINDER`                  | Ask the customer to complete or retry payment                 |
| `SUPPORT_ESCALATION`        | Escalate the issue for human assistance                       |
| `STOP`                      | Stop automated recovery when further action isn't appropriate |

---

### 🛡️ Recovery Safety & Guardrails

RecoverAI is designed to avoid uncontrolled automated retries.

The recovery system includes policies such as:

* Maximum recovery attempt limits
* Non-retryable failure handling
* Recovery probability thresholds
* Retry authorization
* Duplicate active recovery prevention
* Protection against retrying already successful/recovered payments
* Audit logging of automated decisions

For example, the current recovery policy limits automated recovery to **3 attempts**.

This helps ensure that automation focuses on **recovering the right revenue rather than retrying everything**.

---

### 📈 Analytics

RecoverAI provides analytics around:

* Revenue recovery
* Recovery rate
* Failed payments
* Payment attempts
* Recovery performance
* Recovery opportunities

The frontend communicates with the backend through a dedicated API service rather than accessing the database directly.

---

### 🧪 Recovery Benchmark

RecoverAI also includes a benchmark system for comparing recovery strategies.

The benchmark tracks metrics such as:

* Revenue at risk
* Revenue recovered
* Recovery rate
* Successful recoveries
* Automated actions
* Customer actions
* Escalations
* Recovery attempts
* Unsafe actions blocked
* Attempts per successful recovery
* Interventions per successful recovery
* Revenue recovered per automated attempt
* Attempt reduction compared with retry-all strategies

This helps evaluate whether intelligent recovery can outperform a simple "retry everything" approach.

---

# 🏗️ Architecture

RecoverAI follows a layered architecture:

```text
┌─────────────────────────────┐
│       React Frontend        │
│        Vite + TypeScript    │
└──────────────┬──────────────┘
               │
               │ HTTP / JSON
               ▼
┌─────────────────────────────┐
│       FastAPI Backend       │
│        API Layer            │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       AI / ML Layer         │
│                             │
│ Recovery Probability        │
│ Recovery Decision           │
│ AI Recovery Agent           │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      Repository Layer       │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│        MongoDB              │
│                             │
│ merchants                   │
│ customers                   │
│ payments                    │
│ payment_attempts            │
│ recovery_cases              │
│ audit_logs                  │
└─────────────────────────────┘
```

The frontend communicates with the backend through the API service, API routes handle HTTP concerns, repositories handle database operations, and the database layer manages MongoDB connections and indexes.

---

# 🛠️ Tech Stack

## Frontend

* React
* TypeScript
* Vite
* Tailwind CSS
* Lucide React

## Backend

* Python
* FastAPI
* Uvicorn
* Pydantic
* Pydantic Settings

## Database

* MongoDB
* Motor
* PyMongo

## AI / ML

* Python
* scikit-learn
* joblib
* pandas
* AI-powered recovery reasoning
* Recovery decision engine

## Authentication & Security

* JWT authentication
* Password hashing with Argon2
* CORS configuration
* Recovery policy guardrails
* Audit logging

The frontend dependencies include React, TypeScript tooling, Vite, Tailwind CSS, and Supabase client support, while the backend requirements include FastAPI, MongoDB drivers, scikit-learn, joblib, pandas, JWT, and password hashing libraries.

---

# 📁 Project Structure

```text
RecoverAI/
│
├── src/
│   ├── components/
│   ├── pages/
│   ├── context/
│   ├── services/
│   │   └── api.ts
│   ├── config/
│   ├── types/
│   └── App.tsx
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── dashboard.py
│   │   │   ├── analytics.py
│   │   │   ├── payments.py
│   │   │   ├── customers.py
│   │   │   ├── recovery_cases.py
│   │   │   ├── payment_attempts.py
│   │   │   ├── audit_logs.py
│   │   │   ├── ml.py
│   │   │   └── ai.py
│   │   │
│   │   ├── agent/
│   │   ├── ai/
│   │   ├── ml/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── core/
│   │   └── db/
│   │
│   ├── tests/
│   ├── scripts/
│   ├── requirements.txt
│   └── .env.example
│
├── docs/
│   └── ARCHITECTURE.md
│
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

---

# 🚀 Getting Started

## Prerequisites

Make sure you have installed:

* Node.js 18+
* npm
* Python 3.10+
* MongoDB / MongoDB Atlas

---

# ⚙️ Frontend Setup

Clone the repository:

```bash
git clone https://github.com/princy-thakkar/RecoverAI.git
cd RecoverAI
```

Install dependencies:

```bash
npm install
```

Create your frontend environment file if required:

```bash
cp .env.example .env
```

Start the development server:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

---

# 🐍 Backend Setup

Move into the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it.

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the environment file:

```bash
cp .env.example .env
```

Configure your MongoDB connection in `.env`.


The repository already provides a `.env.example` with configuration for application settings, CORS, MongoDB, and future LLM integration.

---

# ▶️ Running the Backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/api/health
```

---

# 🧪 Running Tests

From the backend directory:

```bash
pytest tests/ -v
```

You can also run frontend checks using:

```bash
npm run lint
```

and:

```bash
npm run typecheck
```

---

# 🔌 API Overview

Some of the major API capabilities include:

### Authentication

```text
/api/auth/*
```

### Dashboard

```text
/api/dashboard/*
```

### Analytics

```text
/api/analytics/*
```

### Payments

```text
/api/payments/*
```

### Customers

```text
/api/customers/*
```

### Recovery Cases

```text
/api/recovery-cases/*
```

### Machine Learning

```text
/api/ml/predict-recovery
/api/ml/predict-recovery/{payment_id}
/api/ml/create-recovery-case/{payment_id}
/api/ml/execute-recovery/{recovery_case_id}
/api/ml/run-recovery-agent/{payment_id}
```

The ML API supports recovery probability prediction, recovery action selection, recovery-case creation, and automated recovery execution.

### AI Assistant

```text
/api/ai/*
```

### Payment Attempts

```text
/api/payment-attempts/*
```

### Audit Logs

```text
/api/audit-logs/*
```

### Settings

```text
/api/settings/*
```

---

# 🔄 Recovery Flow

A typical RecoverAI recovery flow looks like:

```text
Failed Payment
      │
      ▼
Collect Payment Context
      │
      ▼
Predict Recovery Probability
      │
      ▼
Determine Recommended Action
      │
      ▼
Apply Recovery Policy
      │
      ├───────────────┐
      │               │
      ▼               ▼
Allowed           Blocked
      │               │
      ▼               ▼
Execute Action      STOP
      │
      ▼
Record Payment Attempt
      │
      ▼
Update Recovery Case
      │
      ▼
Write Audit Log
```

This separation ensures that the ML model predicts recovery probability while the decision/policy system determines whether an action is appropriate. The project's architecture documentation explicitly separates these responsibilities.

---

# 🔐 Security & Responsible Automation

RecoverAI is designed with safeguards around automated payment recovery.

Key principles include:

* Never retry successful or already recovered payments
* Limit the number of automated recovery attempts
* Avoid retrying non-retryable failures
* Keep AI recommendations separate from policy authorization
* Maintain an audit trail of automated decisions
* Prevent cross-merchant conversation access
* Protect authenticated API routes

The AI layer itself explicitly prevents policy bypasses and treats policy authorization as a separate control from AI recommendations.

---

# 📊 Data Model

RecoverAI uses MongoDB collections for the core business entities:

```text
merchants
customers
payments
payment_attempts
recovery_cases
audit_logs
```

The repository layer isolates MongoDB access from API routes, making the architecture easier to maintain and extend.

---

# 🧠 AI Decision Philosophy

RecoverAI does **not** follow a simple:

```text
Payment Failed → Retry
```

Instead:

```text
Payment Failed
      ↓
Can this payment realistically recover?
      ↓
What is the recovery probability?
      ↓
What caused the failure?
      ↓
What has already been attempted?
      ↓
What action is most appropriate?
      ↓
Does policy allow that action?
      ↓
Execute / Stop
```

The goal is to maximize **useful recovered revenue while minimizing unnecessary payment interventions**.

---

# 🚧 Current Limitations

RecoverAI is an evolving project.

Some capabilities may still be under development or subject to further refinement, including:

* More advanced ML models
* Production-grade payment provider integrations
* More sophisticated AI/LLM reasoning
* Expanded recovery strategies
* Real-world payment experimentation
* Additional observability and monitoring
* Larger-scale benchmark datasets

---

# 🔮 Future Roadmap

Potential future improvements include:

* [ ] Stripe / Razorpay payment integration
* [ ] Real-time payment webhooks
* [ ] Advanced ML models for recovery prediction
* [ ] LLM-powered recovery reasoning
* [ ] Customer-level recovery personalization
* [ ] Automated email/SMS recovery campaigns
* [ ] A/B testing of recovery strategies
* [ ] Real-time monitoring
* [ ] Advanced merchant analytics
* [ ] Multi-currency optimization
* [ ] Explainable AI recovery decisions
* [ ] Production-grade observability

---

# 🎯 Project Goals

RecoverAI aims to demonstrate how **AI + machine learning + business rules** can be combined to build safer and more effective revenue recovery systems.

The core idea is simple:

> **Don't recover everything. Recover intelligently.**

---

# 🤝 Contributing

Contributions, ideas, and feedback are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/your-feature
```

3. Commit your changes

```bash
git commit -m "Add your feature"
```

4. Push the branch

```bash
git push origin feature/your-feature
```

5. Open a Pull Request

---

# 📄 License

Add your preferred open-source license here, for example **MIT License**, if you intend to distribute the project under MIT.

---

# 👩‍💻 Author

**Princy Thakkar**

Built with ❤️ using React, FastAPI, MongoDB, Machine Learning, and AI.

⭐ If you find RecoverAI interesting, consider giving the repository a star!
