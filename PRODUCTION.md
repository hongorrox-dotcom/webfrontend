# Production Deployment Notes

## Current Status

✅ **Backend API Live:** https://webfrontend-1aao.onrender.com

## Environment Setup on Render

### Step 1: Add Environment Variables

In Render dashboard settings, add these environment variables:

```
OPENAI_API_KEY=your_actual_key_here
OPENAI_MODEL=gpt-4o-mini
MODEL_PATH=./models/dornodjinkencopy2.mdl
DEMO_MODE_AUTO=0
ALLOWED_ORIGINS=https://your-frontend-domain.onrender.com
ALLOWED_ORIGIN_REGEX=^https://.*\.onrender\.com$
```

### Step 2: Update CORS for Frontend

When you deploy frontend (on Vercel, Netlify, etc.), update:

```
ALLOWED_ORIGINS=https://your-frontend-domain.onrender.com,https://your-frontend-domain.vercel.app
ALLOWED_ORIGIN_REGEX=^https://(your-frontend-domain\.(onrender\.com|vercel\.app))$
```

### Step 3: Update Frontend API URL

In frontend `.env` file, set API URL to:
```
VITE_API_BASE=https://webfrontend-1aao.onrender.com
```

Or pass as environment variable during build:
```bash
VITE_API_BASE=https://webfrontend-1aao.onrender.com npm run build
```

## API Endpoints

- **Base URL:** https://webfrontend-1aao.onrender.com
- **Docs (Swagger):** https://webfrontend-1aao.onrender.com/docs
- **OpenAPI Schema:** https://webfrontend-1aao.onrender.com/openapi.json

## Python Version

Currently running: **Python 3.13** (compatible with requirements)

## Monitoring

Check logs in Render dashboard:
- View real-time logs
- Monitor server status
- Check resource usage

## Troubleshooting

### Cold Start
First request may take 30 seconds (Render free tier behavior)

### CORS Errors
If frontend can't reach API:
1. Check ALLOWED_ORIGINS in Render environment variables
2. Ensure ALLOWED_ORIGIN_REGEX matches frontend domain
3. Verify frontend requests include credentials if needed

### Port Issues
Render automatically assigns PORT via $PORT environment variable. Uvicorn listens on 0.0.0.0:$PORT (currently port 10000)

---

**Deployed:** 2026-02-06
**Service:** Render.com Free Tier
