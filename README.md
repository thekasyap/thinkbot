# ThinkBot

ThinkBot is a tiny adaptive quiz demo that showcases how Gemini can power
personalized learning on resource‑constrained platforms like the free Vercel
hobby plan.  It serves a minimal HTML interface, tracks student accuracy in
small JSON files, and calls Gemini's `gemini-2.5-flash` model using the public
REST API with thinking disabled to conserve quota.

## Features
- Lightweight FastAPI backend with a static front‑end served at the root path
- Question bank with easy/medium/hard levels selected by learner accuracy
- Student progress stored locally as `data/student_<name>.json`
- Gemini feedback for each answer using a single low‑cost API request

## Setup
1. Install Python 3.9+ dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Export your Gemini API key (free tier works):
   ```bash
   export GEMINI_API_KEY="<your-key>"
   ```
3. Run the development server:
   ```bash
   uvicorn api:app --reload
   ```
   Then open [http://localhost:8000/](http://localhost:8000/) to try the quiz.

For deployment on Vercel, the included `vercel.json` forwards all requests to
the `api` directory so the FastAPI app serves the root path.  Set the
`GEMINI_API_KEY` environment variable in the Vercel dashboard and deploy.

## Testing
Run the automated tests to verify basic behaviour:
```bash
python -m pytest -q
```

## License
Released under the MIT License.  See [LICENSE](LICENSE).
