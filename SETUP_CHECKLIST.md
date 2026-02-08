# AI Council Setup Checklist

Use this checklist to track your setup progress.

## ☐ Phase 1: Supabase Account Setup

- [ ] Created Supabase account at https://supabase.com
- [ ] Created new project (name: `ai-council` or similar)
- [ ] Saved database password securely
- [ ] Project finished provisioning (2-3 minutes)

## ☐ Phase 2: Get Supabase Credentials

- [ ] Copied Database Connection String (Pooler)
  - Location: Project Settings → Database → Connection String
  - Format: `postgresql://postgres.xxxxx:password@...`
- [ ] Copied Project URL
  - Location: Project Settings → API
  - Format: `https://xxxxx.supabase.co`
- [ ] Copied Anon Key
  - Location: Project Settings → API
  - Starts with: `eyJhbGc...`

## ☐ Phase 3: Configure Backend

- [ ] Created/Updated `backend/.env` file
- [ ] Set `DATABASE_URL` with Supabase connection string
- [ ] Set `SECRET_KEY` (minimum 32 characters)
- [ ] Set `CORS_ORIGINS` to `["http://localhost:3000","http://localhost:3001"]`
- [ ] Configured Redis URL (or left as localhost for now)

## ☐ Phase 4: Configure Frontend

- [ ] Created/Updated `frontend/.env.local` file
- [ ] Set `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
- [ ] Set `NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws`
- [ ] Set `NEXT_PUBLIC_SUPABASE_URL` with your project URL
- [ ] Set `NEXT_PUBLIC_SUPABASE_ANON_KEY` with your anon key

## ☐ Phase 5: Install Dependencies

- [ ] Installed Poetry: `pip install poetry`
- [ ] Installed backend dependencies: `cd backend && python -m poetry install --no-root`
- [ ] Installed frontend dependencies: `cd frontend && npm install`

## ☐ Phase 6: Database Setup

- [ ] Ran database migrations: `cd backend && python -m poetry run alembic upgrade head`
- [ ] Verified tables created in Supabase dashboard (Table Editor)
- [ ] No migration errors in console

## ☐ Phase 7: Start Services

- [ ] Started backend server: `cd backend && python -m poetry run uvicorn app.main:app --reload`
- [ ] Backend running on http://localhost:8000
- [ ] Started frontend server: `cd frontend && npm run dev`
- [ ] Frontend running on http://localhost:3000

## ☐ Phase 8: Verify Setup

- [ ] Opened http://localhost:3000 in browser
- [ ] No console errors in browser
- [ ] Clicked "Get Started" button
- [ ] Registration form loads correctly
- [ ] Created test account successfully
- [ ] Logged in successfully
- [ ] Dashboard loads correctly

## ☐ Phase 9: Optional - Redis Setup

Choose one option:

### Option A: Docker Redis
- [ ] Installed Docker Desktop
- [ ] Ran: `docker run -d -p 6379:6379 redis:alpine`
- [ ] Verified Redis running: `docker ps`

### Option B: Upstash Redis
- [ ] Created Upstash account at https://upstash.com
- [ ] Created new Redis database
- [ ] Copied connection string
- [ ] Updated `REDIS_URL` in `backend/.env`

### Option C: Skip for Now
- [ ] Decided to skip Redis (some features may be limited)

## ☐ Phase 10: Optional - AI API Keys

- [ ] Created Groq account and got API key
- [ ] Created Together AI account and got API key
- [ ] Created OpenRouter account and got API key
- [ ] Created Hugging Face account and got token
- [ ] Added all keys to `backend/.env`
- [ ] Restarted backend server

## ☐ Phase 11: Test AI Features

- [ ] Logged into application
- [ ] Navigated to AI Council query interface
- [ ] Submitted a test query
- [ ] Received AI response
- [ ] Checked query history

## 🎉 Setup Complete!

If all checkboxes are checked, your AI Council application is fully configured and running!

## 📝 Notes

Use this space to write down any issues or customizations:

```
[Your notes here]
```

## 🆘 Having Issues?

If you're stuck on any step:

1. Check the detailed guide: `SUPABASE_SETUP_GUIDE.md`
2. Review the quick start: `QUICK_START.md`
3. Check backend logs for errors
4. Check browser console for frontend errors
5. Verify all environment variables are set correctly

## Next Steps

- [ ] Read `PRODUCTION_DEPLOYMENT_PLAN.md` for deployment
- [ ] Explore the admin interface
- [ ] Customize the application for your needs
- [ ] Add more AI providers
- [ ] Deploy to production
