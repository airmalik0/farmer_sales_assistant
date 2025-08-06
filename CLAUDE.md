# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Farmer CRM is a multi-service customer relationship management system with AI-powered communication analysis capabilities. The project uses a microservices architecture with three main components: backend API (FastAPI), frontend web app (React), and a Telegram admin bot.

## Architecture

### Service Structure
- **Backend** (`/backend/`): FastAPI REST API with PostgreSQL database
  - Core API at `app/api/` - RESTful endpoints for all entities
  - Database models at `app/models/` - SQLAlchemy ORM models
  - Business logic at `app/services/` - Service layer implementations
  - AI agents at `app/services/ai/` - LangGraph-based ReACT agents for communication analysis
  - Background jobs via APScheduler for triggers and automated tasks
  - WebSocket support for real-time communication

- **Frontend** (`/frontend/`): React + TypeScript + Vite application
  - Components at `src/components/` - Reusable UI components
  - Pages at `src/pages/` - Main application views
  - API client at `src/services/api.ts` - Centralized backend communication
  - WebSocket hook at `src/hooks/useWebSocket.ts` - Real-time updates

- **Bot** (`/bot/`): Telegram admin bot using Aiogram 3.x
  - Admin-only commands for system management
  - Broadcasting capabilities

### Key Integrations
- **Pact.im API**: Multi-channel messaging (WhatsApp, Telegram, etc.) via webhook at `/api/v1/webhook/pact`
- **OpenAI**: GPT models for AI-powered analysis through LangChain/LangGraph
- **PostgreSQL**: Primary database for all persistent data
- **WebSocket**: Real-time bidirectional communication between frontend and backend

## Development Commands

### Frontend Development
```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start development server on port 5173
npm run build        # Build for production
npm run lint         # Run ESLint with TypeScript rules
npm run preview      # Preview production build
```

### Backend Development
```bash
cd backend
pip install -r requirements.txt    # Install Python dependencies
alembic upgrade head               # Run database migrations
uvicorn app.main:app --reload --port 8000  # Start development server
python main.py                     # Alternative: run the application directly
```

### Database Operations
```bash
cd backend
alembic revision --autogenerate -m "description"  # Create new migration
alembic upgrade head                              # Apply migrations
alembic downgrade -1                              # Rollback one migration
```

### Docker Operations
```bash
docker-compose up -d      # Start all services in background
docker-compose down       # Stop all services
docker-compose build      # Rebuild containers
docker-compose logs -f    # View logs
```

## API Structure

### Main API Endpoints (Backend port 8000)
- `/api/v1/clients/` - Client management
- `/api/v1/messages/` - Message handling
- `/api/v1/tasks/` - Task management
- `/api/v1/triggers/` - Automation triggers
- `/api/v1/dossiers/` - Client dossiers
- `/api/v1/car_interests/` - Car interest tracking
- `/api/v1/webhook/pact` - Pact.im webhook integration
- `/api/v1/ai/analyze` - AI analysis endpoints
- `/ws` - WebSocket connection endpoint

### Frontend API Configuration
The frontend expects the backend at `http://localhost:8000` (configured in `src/services/api.ts`). Update the `API_URL` constant if the backend runs on a different port or host.

## Database Schema

Key models defined in `/backend/app/models/`:
- `Client` - Customer information and contact details
- `Message` - Communication history across channels
- `Task` - Task management for sales team
- `Trigger` - Automated workflow triggers
- `Dossier` - Detailed client profiles
- `CarInterest` - Vehicle interest tracking
- `TriggerMessage` - Predefined trigger responses

All models use SQLAlchemy ORM with PostgreSQL as the database backend.

## AI Services Architecture

The AI analysis system (`/backend/app/services/ai/`) uses:
- **LangGraph** for orchestrating multi-step AI workflows
- **ReACT agents** for reasoning and action planning
- **OpenAI GPT models** for natural language understanding
- **Structured output** using Pydantic models for type safety

Key AI capabilities:
- Analyze client communications for intent and sentiment
- Extract car interests and requirements
- Generate contextual responses
- Build comprehensive client dossiers

## Environment Configuration

### Backend Environment Variables
Required in `/backend/.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/farmer_crm
OPENAI_API_KEY=your_openai_key
PACT_API_KEY=your_pact_key
SECRET_KEY=your_secret_key
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
```

### Frontend Environment Variables
Optional in `/frontend/.env`:
```
VITE_API_URL=http://localhost:8000
```

## Testing Strategy

### Frontend Testing
- ESLint configured for React + TypeScript
- Run `npm run lint` to check code quality

### Backend Testing
- Use pytest for unit tests (though test files need to be created)
- Test database operations with a separate test database

## Common Development Tasks

### Adding a New API Endpoint
1. Create model in `/backend/app/models/`
2. Create Pydantic schemas in `/backend/app/schemas/`
3. Implement service logic in `/backend/app/services/`
4. Add API route in `/backend/app/api/v1/`
5. Run `alembic revision --autogenerate` to create migration
6. Update frontend API client in `/frontend/src/services/api.ts`

### Adding a New Frontend Component
1. Create component in `/frontend/src/components/`
2. Use TypeScript interfaces for props
3. Follow existing Tailwind CSS patterns for styling
4. Import and use in relevant pages

### Modifying Database Schema
1. Update SQLAlchemy model in `/backend/app/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration file
4. Apply migration: `alembic upgrade head`

## Code Style Guidelines

### Python (Backend)
- Follow PEP 8 conventions
- Use type hints for all function parameters and returns
- Pydantic models for request/response validation
- Async/await for all database operations

### TypeScript (Frontend)
- Use functional components with hooks
- Define interfaces for all props and state
- Consistent file naming: PascalCase for components, camelCase for utilities
- Use absolute imports from 'src/' base path