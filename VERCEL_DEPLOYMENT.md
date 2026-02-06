# Vercel Frontend Deployment Guide

## Quick Setup

### Step 1: Import Project

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New..." → "Project"
3. Select "Import Git Repository"
4. Choose: `https://github.com/hongorrox-dotcom/webfrontend.git`

### Step 2: Configure Project

**Root Directory:** `frontend`

**Framework Preset:** Vite

**Build & Output Settings:**
- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

### Step 3: Environment Variables

In Vercel Project Settings → Environment Variables, add:

```
VITE_API_BASE=https://webfrontend-1aao.onrender.com
```

**For development:**
```
VITE_API_BASE=http://localhost:8000
```

### Step 4: Deploy

Click "Deploy" - Vercel will automatically deploy on every push to `main` branch.

## After Deployment

### Frontend URL
Your frontend will be available at:
```
https://webfrontend.vercel.app (or custom domain)
```

### Update Backend CORS

When frontend is deployed, update backend CORS on Render:

```
ALLOWED_ORIGINS=https://webfrontend.vercel.app
ALLOWED_ORIGIN_REGEX=^https://webfrontend.*\.vercel\.app$
```

## Automatic Deployments

- **Production:** Every push to `main` → auto-deploys
- **Preview:** Every pull request → preview deployment
- **Draft:** Manual deployments from `vercel.json`

## Troubleshooting

### CORS Errors

If frontend can't reach backend:

1. Check `VITE_API_BASE` environment variable
2. Verify backend `ALLOWED_ORIGINS` includes frontend URL
3. Check browser console for exact error

### Build Fails

1. Check Vercel build logs
2. Ensure `npm run build` works locally:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

### Blank Page

1. Check `VITE_API_BASE` is correctly set
2. Check API requests in Network tab
3. Verify backend is accessible

## File Structure Reference

```
webfrontend/
├── frontend/          ← Vercel Root Directory
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   └── dist/         ← Output Directory (auto-created on build)
├── backend/          ← Deployed on Render.com
├── vercel.json       ← Vercel config
└── README.md
```

---

**Status:** ✅ Ready for Vercel deployment
**Backend API:** https://webfrontend-1aao.onrender.com
**Test:** `curl https://webfrontend-1aao.onrender.com/docs`
