# Supabase Setup Guide for AI Council

This guide will help you set up Supabase for your AI Council application, providing PostgreSQL database, authentication, and real-time features.

## Step 1: Create a Supabase Account

1. Go to [https://supabase.com](https://supabase.com)
2. Click "Start your project"
3. Sign up with GitHub, Google, or email
4. Verify your email if required

## Step 2: Create a New Project

1. Click "New Project" in your Supabase dashboard
2. Fill in the project details:
   - **Name**: `ai-council` (or your preferred name)
   - **Database Password**: Create a strong password (save this!)
   - **Region**: Choose the closest region to you
   - **Pricing Plan**: Free tier is fine for development
3. Click "Create new project"
4. Wait 2-3 minutes for the project to be provisioned

## Step 3: Get Your Connection Details

Once your project is ready:

1. Go to **Project Settings** (gear icon in sidebar)
2. Click on **Database** in the left menu
3. Copy the following information:

### Connection String (Pooler)
- Look for "Connection string" section
- Select **URI** tab
- Copy the connection string that looks like:
  ```
  postgresql://postgres.xxxxx:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
  ```
- Replace `[YOUR-PASSWORD]` with your actual database password

### API Keys
1. Go to **Project Settings** → **API**
2. Copy these values:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: `eyJhbGc...` (long string)
   - **service_role key**: `eyJhbGc...` (long string - keep this secret!)

## Step 4: Configure Backend Environment

1. Open `backend/.env` file
2. Update the following values:

```env
# Supabase Database Configuration
DATABASE_URL=postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# Keep Redis as is (we'll use Upstash or local Redis)
REDIS_URL=redis://localhost:6379/0

# JWT Configuration (use a strong secret key)
SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7

# Cloud AI Provider API Keys (add your keys when ready)
GROQ_API_KEY=your-groq-api-key
TOGETHER_API_KEY=your-together-api-key
OPENROUTER_API_KEY=your-openrouter-api-key
HUGGINGFACE_API_KEY=your-huggingface-api-key

# Application Configuration
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
API_V1_PREFIX=/api/v1

# Rate Limiting
RATE_LIMIT_AUTHENTICATED=100
RATE_LIMIT_DEMO=3
RATE_LIMIT_ADMIN=1000

# WebSocket Configuration
WEBSOCKET_HEARTBEAT_INTERVAL=30
WEBSOCKET_IDLE_TIMEOUT=300
WEBSOCKET_MAX_CONNECTIONS_PER_USER=5

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

## Step 5: Configure Frontend Environment

1. Create `frontend/.env.local` file (copy from `.env.local.example`)
2. Add your Supabase credentials:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...your-anon-key...

# Environment
NEXT_PUBLIC_ENVIRONMENT=development
```

## Step 6: Run Database Migrations

Once you've configured the database URL:

```powershell
cd backend
python -m poetry run alembic upgrade head
```

This will create all the necessary tables in your Supabase database.

## Step 7: Set Up Redis (Optional but Recommended)

### Option A: Use Upstash (Free, Cloud-based)
1. Go to [https://upstash.com](https://upstash.com)
2. Sign up and create a new Redis database
3. Copy the connection string
4. Update `REDIS_URL` in `backend/.env`

### Option B: Use Local Redis (Development)
1. Install Redis locally or use Docker:
   ```powershell
   docker run -d -p 6379:6379 redis:alpine
   ```
2. Keep `REDIS_URL=redis://localhost:6379/0` in your `.env`

## Step 8: Verify Setup

1. Restart your backend server
2. Check the logs for successful database connection
3. Visit http://localhost:8000/api/v1/docs to see the API documentation
4. Try registering a new user through the frontend

## Step 9: Enable Supabase Auth (Optional)

If you want to use Supabase's built-in authentication instead of custom JWT:

1. In Supabase Dashboard, go to **Authentication** → **Providers**
2. Enable **Email** provider
3. Configure email templates if needed
4. Update frontend to use Supabase Auth SDK

## Troubleshooting

### Database Connection Issues
- Verify your password is correct
- Check if your IP is allowed (Supabase allows all IPs by default)
- Ensure you're using the **Pooler** connection string, not the direct connection

### Migration Errors
- Make sure DATABASE_URL is correctly set
- Check if tables already exist in Supabase dashboard
- Try running: `python -m poetry run alembic downgrade base` then upgrade again

### Redis Connection Issues
- If using local Redis, make sure it's running
- For Upstash, verify the connection string format
- Redis is optional for basic functionality

## Next Steps

1. Add your AI API keys to `backend/.env`
2. Test user registration and login
3. Try the AI Council query interface
4. Deploy to production when ready

## Production Deployment

For production:
1. Use Supabase's production database
2. Set `ENVIRONMENT=production` and `DEBUG=false`
3. Use strong SECRET_KEY (generate with: `openssl rand -hex 32`)
4. Enable SSL for database connections
5. Set up proper CORS origins
6. Use environment variables in your hosting platform (Vercel, Railway, etc.)

## Support

- Supabase Docs: https://supabase.com/docs
- AI Council Issues: [Your GitHub repo]
- Supabase Discord: https://discord.supabase.com
