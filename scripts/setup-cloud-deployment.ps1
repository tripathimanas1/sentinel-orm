# Sentinel ORM - Cloud Deployment Setup Script
# This script helps you prepare for cloud deployment

$ErrorActionPreference = "Stop"

Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Sentinel ORM - Cloud Deployment Setup             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-Command($command) {
    try {
        if (Get-Command $command -ErrorAction Stop) {
            return $true
        }
    } catch {
        return $false
    }
}

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow
Write-Host ""

$allGood = $true

# Check Git
if (Test-Command "git") {
    $gitVersion = git --version
    Write-Host "✅ Git installed: $gitVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Git not found. Install from: https://git-scm.com/" -ForegroundColor Red
    $allGood = $false
}

# Check if in git repo
if (Test-Path ".git") {
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
} else {
    Write-Host "⚠️  Not a git repository. Will initialize..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
}

# Check Python
if (Test-Command "python") {
    $pythonVersion = python --version
    Write-Host "✅ Python installed: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python not found" -ForegroundColor Red
    $allGood = $false
}

# Check Poetry
if (Test-Command "poetry") {
    $poetryVersion = poetry --version
    Write-Host "✅ Poetry installed: $poetryVersion" -ForegroundColor Green
} else {
    Write-Host "⚠️  Poetry not found (required for Railway/Render)" -ForegroundColor Yellow
}

Write-Host ""

if (-not $allGood) {
    Write-Host "❌ Please install missing dependencies before continuing." -ForegroundColor Red
    exit 1
}

# Choose deployment platform
Write-Host "🎯 Choose your deployment platform:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Railway (Easiest, recommended for beginners)" -ForegroundColor Green
Write-Host "   - Setup time: 10-15 minutes"
Write-Host "   - Cost: ~`$15-30/month"
Write-Host "   - Best for: MVPs, testing, small apps"
Write-Host ""
Write-Host "2. Render (Good for production)" -ForegroundColor Yellow
Write-Host "   - Setup time: 15-20 minutes"
Write-Host "   - Cost: ~`$20-50/month"
Write-Host "   - Best for: Production apps, medium traffic"
Write-Host ""
Write-Host "3. AWS/Azure (Enterprise)" -ForegroundColor Magenta
Write-Host "   - Setup time: 2-5 days"
Write-Host "   - Cost: ~`$50-150/month"
Write-Host "   - Best for: Enterprise, high traffic"
Write-Host ""
Write-Host "4. Show me the comparison guide" -ForegroundColor Cyan
Write-Host ""

$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🚂 Railway Deployment Selected!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📖 Opening Railway deployment guide..." -ForegroundColor Yellow
        
        if (Test-Path ".agent\workflows\deploy-railway.md") {
            Start-Process ".agent\workflows\deploy-railway.md"
        }
        
        Write-Host ""
        Write-Host "✅ Next Steps:" -ForegroundColor Cyan
        Write-Host "1. Sign up at https://railway.app" -ForegroundColor White
        Write-Host "2. Push your code to GitHub (see instructions below)" -ForegroundColor White
        Write-Host "3. Follow the Railway deployment guide" -ForegroundColor White
        Write-Host "4. Sign up for ClickHouse Cloud: https://clickhouse.cloud" -ForegroundColor White
        Write-Host "5. Sign up for Upstash Kafka: https://upstash.com" -ForegroundColor White
    }
    "2" {
        Write-Host ""
        Write-Host "🎨 Render Deployment Selected!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📖 Opening Render deployment guide..." -ForegroundColor Yellow
        
        if (Test-Path ".agent\workflows\deploy-render.md") {
            Start-Process ".agent\workflows\deploy-render.md"
        }
        
        Write-Host ""
        Write-Host "✅ Next Steps:" -ForegroundColor Cyan
        Write-Host "1. Sign up at https://render.com" -ForegroundColor White
        Write-Host "2. Push your code to GitHub (see instructions below)" -ForegroundColor White
        Write-Host "3. Follow the Render deployment guide" -ForegroundColor White
        Write-Host "4. Sign up for ClickHouse Cloud: https://clickhouse.cloud" -ForegroundColor White
        Write-Host "5. Sign up for Upstash Kafka: https://upstash.com" -ForegroundColor White
    }
    "3" {
        Write-Host ""
        Write-Host "☁️ AWS/Azure Deployment Selected!" -ForegroundColor Green
        Write-Host ""
        Write-Host "⚠️  AWS/Azure deployment requires significant DevOps knowledge." -ForegroundColor Yellow
        Write-Host "Consider using Railway or Render for easier deployment." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "For AWS deployment, you'll need:" -ForegroundColor White
        Write-Host "- AWS account" -ForegroundColor White
        Write-Host "- Terraform or CloudFormation knowledge" -ForegroundColor White
        Write-Host "- DevOps experience" -ForegroundColor White
        Write-Host "- 2-5 days for setup" -ForegroundColor White
    }
    "4" {
        Write-Host ""
        Write-Host "📊 Opening comparison guide..." -ForegroundColor Yellow
        
        if (Test-Path "CLOUD_DEPLOYMENT_GUIDE.md") {
            Start-Process "CLOUD_DEPLOYMENT_GUIDE.md"
        }
    }
    default {
        Write-Host "Invalid choice. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "──────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# Git setup assistance
Write-Host "📦 Git Repository Setup" -ForegroundColor Cyan
Write-Host ""

# Check if remote exists
$hasRemote = git remote -v 2>$null
if ($hasRemote) {
    Write-Host "✅ Git remote already configured:" -ForegroundColor Green
    git remote -v
} else {
    Write-Host "⚠️  No Git remote configured" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To push to GitHub:" -ForegroundColor White
    Write-Host "1. Create a new repository on GitHub: https://github.com/new" -ForegroundColor White
    Write-Host "2. Run these commands:" -ForegroundColor White
    Write-Host ""
    Write-Host "   git remote add origin https://github.com/YOUR_USERNAME/sentinel-orm.git" -ForegroundColor Gray
    Write-Host "   git add ." -ForegroundColor Gray
    Write-Host "   git commit -m 'Initial commit for deployment'" -ForegroundColor Gray
    Write-Host "   git branch -M main" -ForegroundColor Gray
    Write-Host "   git push -u origin main" -ForegroundColor Gray
    Write-Host ""
}

# Check for uncommitted changes
$status = git status --porcelain 2>$null
if ($status) {
    Write-Host "⚠️  You have uncommitted changes:" -ForegroundColor Yellow
    Write-Host ""
    git status --short
    Write-Host ""
    Write-Host "Would you like to commit these changes now? (y/n): " -ForegroundColor Cyan -NoNewline
    $commit = Read-Host
    
    if ($commit -eq "y" -or $commit -eq "Y") {
        $message = Read-Host "Enter commit message (or press Enter for default)"
        if (-not $message) {
            $message = "Prepare for cloud deployment"
        }
        
        git add .
        git commit -m $message
        Write-Host "✅ Changes committed!" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "──────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# Environment variables check
Write-Host "🔐 Environment Variables Check" -ForegroundColor Cyan
Write-Host ""

if (Test-Path ".env.production") {
    Write-Host "✅ .env.production file exists" -ForegroundColor Green
    
    $content = Get-Content ".env.production" -Raw
    
    $warnings = @()
    
    if ($content -match "CHANGE_ME") {
        $warnings += "❌ Some values still have CHANGE_ME placeholders"
    }
    
    if ($content -match "SECRET_KEY=.*CHANGE_ME") {
        $warnings += "❌ SECRET_KEY needs to be changed"
    }
    
    if ($content -match "POSTGRES_PASSWORD=.*CHANGE_ME") {
        $warnings += "❌ POSTGRES_PASSWORD needs to be changed"
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host ""
        Write-Host "⚠️  Warnings:" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "   $warning" -ForegroundColor Yellow
        }
        Write-Host ""
        Write-Host "   Edit .env.production before deploying" -ForegroundColor White
    } else {
        Write-Host "✅ Environment variables look good!" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  .env.production not found" -ForegroundColor Yellow
    Write-Host "   Creating from template..." -ForegroundColor White
    
    if (Test-Path ".env.production.example") {
        Copy-Item ".env.production.example" ".env.production"
        Write-Host "✅ Created .env.production" -ForegroundColor Green
        Write-Host "   ⚠️  IMPORTANT: Edit .env.production and set your secrets!" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "──────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

Write-Host "✨ Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📚 Helpful Files:" -ForegroundColor Cyan
Write-Host "   - CLOUD_DEPLOYMENT_GUIDE.md - Platform comparison" -ForegroundColor White
Write-Host "   - .agent/workflows/deploy-railway.md - Railway guide" -ForegroundColor White
Write-Host "   - .agent/workflows/deploy-render.md - Render guide" -ForegroundColor White
Write-Host "   - DEPLOYMENT_CHECKLIST.md - Deployment checklist" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Quick Links:" -ForegroundColor Cyan
Write-Host "   - Railway: https://railway.app" -ForegroundColor White
Write-Host "   - Render: https://render.com" -ForegroundColor White
Write-Host "   - ClickHouse Cloud: https://clickhouse.cloud" -ForegroundColor White
Write-Host "   - Upstash Kafka: https://upstash.com" -ForegroundColor White
Write-Host ""
Write-Host "Need help? Check the deployment guides or ask for assistance!" -ForegroundColor Yellow
Write-Host ""
