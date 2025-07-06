## Deploying on Railway

### Backend (FastAPI)
1. Go to https://railway.app and create a new project.
2. Select "Deploy from GitHub repo" and point to your backend folder.
3. Set the root directory to `backend`.
4. Add environment variables in Railway dashboard:
   - `GOOGLE_CREDENTIALS_JSON` (path or content of your service account JSON)
   - Any other required variables from `.env.example`
5. Railway will detect the `Procfile` and install dependencies from `requirements.txt`.
6. Deploy!

### Frontend (Streamlit)
1. Create a new Railway service, set root directory to `frontend`.
2. Add environment variables as needed (e.g., `BACKEND_URL`, `GEMINI_API_KEY`).
3. Railway will use the `Procfile` and install dependencies from `requirements.txt`.
4. Deploy!

**Note:**  
- Make sure your backend is deployed and accessible to the frontend (`BACKEND_URL`).
- For secrets, use Railway's environment variable UI.
