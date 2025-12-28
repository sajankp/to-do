# Troubleshooting Guide

This guide covers common issues encountered during development and deployment of FastTodo.

## Frontend Issues

### 1. "Voice Assistant fails to connect" or "400 Bad Request"
**Symptom:**
Clicking the microphone button does nothing, or the console shows a 400 error from Google GenAI.

**Possible Causes:**
- Missing `GEMINI_API_KEY` in environment variables.
- API Key is invalid or expired.
- Browser microphone permission denied.

**Solution:**
1. Check `.env.local` exists in `to-do-frontend/` and contains `GEMINI_API_KEY=AIzaSy...`.
2. Verify the key works in [Google AI Studio](https://aistudio.google.com/).
3. Reset browser permissions for the localhost site.

### 2. "Network Error" or "CORS Error" on Login
**Symptom:**
Frontend shows "Failed to fetch" or console shows "Access to fetch has been blocked by CORS policy".

**Possible Causes:**
- Backend is not running.
- Backend is running on a different port than expected (default: 8000).
- Frontend requests are not matching the backend's allowed origins.

**Solution:**
1. Ensure backend is running: `curl http://localhost:8000/docs` should work.
2. Check `app/main.py`: Currently allows all origins (`allow_origins=["*"]`) for development.
3. If using a custom domain/port, update `ALLOWED_ORIGINS` in `app/config.py`.

### 3. "Module not found" during Build
**Symptom:**
`npm run build` fails with missing dependency errors.

**Possible Causes:**
- `npm install` was not run after a fresh clone or pull.
- `node_modules` is corrupted.

**Solution:**
```bash
rm -rf node_modules package-lock.json
npm install
```

---

## Backend Issues

### 1. "ModuleNotFoundError: No module named 'app'"
**Symptom:**
Running python scripts directly fails.

**Cause:**
Python path incorrectly set for the project structure.

**Solution:**
Always run commands from the project root using module syntax:
```bash
# Correct
python -m app.main
pytest app/tests
# Incorrect
python app/main.py
```

### 2. MongoDB Connection Failed
**Symptom:**
API starts but requests fail with connection timeout.

**Solution:**
1. Check `MONGO_URI` in `.env`.
2. Ensure network allows outbound traffic to MongoDB Atlas (check firewall/VPN).
3. Whitelist your IP address in MongoDB Atlas Network Access.
