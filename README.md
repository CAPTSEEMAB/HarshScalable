# Cloud-Native Inventory & Analytics System

A production-ready, microservices-based inventory management and analytics platform built for small-to-medium retail businesses. Powered by **AWS serverless** services, a **React** SPA, and fully automated **CI/CD**.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                      CloudFront CDN                              │
│         ┌──────────────────┬─────────────────────┐               │
│         │  S3 (React SPA)  │  API Gateway / ALB  │               │
│         └──────────────────┴─────────┬───────────┘               │
│                                      │                           │
│  ┌───────────┬───────────┬───────────┼───────────┬─────────────┐ │
│  │ Auth 8001 │Prod 8002  │Inv 8003   │Txn 8004   │Anlyt 8005  │ │
│  │           │           │           │           │             │ │
│  │           │           │  ┌────────┴────────┐  │             │ │
│  │           │           │  │  Res 8006       │  │Notif 8007  │ │
│  └───────────┴───────────┴──┴─────────────────┴──┴─────────────┘ │
│                       ECS Fargate Cluster                        │
│                                                                  │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  DynamoDB    │  │   SQS    │  │  Redis   │  │ Secrets Mgr  │  │
│  │  (10 tables) │  │ (3 + DLQ)│  │ElastiCache│ │              │  │
│  └─────────────┘  └──────────┘  └──────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Services

| Service | Port | Description |
|---------|------|-------------|
| **Auth** | 8001 | JWT auth, registration, login, RBAC, profile management |
| **Product** | 8002 | Product & category CRUD, SKU management |
| **Inventory** | 8003 | Stock tracking per warehouse, transfers, low-stock detection |
| **Transaction** | 8004 | Purchase / sale / return / damage recording |
| **Analytics** | 8005 | Dashboard, ML demand forecasting, SQS consumer |
| **Resource** | 8006 | Supplier recommendations, vendor search, restock guides |
| **Notification** | 8007 | Email alerts via SES/SNS, SQS-driven processing |

---

## Tech Stack

### Backend
- **Python 3.12** / **FastAPI** / **Uvicorn**
- **boto3** – DynamoDB, SQS, SES, SNS, Secrets Manager
- **redis** – caching & rate limiting
- **scikit-learn** – ML demand forecasting (GradientBoosting)
- **python-jose** / **passlib** – JWT & password hashing

### Frontend
- **React 18** / **TypeScript** / **Vite**
- **Tailwind CSS** – utility-first styling
- **Recharts** – analytics charts
- **Axios** – HTTP client with JWT interceptor

### Infrastructure
- **AWS**: ECS Fargate, ALB, API Gateway, CloudFront, DynamoDB, SQS, ElastiCache Redis, S3, ECR, Secrets Manager, SES, SNS, CloudWatch
- **Terraform** – modular IaC (VPC, ECR, DynamoDB, SQS, Redis, S3, Secrets, ECS, CloudFront, API Gateway)
- **Docker Compose** – local development
- **GitHub Actions** – CI (lint/test/validate) + CD (build/push/deploy)

---

## Quick Start – Local Development

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for frontend dev)
- Python 3.12+ (for backend dev)

### 1. Start all services

```bash
docker compose up --build
```

This starts:
- **DynamoDB Local** on port 8000
- **Redis** on port 6379
- All 7 microservices on ports 8001–8007
- Auto-creates all 10 DynamoDB tables

### 2. Start frontend dev server

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — the Vite dev server proxies all API calls to backend services.

### 3. Register & login

1. Navigate to `/register` and create an account
2. Login at `/login`
3. Explore the dashboard, products, inventory, etc.

---

## Production Deployment

### Quick Start

```bash
# 1. Prepare AWS services (DynamoDB, SQS, ElastiCache, Secrets Manager)
# 2. Copy .env.example to .env and configure with AWS credentials
cp .env.example .env
nano .env  # Edit with your AWS settings

# 3. Run setup script
chmod +x setup-production.sh
./setup-production.sh

# 4. Start services
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify deployment
docker-compose -f docker-compose.prod.yml ps
```

### Full Deployment Guide

See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for:
- AWS service setup (DynamoDB, SQS, ElastiCache, Secrets Manager)
- Environment configuration via `.env`
- Docker Compose production deployment
- ECS cluster deployment
- Frontend build & CloudFront deployment
- Monitoring, scaling, and security best practices

### Configuration Reference

All configuration options are documented in [CONFIGURATION.md](CONFIGURATION.md):
- Environment variables for each service
- AWS Secrets integration
- Development vs. production settings
- Security best practices

---

## Project Structure

```
HarshScalable/
├── backend/
│   ├── shared/                  # Shared AWS helpers & JWT auth
│   │   ├── aws_helpers.py
│   │   └── auth.py
│   ├── Dockerfile               # Unified multi-service Dockerfile
│   ├── auth-service/
│   ├── product-service/
│   ├── inventory-service/
│   ├── transaction-service/
│   ├── analytics-service/       # Includes forecaster.py & consumer.py
│   ├── resource-service/
│   └── notification-service/
├── frontend/
│   ├── src/
│   │   ├── pages/               # 10 page components
│   │   ├── components/          # Sidebar, StatCard, ProtectedLayout
│   │   ├── hooks/               # useAuth context
│   │   └── services/            # API client
│   ├── vite.config.ts
│   └── nginx.conf               # Production reverse proxy
├── infra/
│   └── terraform/
│       ├── environments/dev/    # Dev env config
│       └── modules/             # VPC, ECR, DynamoDB, SQS, Redis,
│                                # S3, Secrets, ECS, CloudFront,
│                                # API Gateway
├── .github/workflows/
│   ├── ci.yml                   # Lint, test, validate
│   └── cd.yml                   # Build, push ECR, deploy ECS & S3
└── docker-compose.yml
```

---

## API Endpoints

### Auth Service (`/auth`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, returns JWT tokens |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/profile` | Get current user profile |
| PUT | `/auth/profile` | Update profile |
| DELETE | `/auth/account` | Delete account |
| GET | `/auth/users` | List all users (admin) |

### Product Service (`/products`, `/categories`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/products` | List products (filter by category) |
| POST | `/products` | Create product |
| GET | `/products/{id}` | Get product |
| PUT | `/products/{id}` | Update product |
| DELETE | `/products/{id}` | Delete product |
| GET/POST | `/categories` | List / create categories |

### Inventory Service (`/inventory`, `/warehouses`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/inventory` | List stock records |
| POST | `/inventory/stock-in` | Add stock |
| POST | `/inventory/stock-out` | Remove stock |
| POST | `/inventory/transfer` | Transfer between warehouses |
| GET | `/inventory/history/{product_id}` | Stock movement history |
| CRUD | `/warehouses` | Warehouse management |

### Transaction Service (`/transactions`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/transactions/purchase` | Record purchase |
| POST | `/transactions/sale` | Record sale |
| POST | `/transactions/return` | Record return |
| POST | `/transactions/damage` | Record damage |
| GET | `/transactions/history` | List with filters |
| GET | `/transactions/{id}` | Get transaction |

### Analytics Service (`/analytics`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/analytics/dashboard` | Summary stats |
| GET | `/analytics/low-stock` | Low stock alerts |
| GET | `/analytics/top-products` | Best sellers |
| GET | `/analytics/slow-products` | Slow movers |
| GET | `/analytics/warehouse-performance` | Per-warehouse stats |
| GET | `/analytics/reorder-recommendations` | Reorder suggestions |
| GET | `/analytics/forecast/{product_id}` | ML demand forecast |

### Resource Service (`/resources`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/resources/suppliers` | List suppliers |
| GET | `/resources/recommendations` | Product-based recommendations |
| GET | `/resources/restock-guides` | Restocking best practices |
| GET | `/resources/vendor-search?q=` | Search vendors |

### Notification Service (`/notifications`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/notifications/health` | Service health |
| GET | `/notifications/history` | Notification log |
| POST | `/notifications/send` | Manual send (admin) |

---

## Infrastructure Deployment

### Prerequisites
- AWS account with appropriate permissions
- Terraform 1.7+
- S3 bucket for Terraform state

### Deploy

```bash
cd infra/terraform/environments/dev

# Initialize
terraform init

# Plan
terraform plan -out=tfplan

# Apply
terraform apply tfplan
```

### GitHub Actions Secrets Required

| Secret | Description |
|--------|-------------|
| `AWS_DEPLOY_ROLE_ARN` | IAM role ARN for OIDC federation |

---

## ML Demand Forecasting

The Analytics Service includes a **GradientBoostingRegressor** model that:

1. Aggregates daily transaction data per product
2. Engineers features: day index, day-of-week, 3/7-day moving averages, 7-day volatility/max/min
3. Trains on historical data with 80/20 split
4. Falls back to moving-average forecast if insufficient data (<14 days) or low model score
5. Returns predictions with confidence levels: `high`, `medium`, `low`, `none`

---

## Event-Driven Architecture

```
Inventory Service ──▶ SQS (stock-events) ──▶ Analytics Consumer
                                           ──▶ Notification Service

Transaction Service ──▶ SQS (transaction-events) ──▶ Analytics Consumer

Analytics Service ──▶ SQS (notification-events) ──▶ Notification Service
```

Events emitted: `STOCK_IN`, `STOCK_OUT`, `STOCK_TRANSFER`, `LOW_STOCK_TRIGGERED`, `PURCHASE_CREATED`, `SALE_COMPLETED`, `RETURN_PROCESSED`, `DAMAGE_RECORDED`, `REORDER_RECOMMENDED`

---

## License

MIT
