# Cellytics Deployment Guide

## Current Production Status

**Backend**: Deployed to [Render](https://cellytics-yvet.onrender.com)

- Status: ✅ Running
- Health Check: https://cellytics-yvet.onrender.com/health
- Keep-Alive: APScheduler pings every 5 minutes to prevent spin-down

**Frontend**: Ready for deployment (currently development on localhost:3001)

---

## Backend Deployment (Render)

### Current Configuration

- **Service**: https://cellytics-yvet.onrender.com
- **Runtime**: Python 3.11 with Uvicorn
- **Database**: PostgreSQL on Neon.tech (connected via SQLAlchemy)
- **Auto-Deploy**: Enabled for main branch

### How It Works

1. Push code to `main` branch on GitHub
2. Render automatically detects changes
3. Rebuilds and redeploys within 2-3 minutes

### Environment Variables (Set in Render Dashboard)

```
DATABASE_URL=<PostgreSQL connection string from Neon>
DATABASE_POOL_SIZE=5
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
```

### CORS Configuration

**Allowed Origins** (set in `main.py`):

```python
allow_origins=[
    "http://localhost:3000",
    "http://localhost:3001",
    "https://cellytics-backend.vercel.app",
]
allow_origin_regex=r"https://.*\.vercel\.app"
```

**To Add Production Frontend Domain**:

1. Edit [main.py](main.py) line 39-46
2. Add your frontend domain to `allow_origins`
3. Push to `main` branch
4. Render auto-redeploys

---

## Frontend Deployment

### Development Environment

```bash
cd cellytics_dashboards
npm install
npm run dev
```

Runs on `localhost:3001` with `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Production Build

```bash
cd cellytics_dashboards
npm run build
npm start
```

### Deploy to Vercel (Recommended)

1. **Connect Repository**

   ```bash
   npm install -g vercel
   vercel login
   vercel
   ```

2. **Set Environment Variable** in Vercel Dashboard:

   ```
   NEXT_PUBLIC_API_URL=https://cellytics-yvet.onrender.com
   ```

3. **Auto-Deploy Setup**
   - Vercel automatically deploys on push to `main`
   - No additional configuration needed

### Deploy to Other Platforms

1. Build: `npm run build`
2. Set `NEXT_PUBLIC_API_URL=https://cellytics-yvet.onrender.com`
3. Deploy the `.next` directory

---

## Testing Checklist

✅ **Local Development**

- [ ] Backend: `uvicorn main:app --reload` on port 8000
- [ ] Frontend: `npm run dev` on port 3001
- [ ] Login with test credentials: +237690200000 / 123456
- [ ] Dashboard loads with all stats
- [ ] CORS works (no errors in browser console)

✅ **Production**

- [ ] Backend: https://cellytics-yvet.onrender.com/health returns 200
- [ ] Frontend: Deployed and accessible
- [ ] Login works with production database
- [ ] Dashboard fetches data from Render backend
- [ ] No CORS errors

---

## Troubleshooting

### Backend Not Responding

1. Check Render dashboard: https://dashboard.render.com
2. View logs in Render for any errors
3. Verify database connection string in environment variables
4. Try manual rebuild: Render Dashboard → Manual Deploy

### CORS Errors

```
Access to fetch at 'https://cellytics-yvet.onrender.com/api/...'
from origin '...' has been blocked by CORS policy
```

**Solution**: Add origin to `allow_origins` in [main.py](main.py) and redeploy

### Slow Render Response

- First request might be slow (cold start)
- Subsequent requests are fast
- Keep-alive pinger runs every 5 minutes to maintain hot state

---

## Environment Files

### .env.local (Development)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### .env.production (Vercel)

Set in Vercel dashboard:

```
NEXT_PUBLIC_API_URL=https://cellytics-yvet.onrender.com
```

---

## Key Files

| File                                                               | Purpose                      |
| ------------------------------------------------------------------ | ---------------------------- |
| [main.py](main.py)                                                 | FastAPI app with CORS config |
| [database.py](database.py)                                         | SQLAlchemy database setup    |
| [routers/dashboards.py](routers/dashboards.py)                     | Dashboard endpoints          |
| [services/dashboard_service.py](services/dashboard_service.py)     | Dashboard business logic     |
| [cellytics_dashboards/.env.local](cellytics_dashboards/.env.local) | Frontend env config          |
| [requirements.txt](requirements.txt)                               | Python dependencies          |

---

## Git Workflow

```bash
# Make changes
git add .
git commit -m "Your message"

# Push to main (triggers auto-deployment)
git push origin main

# Check deployment
# Backend: https://cellytics-yvet.onrender.com/docs (after ~2 min)
# Frontend: Check your Vercel dashboard
```

---

## Contact & Support

For deployment issues:

1. Check Render logs: https://dashboard.render.com
2. Check Vercel logs (if deployed there)
3. Review this guide's troubleshooting section
4. Check GitHub Actions or CI/CD logs
