# Claude Code Action Test Repository

FastAPI web application for testing Kimi K2 model compatibility with Claude Code Action functionality. This repository contains a Python FastAPI application with comprehensive testing, linting, and CI/CD workflows.

**ALWAYS follow these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Bootstrap and Setup (NEVER CANCEL - Network operations may take time)
- Change to the api directory: `cd /home/runner/work/claude-code-action-test/claude-code-action-test/api`
- Install Python dependencies: `pip install -r requirements.txt` 
  - **Takes ~45 seconds. NEVER CANCEL.** Set timeout to 120+ seconds.
  - **May fail due to network timeouts or firewall limitations** - retry if needed

### Code Quality and Linting (Fast operations - complete in under 1 second)
- **Check code style**: `ruff check .`
- **Fix code style issues**: `ruff check . --fix`
- **Format code**: `ruff format .`
- **Check formatting without changes**: `ruff format --check .`
- **Combined fix and format**: `ruff check . --fix && ruff format .`

### Testing (NEVER CANCEL - Tests may take time)
- **Run tests quickly**: `python -m pytest -q`
  - **Takes ~10 seconds. NEVER CANCEL.** Set timeout to 30+ seconds.
- **Run tests with coverage**: `python -m pytest -q --cov=core --cov-report=term-missing`
  - **Takes ~13 seconds. NEVER CANCEL.** Set timeout to 30+ seconds.
- **Full CI-style test run**: `python -m pytest -q --cov=./ --cov-report=term-missing --cov-report=json:coverage.json`
  - **Takes ~13 seconds. NEVER CANCEL.** Set timeout to 30+ seconds.

### Running the Application
- **Method 1 - Direct Python**: `python app.py`
  - Runs on `http://0.0.0.0:8000` (listens on all interfaces)
- **Method 2 - Uvicorn command**: `uvicorn app:app --reload`
  - Runs on `http://127.0.0.1:8000` (localhost only)
  - Use `--reload` for development (auto-restart on code changes)

### Pre-commit Hooks (May fail due to network issues)
- **Install hooks**: `pre-commit install` (takes <1 second)
- **Run on all files**: `pre-commit run --all-files`
  - **WARNING**: May fail with network timeouts when downloading dependencies
  - **Failure is expected in CI environments with network restrictions**
  - Document as: "pre-commit run --all-files -- may fail due to network limitations"

## Validation

### Manual Testing Requirements
**ALWAYS test actual functionality after making changes by running complete user scenarios:**

1. **Start the application** using either method above
2. **Test core endpoints**:
   - `curl http://localhost:8000/echo` - Should return JSON with request details
   - `curl -X POST http://localhost:8000/echo -d "test data"` - Should echo POST data
3. **Verify Swagger UI**: Visit `http://localhost:8000/docs` - Should load interactive API documentation
4. **Check logs**: Application should start without errors and show configuration info

### Essential Pre-commit Validation
**ALWAYS run these commands before committing changes or CI will fail:**
- `ruff check . --fix && ruff format .` (in api/ directory)
- `python -m pytest -q --cov=core --cov-report=term-missing` (in api/ directory)

## Common Tasks

### Repository Structure
```
.
├── .github/workflows/          # CI/CD workflows (api-tests.yml, style.yml)
├── api/                        # Main FastAPI application
│   ├── app.py                 # Main application entry point
│   ├── controller/            # API route controllers
│   ├── core/                  # Business logic (wecom, stream_manager, llm)
│   ├── service/               # Service layer
│   ├── utils/                 # Utilities (config, logging, exceptions)
│   ├── tests/                 # Test suites (unit_tests/, integration_tests/)
│   ├── requirements.txt       # Python dependencies
│   ├── .ruff.toml            # Ruff configuration
│   ├── pytest.ini           # Pytest configuration
│   └── .env.example          # Environment variables template
├── docs/                      # Documentation and task management
├── CLAUDE.md                  # Claude working guidelines
└── README.md                  # Project overview
```

### Key Configuration Files
- **Python version**: 3.12
- **Main dependencies**: FastAPI 0.116.1, uvicorn 0.35.0, pytest 8.4.1, ruff 0.12.8
- **Linting config**: `.ruff.toml` (line length 120, Python 3.12 target)
- **Test config**: `pytest.ini` (testpaths = tests)

### Environment Configuration
- Copy `.env.example` to `.env` if needed for configuration
- Default configuration works for testing (uses mock LLM provider)
- WeChat Work integration requires WECOM_TOKEN and WECOM_ENCODING_AES_KEY

### CI/CD Workflows
- **API Tests** (`.github/workflows/api-tests.yml`): Runs pytest with coverage on api/ changes
- **Style Check** (`.github/workflows/style.yml`): Runs ruff check and format validation

### Quick Reference Commands
```bash
# Setup (run once)
cd /home/runner/work/claude-code-action-test/claude-code-action-test/api
pip install -r requirements.txt  # 45 seconds, timeout 120s

# Development workflow
ruff check . --fix && ruff format .  # Fix code style
python -m pytest -q --cov=core --cov-report=term-missing  # Run tests (13s)
python app.py  # Start application

# Validation
curl http://localhost:8000/echo  # Test API endpoint
# Visit http://localhost:8000/docs for Swagger UI
```

### Common Issues and Solutions
- **pip install fails**: Network timeout/firewall - retry or document as limitation
- **pre-commit fails**: Network issues downloading dependencies - expected in restricted environments
- **Tests fail**: Check if application dependencies are properly installed
- **Import errors**: Ensure you're running commands from the `api/` directory

### Task Management
- Task documentation located in `docs/tasks/`
- Follow CLAUDE.md guidelines for task management workflow
- Each task should have its own markdown document before execution

**CRITICAL REMINDERS:**
- **NEVER CANCEL** long-running operations (pip install, tests)
- **ALWAYS** validate changes by running the application and testing endpoints
- **ALWAYS** run linting and tests before considering work complete
- Set appropriate timeouts: 120s for pip install, 30s for tests