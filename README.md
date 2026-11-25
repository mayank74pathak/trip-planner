# Trip Planner

A full-stack trip planning app. Users sign up, create trips (destination, dates, number of travelers, budget), and generate a day-by-day itinerary with AI. The itinerary is produced by an OpenAI model that can call tools on a separate **MCP (Model Context Protocol) server** to look up attractions and estimate trip costs against the budget.

 

## Features

- Account registration and login with JWT authentication
- Create, view, edit and delete trips (each user sees only their own trips)
- AI-generated itineraries organized by day, with morning, afternoon and evening plans, estimated costs, a budget summary and travel tips
- Itineraries saved to PostgreSQL, so they can be reopened later
- MCP tool server the model calls while planning:
  - `search_attractions`: sample attractions for supported destinations (Goa, Jaipur, Delhi)
  - `estimate_trip_cost`: breaks costs down into accommodation, food, transport and activities (in INR) and checks them against the budget

## Architecture

```
┌──────────────┐   REST + JWT    ┌──────────────────┐  Streamable HTTP  ┌──────────────┐
│   Frontend   │ ──────────────▶ │     Backend      │ ────────────────▶ │  MCP server  │
│ React + Vite │                 │     FastAPI      │                   │   FastMCP    │
└──────────────┘                 └──────────────────┘                   └──────────────┘
                                    │          │
                                    ▼          ▼
                              PostgreSQL   OpenAI Responses API
```

When a user generates an itinerary, the backend connects to the MCP server, discovers its tools, and hands them to the OpenAI model as function tools. The backend runs the model's tool calls on the MCP server and passes the results back, for up to 6 rounds, until the model returns the finished itinerary.

## Tech stack

| Layer      | Technologies |
|------------|--------------|
| Frontend   | React 19, Vite, React Router, Axios |
| Backend    | FastAPI, SQLAlchemy, PostgreSQL (psycopg), Pydantic, python-jose (JWT), pwdlib (Argon2) |
| AI         | OpenAI Responses API (default model `gpt-5-mini`), MCP Python SDK |
| MCP server | `mcp` FastMCP over Streamable HTTP |

## Project structure

```
trip-planner/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, routers
│   │   ├── database.py        # SQLAlchemy engine and session
│   │   ├── models/            # User, Trip, Itinerary tables
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── routes/            # /auth and /trips endpoints
│   │   └── services/          # auth, itinerary prompt, MCP + OpenAI client
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/             # Login, Register, Dashboard, CreateTrip, EditTrip
│   │   ├── services/api.js    # Axios client with JWT interceptor
│   │   └── App.jsx            # Routes and protected-route wrapper
│   └── package.json
└── mcp-server/
    ├── server.py              # MCP tools: search_attractions, estimate_trip_cost
    └── requirements.txt
```

## Getting started

### Prerequisites

- Python 3.10+
- Node.js 20+
- A PostgreSQL database
- An OpenAI API key

### 1. MCP server

```bash
cd mcp-server
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

The server listens on port `8001` by default (set `PORT` to change it), and its MCP endpoint is `http://127.0.0.1:8001/mcp`.

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/trip_planner
SECRET_KEY=replace-with-a-long-random-string
ALGORITHM=HS256
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-mini
MCP_SERVER_URL=http://127.0.0.1:8001/mcp
```

Run the API:

```bash
uvicorn app.main:app --reload
```

The tables are created automatically on startup. Interactive API docs are at http://127.0.0.1:8000/docs.

> **Local development note:** CORS in `backend/app/main.py` only allows the deployed Vercel URLs. Add `http://localhost:5173` to `allow_origins` when running the frontend locally.

### 3. Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the dev server:

```bash
npm run dev
```

Open http://localhost:5173.

## Environment variables

| Variable | Service | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Backend | SQLAlchemy connection URL for PostgreSQL |
| `SECRET_KEY` | Backend | Secret used to sign JWTs |
| `ALGORITHM` | Backend | JWT algorithm (default `HS256`) |
| `OPENAI_API_KEY` | Backend | OpenAI API key |
| `OPENAI_MODEL` | Backend | Model used for itineraries (default `gpt-5-mini`) |
| `MCP_SERVER_URL` | Backend | MCP endpoint (default `http://127.0.0.1:8001/mcp`) |
| `PORT` | MCP server | Port to listen on (default `8001`) |
| `VITE_API_BASE_URL` | Frontend | Base URL of the backend API |

## API reference

All `/trips` endpoints need an `Authorization: Bearer <token>` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Create an account (`name`, `email`, `password`) |
| `POST` | `/auth/login` | Log in and receive an access token |
| `GET` | `/trips/` | List the current user's trips |
| `POST` | `/trips/` | Create a trip (`destination`, `start_date`, `end_date`, `travelers`, `budget`) |
| `GET` | `/trips/{trip_id}` | Get one trip |
| `PUT` | `/trips/{trip_id}` | Update a trip (any field) |
| `DELETE` | `/trips/{trip_id}` | Delete a trip and its itinerary |
| `POST` | `/trips/{trip_id}/generate-itinerary` | Generate (or regenerate) and save the AI itinerary |
| `GET` | `/trips/{trip_id}/itinerary` | Get the saved itinerary |

## Deployment

The frontend is deployed on Vercel. The MCP server reads the `PORT` Render assigns, so it can run as a Render web service. The backend can be hosted anywhere that runs FastAPI. Point its `MCP_SERVER_URL` at the deployed MCP server's `/mcp` endpoint, and add the frontend's domain to the CORS `allow_origins` list.

## Limitations

- Attraction data is a small built-in sample covering Goa, Jaipur and Delhi. Other destinations rely on the model's own knowledge.
- All costs are estimates. The app does not check live prices, availability or bookings.

## License

[MIT](LICENSE) © 2026 Mayank Pathak
