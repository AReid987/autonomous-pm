# Quick Start Guide - Autonomous PM System

## 🚀 Phase 1 Complete!

You now have a fully functional FastAPI + SQLModel backend with GitHub Projects v2 integration.

## What's Been Built

### ✅ Core Features
- **FastAPI Backend** with async support
- **SQLModel Database** with Project, Epic, Task, and User models
- **CRUD Endpoints** for all entities
- **GitHub Projects v2 API** integration
- **Bidirectional Sync** (Kanban ↔ GitHub)
- **Docker Setup** with PostgreSQL and Redis
- **Test Suite** with pytest
- **CLI Tool** for testing

### 📁 Project Structure
```
autonomous-pm/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── database.py          # SQLModel setup
│   ├── models/              # Database models
│   │   ├── project.py
│   │   ├── epic.py
│   │   ├── task.py
│   │   ├── user.py
│   │   └── task_dependency.py
│   ├── api/v1/              # API endpoints
│   │   ├── projects.py
│   │   ├── epics.py
│   │   ├── tasks.py
│   │   └── sync.py
│   └── services/            # Business logic
│       ├── github.py
│       └── sync.py
├── tests/                   # Test suite
├── cli.py                   # CLI tool
├── docker-compose.yml       # Docker setup
├── pyproject.toml           # Dependencies
└── README.md
```

## 🛠️ Setup & Run

### 1. Install Dependencies
```bash
cd code/autonomous-pm
pip install -e ".[dev]"
```

### 2. Configure Environment
```bash
cp env.example .env
# Edit .env with your settings:
# - GITHUB_TOKEN (required)
# - GITHUB_ORG (required)
# - API_SECRET_KEY (generate with: openssl rand -hex 32)
```

### 3. Run Locally
```bash
# Development mode with auto-reload
fastapi dev app/main.py

# Or with uvicorn
uvicorn app.main:app --reload
```

### 4. Run with Docker
```bash
# Start all services (API + PostgreSQL + Redis)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## 🧪 Test the API

### Using the CLI
```bash
# Check health
python cli.py health

# Create a project
python cli.py create-project "My Project" --github-org "your-org"

# List projects
python cli.py list-projects

# Create an epic
python cli.py create-epic "Authentication System" --project-id 1

# Create a task
python cli.py create-task "Implement login" --epic-id 1 --priority high

# View kanban board
python cli.py kanban

# Sync with GitHub
python cli.py sync 1 --repo-owner your-org --repo-name your-repo
```

### Using the API Directly
```bash
# Health check
curl http://localhost:8000/health

# Create project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project", "github_org": "your-org"}'

# List projects
curl http://localhost:8000/api/v1/projects
```

### Using Swagger UI
Visit http://localhost:8000/docs for interactive API documentation.

## 📊 Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api.py -v
```

## 🔄 GitHub Sync Workflow

### 1. Create Local Project
```bash
python cli.py create-project "My App" --github-org "myorg"
```

### 2. Add Epics and Tasks
```bash
python cli.py create-epic "User Management" --project-id 1
python cli.py create-task "Login page" --epic-id 1
python cli.py create-task "Signup page" --epic-id 1
```

### 3. Sync to GitHub
```bash
python cli.py sync 1 --repo-owner myorg --repo-name myapp
```

This will:
- Create a GitHub Project v2
- Create Issues for each Epic (labeled "epic")
- Create Issues for each Task
- Link tasks to their epic
- Add all issues to the project

### 4. Update from GitHub
When you close issues or update them in GitHub, sync back:
```bash
curl -X POST http://localhost:8000/api/v1/sync/projects/1/from-github
```

## 🎯 What's Next - Phase 2

Now that the backend is solid, you can build:

1. **Next.js Frontend** - Web GUI with kanban board
2. **Textual TUI** - Terminal interface
3. **WebSocket Support** - Real-time updates
4. **Agent System** - Doc generation from BMAD/get-shit-done patterns
5. **AI Gateway Integration** - LLM-powered features

## 🐛 Troubleshooting

### Database Issues
```bash
# Reset database
rm autonomous_pm.db
python -c "from app.database import init_db; init_db()"
```

### GitHub API Issues
- Verify your GITHUB_TOKEN has `repo` and `project` permissions
- Check rate limits: https://api.github.com/rate_limit

### Docker Issues
```bash
# Rebuild containers
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## 📚 API Endpoints

### Projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List projects
- `GET /api/v1/projects/{id}` - Get project
- `PATCH /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Epics
- `POST /api/v1/epics` - Create epic
- `GET /api/v1/epics?project_id={id}` - List epics
- `GET /api/v1/epics/{id}` - Get epic
- `PATCH /api/v1/epics/{id}` - Update epic
- `DELETE /api/v1/epics/{id}` - Delete epic

### Tasks
- `POST /api/v1/tasks` - Create task
- `GET /api/v1/tasks?epic_id={id}&status={status}` - List tasks
- `GET /api/v1/tasks/{id}` - Get task
- `PATCH /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task
- `GET /api/v1/tasks/kanban/board` - Get kanban view

### Sync
- `POST /api/v1/sync/projects/{id}?repo_owner={owner}&repo_name={name}` - Full sync
- `POST /api/v1/sync/projects/{id}/from-github` - Sync from GitHub

## 🎉 You're All Set!

Your autonomous PM system backend is ready. Start the server and try creating some projects!
