# AI Council - Complete Setup Documentation

Welcome! This document will guide you through setting up your AI Council application with Supabase.

## 📚 Documentation Overview

We've created comprehensive guides to help you get started:

### 🚀 Start Here
- **[QUICK_START.md](QUICK_START.md)** - Get running in 5 minutes
- **[SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)** - Track your progress step-by-step

### 📖 Detailed Guides
- **[SUPABASE_SETUP_GUIDE.md](SUPABASE_SETUP_GUIDE.md)** - Complete Supabase configuration
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Solutions to common issues

### 🔧 Component Documentation
- **[backend/README.md](backend/README.md)** - Backend API documentation
- **[frontend/README.md](frontend/README.md)** - Frontend application guide

### 🚢 Deployment
- **[PRODUCTION_DEPLOYMENT_PLAN.md](PRODUCTION_DEPLOYMENT_PLAN.md)** - Deploy to production

## 🎯 Quick Setup Path

### For Beginners
1. Read [QUICK_START.md](QUICK_START.md)
2. Follow [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)
3. Refer to [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if needed

### For Experienced Developers
1. Run `.\setup-supabase.ps1`
2. Configure environment files
3. Run migrations and start servers

## 🏗️ Architecture Overview

```
AI Council Application
├── Frontend (Next.js 14)
│   ├── React components
│   ├── Tailwind CSS styling
│   ├── Real-time WebSocket
│   └── Supabase integration
│
├── Backend (FastAPI)
│   ├── RESTful API
│   ├── WebSocket support
│   ├── AI orchestration
│   ├── Authentication (JWT)
│   └── Database (PostgreSQL via Supabase)
│
└── Infrastructure
    ├── Supabase (Database + Auth)
    ├── Redis (Caching - optional)
    └── AI Providers (Groq, Together, etc.)
```

## 🔑 Key Features

- ✅ User authentication and authorization
- ✅ AI Council orchestration system
- ✅ Real-time query progress via WebSocket
- ✅ Admin dashboard for system monitoring
- ✅ Query history and analytics
- ✅ Multiple AI provider support
- ✅ Rate limiting and security
- ✅ Responsive modern UI

## 📋 Prerequisites

Before you begin, ensure you have:

- **Node.js 18+** and npm
- **Python 3.11+**
- **Poetry** (Python package manager)
- **Supabase account** (free tier available)
- **Git** (for version control)

Optional but recommended:
- **Docker** (for Redis)
- **VS Code** (recommended editor)

## 🚀 Quick Start Commands

```powershell
# 1. Run setup script
.\setup-supabase.ps1

# 2. Install dependencies
cd backend && python -m poetry install --no-root
cd ../frontend && npm install

# 3. Run migrations
cd backend && python -m poetry run alembic upgrade head

# 4. Start backend (Terminal 1)
cd backend && python -m poetry run uvicorn app.main:app --reload

# 5. Start frontend (Terminal 2)
cd frontend && npm run dev

# 6. Open browser
# http://localhost:3000
```

## 🔐 Environment Configuration

### Backend (.env)
```env
DATABASE_URL=postgresql://postgres.xxxxx:[PASSWORD]@aws-0-region.pooler.supabase.com:6543/postgres
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-super-secret-key-min-32-characters
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

## 🧪 Testing the Setup

1. **Backend Health Check**
   - Visit: http://localhost:8000/api/v1/docs
   - Should see Swagger API documentation

2. **Frontend Check**
   - Visit: http://localhost:3000
   - Should see landing page

3. **Authentication Test**
   - Click "Get Started"
   - Register a new account
   - Login successfully

4. **AI Query Test** (requires API keys)
   - Navigate to dashboard
   - Submit a test query
   - Verify response

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| Database connection fails | Check DATABASE_URL and Supabase status |
| Port 8000 already in use | Kill process or use different port |
| Frontend can't connect | Verify backend is running |
| Migration errors | Check database credentials |
| Redis connection fails | Use Docker or Upstash, or skip for now |

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

## 📦 Project Structure

```
ai-council/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration
│   │   ├── models/         # Database models
│   │   └── services/       # Business logic
│   ├── alembic/            # Database migrations
│   ├── tests/              # Test files
│   └── .env                # Environment variables
│
├── frontend/               # Next.js frontend
│   ├── app/               # App router pages
│   ├── components/        # React components
│   ├── lib/               # Utilities
│   ├── hooks/             # Custom hooks
│   └── .env.local         # Environment variables
│
├── ai_council/            # AI orchestration core
│   ├── analysis/          # Query analysis
│   ├── arbitration/       # Decision making
│   ├── execution/         # AI execution
│   └── synthesis/         # Response synthesis
│
└── docs/                  # Documentation
    ├── QUICK_START.md
    ├── SUPABASE_SETUP_GUIDE.md
    ├── SETUP_CHECKLIST.md
    └── TROUBLESHOOTING.md
```

## 🎓 Learning Resources

### Supabase
- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [PostgreSQL Tutorial](https://www.postgresql.org/docs/current/tutorial.html)

### FastAPI
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)

### Next.js
- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/docs)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

[Your License Here]

## 🆘 Getting Help

- **Documentation**: Start with QUICK_START.md
- **Issues**: Check TROUBLESHOOTING.md
- **Community**: [Your Discord/Forum]
- **Email**: [Your Support Email]

## 🎉 Next Steps

Once your setup is complete:

1. ✅ Explore the admin dashboard
2. ✅ Add your AI API keys
3. ✅ Test the AI Council features
4. ✅ Customize the UI
5. ✅ Deploy to production

Happy coding! 🚀
