# FastTodo: A Production-Ready Todo Application

A modern, secure, and scalable Todo application built with **FastAPI** and **MongoDB**, enhanced by AI-powered development tools.

## 📌 About This Project

FastTodo is a **reference implementation** for building production-grade APIs with FastAPI.
It emphasizes documentation, testing, and structured decision-making.

**Key aspects:**
- Architectural decisions documented in [ADRs](docs/adr/)
- Development workflow with pre-commit hooks and conventional commits
- AI-assisted development using modern tooling (Copilot, Claude, Gemini)

## 📚 Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - Full system architecture and technical decisions
- **[Project Roadmap](docs/ROADMAP.md)** - Phases, priorities, and technical debt
- **[ADRs](docs/adr/)** - Key architectural decisions and their rationale
- **[Test Plan](docs/test-plan.md)** - Comprehensive testing and QA checklist
- **[Agent Context](AGENTS.md)** - Quick reference for AI agents and new developers
- **[API Docs (Live)](https://to-do-4w0k.onrender.com/docs)** - Interactive Swagger documentation

## 🔄 Major Updates & Migrations

### Pydantic v2 Migration
- ✅ Successfully migrated from Pydantic v1 to v2
- ✅ Updated model configurations using `ConfigDict`
- ✅ Implemented new validation patterns for models
- ✅ Enhanced serialization methods for MongoDB `ObjectId`
- ✅ Updated settings management with `pydantic_settings`

### MongoDB Integration Enhancements
- ✅ Implemented connection pooling with timeout management
- ✅ Added robust error handling for database operations
- ✅ Integrated health checks for MongoDB connectivity
- ✅ Implemented proper database session management

### Security Improvements
- ✅ Implemented JWT-based authentication with refresh tokens
- ✅ Added token expiration and refresh mechanisms
- ✅ Enhanced password security with bcrypt hashing
- ✅ Implemented strict user data isolation
- ✅ Added request middleware for authentication

### Testing Infrastructure
- ✅ Comprehensive test suite with pytest
- ✅ Integration tests for user-todo associations
- ✅ Automated test coverage reporting
- ✅ Configured pytest with coverage tracking

### CORS Implementation
- ✅ Configurable CORS middleware with environment-based settings
- ✅ Support for multiple origins, methods, and headers
- ✅ Wildcard and specific origin configuration
- ✅ Comprehensive CORS testing suite

## 🛠️ Technology Stack

### **Core Technologies**
- **FastAPI** - High-performance, modern Python web framework
- **MongoDB** - Flexible, scalable NoSQL database
- **Pydantic v2** - Advanced data validation and settings management with latest features
  - Modern serialization patterns
  - Enhanced type annotations support
  - Improved performance and validation
- **Docker** - Containerized deployment with security best practices
- **pytest** - Comprehensive testing framework with 80%+ coverage

### **AI Development Tools**
- **Chat GPT** - Research, code analysis, and architectural guidance
- **Perplexity AI** - New feature suggestion, Issue tracking
- **GitHub Copilot** - Code completion and generation
- **Qodo / Comet** - Automated test generation
- **Gemini Code Assist** - Automated pull request code review
- **AI Agents (Antigravity, Claude, Copilot Agent)** - Development assistance, bug fixes, and optimization

## 📋 Current Status & Roadmap

### ✅ Implemented Features
- User registration and authentication (JWT-based)
- Todo CRUD operations with priority levels
- MongoDB integration with proper connection handling
- Docker containerization
- CI/CD pipeline with GitHub Actions
- Comprehensive API documentation with Swagger/OpenAPI
- CORS middleware with configurable origins, methods, and headers
- Rate limiting on authentication endpoints
- Pre-commit hooks for code quality (Ruff linting and formatting)

> For project roadmap and priorities, see [ROADMAP.md](docs/ROADMAP.md).

## 🏗️ Architecture

```
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Application configuration and settings
│   ├── models/              # Pydantic v2 models and schemas
│   │   ├── base.py          # Base model with common fields
│   │   ├── todo.py          # Todo-related models
│   │   └── user.py          # User authentication models
│   ├── routers/             # API route handlers
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── todo.py          # Todo CRUD operations
│   │   └── user.py          # User management
│   ├── database/            # Database connection and utilities
│   │   └── mongodb.py       # MongoDB client configuration
│   ├── utils/               # Utility functions and constants
│   │   ├── constants.py     # Application constants
│   │   ├── health.py        # Health check utilities
│   │   └── validate_env.py  # Environment validation
│   └── tests/               # Test suite with 80%+ coverage
│       ├── test_main.py     # Application-level tests
│       ├── test_integration_todo_user.py  # Integration tests
│       ├── routers/         # Router-specific tests
│       ├── database/        # Database integration tests
│       ├── models/          # Model tests
│       └── utils/           # Utils tests
├── .github/
│   └── workflows/           # CI/CD configuration
├── Dockerfile              # Secure container configuration
├── docs/
│   ├── ARCHITECTURE.md             # Full system specification
│   ├── test-plan.md        # Comprehensive test plan
│   └── adr/                # Architecture Decision Records
├── AGENTS.md               # AI agent quick reference
├── .pre-commit-config.yaml # Pre-commit hooks configuration
├── conftest.py             # Pytest shared fixtures
├── pytest.ini              # Test configuration
├── ruff.toml               # Ruff linter/formatter configuration
├── requirements.txt        # Python dependencies
├── .coveragerc             # Coverage configuration
└── .env.example            # Environment configuration template
```

## 🚀 Quick Start

### Prerequisites
- Python 3.13
- Docker (optional)
- MongoDB Atlas account or local MongoDB instance

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/sajankp/to-do.git
   cd to-do
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB credentials and secrets
   ```

3. **Build and run with Docker**
   ```bash
   docker build -t fasttodo .
   docker run -p 80:80 --env-file .env fasttodo
   ```

4. **Access the application**
   - API Documentation: http://localhost/docs
   - Health Check: http://localhost/health

### Option 2: Local Development

1. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload --port 80
   ```

## 🔐 Environment Configuration

Create a `.env` file with the following variables:

```env
# Database Configuration
MONGO_USERNAME=your_mongodb_username
MONGO_PASSWORD=your_mongodb_password
MONGO_HOST=cluster0.example.mongodb.net
MONGO_DATABASE=fasttodo
MONGO_TODO_COLLECTION=todos
MONGO_USER_COLLECTION=users
MONGO_TIMEOUT=5

# Security Configuration
SECRET_KEY=your-super-secret-key-here
PASSWORD_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_SECONDS=1800
REFRESH_TOKEN_EXPIRE_SECONDS=3600

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_AUTH=5/minute
# REDIS_URL=redis://localhost:6379/0  # Optional: for distributed rate limiting

# CORS Configuration
# For development: Use "*" or specify localhost origins
# For production: Specify exact allowed origins (comma-separated)
CORS_ORIGINS=*
# CORS_ORIGINS=http://localhost:3000,http://localhost:8080,https://yourdomain.com
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_METHODS=*
CORS_ALLOW_HEADERS=*

# Application Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development
```

## 🧪 Testing

> For comprehensive testing guidelines, see [docs/test-plan.md](docs/test-plan.md).

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest app/tests/routers/test_auth.py -v
```


## 📊 API Documentation

### Authentication Endpoints
- `POST /token` - Login and receive JWT tokens
- `POST /token/refresh` - Refresh access token
- `POST /user` - User registration

### Todo Management
- `GET /todo/` - List user's todos (paginated)
- `POST /todo/` - Create new todo
- `GET /todo/{id}` - Get specific todo
- `PUT /todo/{id}` - Update todo
- `DELETE /todo/{id}` - Delete todo

### User Management
- `GET /user/me` - Get current user information

### System Endpoints
- `GET /` - Root endpoint
- `GET /health` - Application health check

## 🤖 AI-Assisted Development

This project leverages multiple AI tools for enhanced development experience:

### **Perplexity**
- **Code Analysis**: Deep repository analysis and improvement suggestions
- **Research**: Latest best practices and security recommendations
- **Architecture**: Design pattern guidance and scalability advice
- **Documentation**: README and docstring generation
- **Bug Generation**: Identify and report bugs

### **GitHub Copilot / Qodo**
- **Test Generation**: Automated test case creation

### **Comet**
- **Automated Testing**: Run the tests defined in [docs/test-plan.md](https://github.com/sajankp/to-do/blob/main/docs/test-plan.md)

### **AI Agent Workflow**
- **Bug Fix**: Automated Bug Fix ✅
- **Security Scanning**: Make use of Github Code Analysis ✅
- **Test Generation**: Automated test case creation ✅
- **Code Review**: Automated pull request analysis ✅
- **Performance Optimization**: Automated performance bottleneck identification (planned)

## 🔒 Security

For security architecture details, see [ARCHITECTURE.md](docs/ARCHITECTURE.md#security-architecture).


## 🚀 Deployment

### Production Deployment
The application is designed for cloud deployment with the following considerations:

- **Container Security**: Non-root user, minimal base image
- **Secret Management**: External secret injection
- **Health Checks**: Kubernetes/Docker health endpoints
- **Monitoring**: Prometheus metrics and logging
- **Scaling**: Horizontal pod autoscaling support

### Supported Platforms
- **Render** (Current deployment)
- **Docker/Kubernetes**
- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Instances**

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow and guidelines.




## 📄 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** community for excellent framework and documentation
- **MongoDB** for flexible and scalable database solutions
- **Perplexity** for intelligent code analysis and research assistance
- **GitHub Copilot** for AI-powered development enhancement
- **Open Source Community** for inspiring best practices and continuous learning

## 📞 Support & Contact

- **Live API**: https://to-do-4w0k.onrender.com/docs
- **GitHub Issues**: [Create an issue](https://github.com/sajankp/to-do/issues)
- **Documentation**: Available in `/docs` endpoint when running
- **Developer**: [sajankp](https://github.com/sajankp)

---

**Built with ❤️ using AI-assisted development practices**
