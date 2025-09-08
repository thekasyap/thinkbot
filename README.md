# ThinkBot

ThinkBot is a simple learning assistant that uses
[Google's Gemini API](https://ai.google.dev/) to adapt to each learner. It
augments the model with your own PDF material and tracks learner accuracy to
adjust the difficulty of explanations and quizzes. Student progress and quiz
results are stored in small JSON files, making it easy to inspect or reset the
state. A small FastAPI service powers a web-based quiz demo that can be deployed
to platforms like Vercel.

## Features

- **Retrieval‑Augmented Generation** – ingest PDFs and retrieve relevant
  snippets during chat.
- **Adaptive tutoring** – responses become simpler if the student struggles,
  and more advanced when they do well.
- **Random quizzing and scoring** – the bot occasionally asks short questions
  and keeps track of correct answers for each student.
- **Gemini powered** – uses the official `google-genai` SDK with the free
  `gemini-2.5-flash` model. Thinking is disabled to stay within the free tier
  limits.
- **Web API & demo UI** – serve adaptive quiz questions via FastAPI and a
  lightweight HTML/JS interface.

## Requirements

- Python 3.9+
- A Google Gemini API key. Set the ``GEMINI_API_KEY`` environment variable.
- Python dependencies listed in `requirements.txt`.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

If your model endpoint or key differs, edit the constants at the top of
`main.py`.

## Usage

1. **Ingest study material** (once per PDF):

   ```bash
   python main.py ingest path/to/lesson.pdf
   ```

2. **Start a tutoring session**:

   ```bash
   python main.py chat Alice
   ```

   Type your questions and the bot will answer using the retrieved context. It
   may occasionally present a quiz. Type `exit` to finish the session. At the
   end you will see your score. All progress is stored in `data/student_Alice.json`.

3. **Run the web demo**:

   ```bash
   export GEMINI_API_KEY="<your-key>"  # e.g. AIzaSy...
   uvicorn api:app --reload
   ```

   Open `static/index.html` in your browser and interact with the quiz. The
   server selects question difficulty based on your accuracy and uses Gemini for
   feedback. This API structure is compatible with serverless hosts such as
   Vercel.

## Data Storage

The `data/` folder contains JSON files for the knowledge base and each
student’s progress. These files are ignored by git by default.

It also includes `questions.json`, a small sample bank of quiz questions at
three difficulty levels used by the web demo.

## Disclaimer

ThinkBot is a prototype. It does not enforce strict curriculum design and
relies on the quality of the underlying model and material. Review all content
before using it in a learning environment.

## License

This project is released under the MIT license. See [LICENSE](LICENSE).

