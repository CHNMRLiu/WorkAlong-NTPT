# WorkBuddy-NTPT · 长泵能碳管理系统

> **Energy & Carbon Management System** for industrial enterprises — monitoring energy
> consumption, energy efficiency, and carbon emissions in one unified platform.
>
> 面向制造企业的能源与碳排放数字化管理平台，覆盖能源消费、能效测评、能流平衡与碳核算/存证全流程。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. Features · 功能特性

- **Energy consumption management** · 能源消费：电 / 天然气 / 水等多能源类型，表计读数自动折算费用、标准煤、碳排放
- **Energy analysis** · 能源分析：同比环比、能耗结构、部门/产品能耗强度
- **Efficiency evaluation** · 能效测评：单位产值 / 单位产品能耗强度
- **Energy flow & balance** · 能流平衡：支持手工或"一键生成"的桑基能流图（Sankey）
- **Carbon accounting** · 碳核算：范围 1/2/3 排放源活动数据录入，自动按排放因子计算排放量
- **Carbon evidence** · 碳核算存证：核算记录可一键生成存证编号并登记上链信息，避免重复存证
- **Dashboards & big screen** · 看板与大屏：综合能耗、碳排总量、强度指标可视化

---

## 2. Tech Stack · 技术栈

| Layer      | Technology                                              |
|------------|---------------------------------------------------------|
| Frontend   | Vue 3 · Vite · Element Plus · ECharts · Pinia · Vue Router |
| Backend    | FastAPI · SQLAlchemy 2.0 · Pydantic · Uvicorn            |
| Database   | PostgreSQL 15                                           |
| Web Server | Nginx (serves built SPA + reverse-proxies `/api`)        |
| Deploy     | Docker Compose (Linux / Windows / macOS)                 |

---

## 3. Project Structure · 目录结构

```
WorkBuddy-NTPT/
├── backend/                 # FastAPI 后端服务
│   ├── app/                 # 应用代码（api / models / schemas / database）
│   ├── init_db.py           # 启动建表 + 种子数据
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                # Vue 3 前端
│   ├── src/
│   ├── nginx.conf           # 容器内的 Nginx 反代配置
│   ├── vite.config.js
│   └── Dockerfile           # 多阶段构建：node build → nginx serve
├── docker-compose.yml       # 一键编排 db + backend + frontend
├── LICENSE
└── README.md
```

---

## 4. Quick Start · 快速开始

### 4.1 Docker (recommended) · 推荐方式

Requires Docker Engine 20.10+ and Docker Compose v2. Works on **Linux, Windows (Docker Desktop), and macOS**.

```bash
# 1. Clone
git clone https://github.com/CHNMRLiu/WorkBuddy-NTPT.git
cd WorkBuddy-NTPT

# 2. Build & start (first run pulls base images, may take a few minutes)
docker compose up -d --build

# 3. Open in browser
#    Web UI:      http://localhost          (or http://localhost:18080 if you remapped ports)
#    API docs:    http://localhost:8000/docs
```

The database, tables, and seed data (energy types, emission sources) are created
automatically on first backend start.

> **Port conflict?** If the default host ports (`80`, `8000`, `5432`) are occupied,
> edit the `ports:` mapping on the left side of `docker-compose.yml`, e.g.
> `18080:80`, `18000:8000`, `15432:5432`. The container-internal network is unaffected.

To stop / remove:

```bash
docker compose down            # stop containers (keeps data volume)
docker compose down -v         # stop AND delete the database volume
```

### 4.2 Local development without Docker · 本地开发（无容器）

#### Prerequisites
- Python 3.11+
- Node.js 18+
- A running PostgreSQL 15 instance

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# set env vars (Linux/macOS)
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/energy_carbon
export SECRET_KEY=change-me-to-a-random-string
# Windows (PowerShell):
#   $env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/energy_carbon"
#   $env:SECRET_KEY="change-me-to-a-random-string"

python init_db.py            # create tables + seed data
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev                  # dev server on http://localhost:5173 (proxies /api -> :8000)
# production build:
npm run build                # outputs dist/ (serve with any static server / nginx)
```

---

## 5. Default Login · 默认账号

| Username | Password  |
|----------|-----------|
| `admin`  | `admin123`|

> Change the password after first login in a production environment.

---

## 6. Configuration · 配置项

| Variable       | Default (compose)                                  | Description                          |
|----------------|----------------------------------------------------|--------------------------------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@db:5432/energy_carbon` | SQLAlchemy DB connection string   |
| `SECRET_KEY`   | `energy-carbon-system-2026-dev-secret-change-me`   | JWT / session signing secret (override in prod) |

Frontend is built as a static SPA; the API base path is `/api`, reverse-proxied by
Nginx inside the `frontend` container. No frontend env var is required for the
default Docker deployment.

---

## 7. License · 许可证

Released under the [MIT License](LICENSE).
