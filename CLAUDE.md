# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands and Development Workflow

### Local Development
```bash
# Install dependencies
cd api && pip install -r requirements.txt

# Setup pre-commit hooks
pip install pre-commit==4.3.0
pre-commit install

# Start development server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Run tests
python -m pytest -q --cov=./ --cov-report=term-missing

# Lint and format (using ruff)
ruff check .
ruff format .
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yaml up

# Build API image only
docker build -t api:latest ./api
```

## Project Architecture

### Technology Stack
- **Language**: Python 3.12
- **Framework**: FastAPI (async)
- **Purpose**: WeChat Work bot service with LLM integration

### Directory Structure
```
api/                          # Main application
├── app.py                   # FastAPI entry point
├── controller/              # HTTP route handlers
├── core/                    # Business logic
│   ├── wecom/              # WeChat Work integration
│   ├── llm/                # LLM client integration
│   └── stream_manager.py   # Stream state management
├── service/                 # Business services
├── utils/                   # Utilities (config, logging)
└── tests/                   # Test suites
```

### Key Components
- **Controllers**: Handle HTTP requests (`health_controller.py`, `wecom_callback_controller.py`)
- **Core**: Domain logic (WeChat Work crypto, LLM integration, streaming)
- **Services**: Business logic layer for WeChat Work operations
- **Utils**: Configuration, logging, error handling

## Environment Setup

Required environment variables (see `api/utils/config.py`):
- `WECOM_TOKEN`: WeChat Work verification token
- `WECOM_ENCODING_AES_KEY`: Encryption key
- `WECOM_CORP_ID`: WeChat Work corporation ID
- `OPENAI_API_KEY`: OpenAI API key
- `LOG_LEVEL`: Logging level (default: INFO)

## Testing

Test structure:
- **Unit tests**: `api/tests/unit_tests/`
- **Integration tests**: `api/tests/integration_tests/`
- **Coverage**: pytest-cov for code coverage

## CI/CD

GitHub Actions workflows:
- `api-tests.yml`: Run pytest on PR changes
- `build-push.yml`: Build and push Docker images
- `claude-code-review.yml`: AI-powered code review
- `style.yml`: Ruff linting and formatting
- `deploy.yml`: Automated deployment
