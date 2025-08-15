# ThinkBot

ThinkBot is a simple learning assistant that runs entirely on your machine. It
uses a locally hosted small language model (e.g. **DeepSeek R1 0528 Qwen3 8B
4bit** via [Ollama](https://ollama.com) or [LM Studio](https://lmstudio.ai))
and augments the model with your own PDF material. Student progress and quiz
results are stored in small JSON files, making it easy to inspect or reset the
state.

## Features

- **Retrieval‑Augmented Generation** – ingest PDFs and retrieve relevant
  snippets during chat.
- **Adaptive tutoring** – responses become simpler if the student struggles,
  and more advanced when they do well.
- **Random quizzing and scoring** – the bot occasionally asks short questions
  and keeps track of correct answers for each student.
- **Offline friendly** – all data and models stay on your machine.

## Requirements

- Python 3.9+
- A locally running LLM exposing an OpenAI compatible chat completion API.
  - Example with Ollama: `ollama run deepseek-r1:latest` and keep the server
    running at `http://localhost:11434`.
- Python dependencies listed in `requirements.txt`.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

If your model endpoint differs, edit `API_URL` and `MODEL` at the top of
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

## Data Storage

The `data/` folder contains JSON files for the knowledge base and each
student’s progress. These files are ignored by git by default.

## Disclaimer

ThinkBot is a prototype. It does not enforce strict curriculum design and
relies on the quality of the underlying model and material. Review all content
before using it in a learning environment.

## License

This project is released under the MIT license. See [LICENSE](LICENSE).

