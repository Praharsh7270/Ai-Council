# AI Council Troubleshooting Guide

Common issues and their solutions.

## Database Connection Issues

### Error: "could not connect to server"
**Cause**: Database URL is incorrect or Supabase project is down

**Solutions**:
1. Verify your DATABASE_URL in `backend/.env`
2. Make sure you're using the **Pooler** connection string, not direct
3. Check if your Supabase project is running in the dashboard
4. Verify your password is correct (no special characters causing issues)
5. Try regenerating the database password in Supabase settings

### Error: "password authentication failed"
**Cause**: Wrong password in connection string

**Solutions**:
1. Go to Supabase → Project Settings → Database
2. Reset your database password
3. Update the password in your DATABASE_URL
4. Make sure there are no extra spaces or special characters

### Error: "SSL connection required"
**Cause**: Missing SSL parameter in connection string

**Solution**:
Add `?sslmode=require` to the end of your DATABASE_URL:
```
postgresql://postgres.xxxxx:password@host:6543/postgres?sslmode=require
```

## Migration Issues

### Error: "alembic: command not found"
**Cause**: Alembic not installed or not in PATH

**Solutions**:
```powershell
cd backend
python -m poetry install --no-root
python -m poetry run alembic upgrade head
```

### Error: "Target database is not up to date"
**Cause**: Database schema mismatch

**Solutions**:
```powershell
# Check current version
python -m poetry run alembic current

# Upgrade to latest
python -m poetry run alembic upgrade head

# If issues persist, reset (WARNING: deletes data)
python -m poetry run alembic downgrade base
python -m poetry run alembic upgrade head
```

### Error: "Table already exists"
**Cause**: Tables were created manually or by previous migration

**Solutions**:
1. Check Supabase Table Editor to see existing tables
2. Either drop all tables and re-run migrations
3. Or stamp the current version: `python -m poetry run alembic stamp head`

## Backend Server Issues

### Error: "Address already in use" (Port 8000)
**Cause**: Another process is using port 8000

**Solutions**:
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use a different port
python -m poetry run uvicorn app.main:app --reload --port 8001
```

### Error: "ModuleNotFoundError: No module named 'app'"
**Cause**: Running from wrong directory or dependencies not installed

**Solutions**:
```powershell
# Make sure you're in the backend directory
cd backend

# Reinstall dependencies
python -m poetry install --no-root

# Run from backend directory
python -m poetry run uvicorn app.main:app --reload
```

### Error: "No module named 'structlog'"
**Cause**: Missing dependency in Poetry environment

**Solution**:
```powershell
cd backend
python -m poetry run pip install structlog tenacity
```

## Frontend Issues

### Error: "useState only works in Client Components"
**Cause**: Missing "use client" directive

**Solution**: Already fixed! If you see this, make sure you have the latest code.

### Error: "Failed to fetch" or "Network Error"
**Cause**: Backend not running or wrong API URL

**Solutions**:
1. Make sure backend is running on http://localhost:8000
2. Check `frontend/.env.local` has correct `NEXT_PUBLIC_API_URL`
3. Verify CORS is configured in backend `.env`
4. Check browser console for actual error

### Error: "Hydration failed"
**Cause**: Server/client mismatch in React

**Solutions**:
1. Clear browser cache and reload
2. Delete `.next` folder and restart: `rm -rf .next && npm run dev`
3. Check for console errors for specific component

### Error: "Module not found: Can't resolve '@/...'"
**Cause**: TypeScript path alias not configured

**Solution**: Check `tsconfig.json` has:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

## Redis Issues

### Error: "Redis connection refused"
**Cause**: Redis not running

**Solutions**:

**Option 1 - Skip Redis (temporary)**:
Comment out Redis-dependent code or set `REDIS_URL=` (empty)

**Option 2 - Use Docker**:
```powershell
docker run -d -p 6379:6379 redis:alpine
```

**Option 3 - Use Upstash**:
1. Go to https://upstash.com
2. Create free Redis database
3. Copy connection string to `backend/.env`

## Authentication Issues

### Error: "Invalid credentials" on login
**Cause**: User doesn't exist or wrong password

**Solutions**:
1. Try registering a new account first
2. Check Supabase Table Editor → `users` table
3. Verify password hashing is working (check backend logs)

### Error: "Token expired"
**Cause**: JWT token expired

**Solution**: Log out and log back in. Tokens expire after 7 days by default.

### Error: "Unauthorized" on protected routes
**Cause**: Token not being sent or invalid

**Solutions**:
1. Check browser localStorage for `auth_token`
2. Verify token is being sent in Authorization header
3. Check backend logs for authentication errors

## AI API Issues

### Error: "API key not found"
**Cause**: AI provider API keys not configured

**Solution**:
Add your API keys to `backend/.env`:
```env
GROQ_API_KEY=your-key-here
TOGETHER_API_KEY=your-key-here
OPENROUTER_API_KEY=your-key-here
HUGGINGFACE_API_KEY=your-key-here
```

### Error: "Rate limit exceeded"
**Cause**: Too many requests to AI provider

**Solutions**:
1. Wait a few minutes and try again
2. Use a different AI provider
3. Upgrade your API plan
4. Implement request queuing

### Error: "Model not found"
**Cause**: Requested model doesn't exist or isn't available

**Solution**: Check the AI provider's documentation for available models

## Performance Issues

### Backend is slow
**Solutions**:
1. Check database connection pool settings
2. Verify Redis is running (caching helps)
3. Check Supabase dashboard for slow queries
4. Enable database indexes if needed

### Frontend is slow
**Solutions**:
1. Check Network tab in browser DevTools
2. Verify API responses are fast
3. Check for unnecessary re-renders
4. Enable production build: `npm run build && npm start`

## Environment Variable Issues

### Changes not taking effect
**Cause**: Server not restarted or wrong env file

**Solutions**:
1. Restart both backend and frontend servers
2. Verify you're editing the right file:
   - Backend: `backend/.env`
   - Frontend: `frontend/.env.local`
3. Check for typos in variable names
4. Make sure there are no spaces around `=`

### Variables showing as undefined
**Cause**: Missing `NEXT_PUBLIC_` prefix or not in .env.local

**Solution**: Frontend variables must:
1. Start with `NEXT_PUBLIC_`
2. Be in `frontend/.env.local`
3. Server must be restarted after changes

## Still Having Issues?

1. **Check the logs**:
   - Backend: Look at terminal where uvicorn is running
   - Frontend: Check browser console (F12)
   - Supabase: Check Logs in dashboard

2. **Verify configuration**:
   - Run through SETUP_CHECKLIST.md again
   - Double-check all environment variables
   - Verify Supabase project is active

3. **Clean restart**:
   ```powershell
   # Stop all servers
   # Delete cache
   cd backend && rm -rf __pycache__
   cd frontend && rm -rf .next
   
   # Restart
   cd backend && python -m poetry run uvicorn app.main:app --reload
   cd frontend && npm run dev
   ```

4. **Get help**:
   - Check GitHub issues
   - Review Supabase documentation
   - Ask in community forums

## Useful Commands

```powershell
# Check if ports are in use
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Check Python version
python --version

# Check Node version
node --version

# Check Poetry version
poetry --version

# View backend logs
cd backend && python -m poetry run uvicorn app.main:app --reload --log-level debug

# View database tables in Supabase
# Go to: Supabase Dashboard → Table Editor

# Test backend API
curl http://localhost:8000/api/v1/docs

# Test database connection
cd backend && python -m poetry run python -c "from app.core.database import engine; print(engine.url)"
```
