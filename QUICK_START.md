# AI Council - Quick Start Guide

Get your AI Council application running in minutes!

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Poetry (Python package manager)
- A Supabase account (free tier works great!)

## 🚀 Quick Setup (5 minutes)

### 1. Set Up Supabase

1. Go to [supabase.com](https://supabase.com) and create an account
2. Create a new project (takes 2-3 minutes to provision)
3. Get your credentials:
   - **Database URL**: Project Settings → Database → Connection String (Pooler)
   - **Project URL & Keys**: Project Settings → API

### 2. Run Setup Script

```powershell
# Run the automated setup script
.\setup-supabase.ps1
```

Follow the prompts to enter your Supabase credentials, or skip and configure manually.

### 3. Configure Environment Files

#### Backend (`backend/.env`)
```env
DATABASE_URL=postgresql://postgres.xxxxx:[PASSWORD]@aws-0-region.pooler.supabase.com:6543/postgres
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-super-secret-key-min-32-characters-long
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
```

#### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### 4. Install Dependencies

```powershell
# Backend
cd backend
python -m poetry install --no-root

# Frontend
cd ../frontend
npm install
```

### 5. Run Database Migrations

```powershell
cd backend
python -m poetry run alembic upgrade head
```

### 6. Start the Application

Open two terminal windows:

**Terminal 1 - Backend:**
```powershell
cd backend
python -m poetry run uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

### 7. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/api/v1/docs

## ✅ Verify Everything Works

1. Open http://localhost:3000
2. Click "Get Started" or "Sign In"
3. Register a new account
4. Try the AI Council query interface

## 🔧 Optional: Redis Setup

### Option A: Docker (Easiest)
```powershell
docker run -d -p 6379:6379 redis:alpine
```

### Option B: Upstash (Cloud, Free)
1. Go to [upstash.com](https://upstash.com)
2. Create a Redis database
3. Copy the connection string to `backend/.env`

## 🤖 Add AI API Keys

To use the AI Council features, add your API keys to `backend/.env`:

```env
GROQ_API_KEY=your-groq-api-key
TOGETHER_API_KEY=your-together-api-key
OPENROUTER_API_KEY=your-openrouter-api-key
HUGGINGFACE_API_KEY=your-huggingface-api-key
```

Get free API keys from:
- **Groq**: https://console.groq.com
- **Together AI**: https://api.together.xyz
- **OpenRouter**: https://openrouter.ai
- **Hugging Face**: https://huggingface.co/settings/tokens

## 📚 Detailed Documentation

- **Supabase Setup**: See `SUPABASE_SETUP_GUIDE.md`
- **Backend README**: See `backend/README.md`
- **Frontend README**: See `frontend/README.md`
- **Deployment**: See `PRODUCTION_DEPLOYMENT_PLAN.md`

## 🐛 Troubleshooting

### Backend won't start
- Check if DATABASE_URL is correct
- Verify Supabase project is running
- Check if port 8000 is available

### Frontend errors
- Make sure backend is running first
- Check if .env.local exists
- Verify API URL is correct

### Database connection issues
- Use the **Pooler** connection string, not direct
- Verify your password is correct
- Check Supabase dashboard for connection issues

### Redis connection issues
- Redis is optional for basic functionality
- Use Docker or Upstash for easy setup
- Or comment out Redis-dependent features

## 🎉 You're All Set!

Your AI Council application is now running with:
- ✅ Supabase PostgreSQL database
- ✅ User authentication
- ✅ Real-time WebSocket support
- ✅ AI orchestration backend
- ✅ Modern React frontend

Start building amazing AI-powered applications!

## 📞 Need Help?

- Check the detailed guides in the docs folder
- Review the SUPABASE_SETUP_GUIDE.md
- Check backend/frontend README files
- Open an issue on GitHub
