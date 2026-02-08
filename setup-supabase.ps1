# AI Council - Supabase Setup Script
# This script helps you configure Supabase for your AI Council application

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "AI Council - Supabase Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env files exist
$backendEnvExists = Test-Path "backend/.env"
$frontendEnvExists = Test-Path "frontend/.env.local"

if (-not $backendEnvExists) {
    Write-Host "Creating backend/.env from template..." -ForegroundColor Yellow
    Copy-Item "backend/.env.example" "backend/.env"
}

if (-not $frontendEnvExists) {
    Write-Host "Creating frontend/.env.local from template..." -ForegroundColor Yellow
    Copy-Item "frontend/.env.local.example" "frontend/.env.local"
}

Write-Host ""
Write-Host "Setup Instructions:" -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green
Write-Host ""
Write-Host "1. Create a Supabase account at https://supabase.com" -ForegroundColor White
Write-Host "2. Create a new project and wait for it to provision" -ForegroundColor White
Write-Host "3. Get your connection details:" -ForegroundColor White
Write-Host "   - Go to Project Settings → Database" -ForegroundColor Gray
Write-Host "   - Copy the Connection String (Pooler)" -ForegroundColor Gray
Write-Host "   - Go to Project Settings → API" -ForegroundColor Gray
Write-Host "   - Copy the Project URL and anon key" -ForegroundColor Gray
Write-Host ""

# Prompt for Supabase details
Write-Host "Enter your Supabase details (or press Enter to skip and configure manually):" -ForegroundColor Cyan
Write-Host ""

$supabaseUrl = Read-Host "Supabase Project URL (e.g., https://xxxxx.supabase.co)"
$supabaseAnonKey = Read-Host "Supabase Anon Key"
$databaseUrl = Read-Host "Database Connection String (Pooler)"

if ($supabaseUrl -and $supabaseAnonKey) {
    Write-Host ""
    Write-Host "Updating frontend/.env.local..." -ForegroundColor Yellow
    
    $frontendEnv = Get-Content "frontend/.env.local" -Raw
    $frontendEnv = $frontendEnv -replace "NEXT_PUBLIC_SUPABASE_URL=.*", "NEXT_PUBLIC_SUPABASE_URL=$supabaseUrl"
    $frontendEnv = $frontendEnv -replace "NEXT_PUBLIC_SUPABASE_ANON_KEY=.*", "NEXT_PUBLIC_SUPABASE_ANON_KEY=$supabaseAnonKey"
    $frontendEnv | Set-Content "frontend/.env.local"
    
    Write-Host "✓ Frontend configuration updated!" -ForegroundColor Green
}

if ($databaseUrl) {
    Write-Host "Updating backend/.env..." -ForegroundColor Yellow
    
    $backendEnv = Get-Content "backend/.env" -Raw
    $backendEnv = $backendEnv -replace "DATABASE_URL=.*", "DATABASE_URL=$databaseUrl"
    $backendEnv | Set-Content "backend/.env"
    
    Write-Host "✓ Backend configuration updated!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "==========" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Review and update backend/.env with your settings" -ForegroundColor White
Write-Host "2. Review and update frontend/.env.local with your settings" -ForegroundColor White
Write-Host "3. Run database migrations:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   python -m poetry run alembic upgrade head" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Restart your servers:" -ForegroundColor White
Write-Host "   Backend: cd backend && python -m poetry run uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host "   Frontend: cd frontend && npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "For detailed instructions, see SUPABASE_SETUP_GUIDE.md" -ForegroundColor Yellow
Write-Host ""
Write-Host "Setup script completed!" -ForegroundColor Green
