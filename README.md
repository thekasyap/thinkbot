# ThinkBot

ThinkBot is an intelligent, adaptive quiz application powered by Google's Gemini AI that provides personalized learning experiences. It features a modern web interface, comprehensive analytics, and smart answer matching to create an engaging educational platform.

## 🌟 Features

### Core Learning Features
- **Adaptive Difficulty**: Questions automatically adjust based on student performance
- **Smart Answer Matching**: Mathematical equivalence and intelligent text matching
- **Personalized Feedback**: AI-generated feedback tailored to each student's learning style
- **Learning Analytics**: Detailed insights into student progress and learning patterns
- **Multiple Question Types**: Math, science, geography, and general knowledge
- **Real-time Hints**: Contextual hints when students need help

### Advanced Analytics
- **Student Profiles**: Comprehensive tracking of individual progress
- **Learning Style Detection**: Identifies visual, auditory, kinesthetic, or reading preferences
- **Performance Metrics**: Accuracy, response time, engagement levels, and more
- **Class Overview**: Analytics for multiple students with comparison tools
- **Progress Tracking**: Historical performance and improvement trends

### Technical Features
- **Modern UI**: Responsive design with smooth animations and intuitive interface
- **FastAPI Backend**: High-performance API with automatic documentation
- **Mathematical Equivalence**: Handles fractions, decimals, and various number formats
- **Text Matching**: Flexible matching for geography and general knowledge questions
- **Session Management**: Track quiz sessions and learning progress
- **Data Persistence**: Student data stored locally in JSON format

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ installed on your system
- A Google Gemini API key (free tier available)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd thinkbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your Gemini API key**
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key-here"
   ```

4. **Start the development server**
   ```bash
   python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Open your browser**
   Navigate to `http://localhost:8000` to start using ThinkBot!

## 📊 Usage

### Starting a Quiz Session
1. Enter your name in the student name field
2. Click "Start Now" to begin a personalized quiz
3. Answer questions - the system adapts difficulty based on your performance
4. Get instant feedback powered by AI
5. View detailed analytics to track your learning progress

### Analytics Dashboard
- **Student Profile**: View individual performance metrics
- **Learning Style**: Discover your preferred learning approach
- **Class Overview**: Compare performance across multiple students
- **Progress Tracking**: Monitor improvement over time

## 🔧 Configuration

### Environment Variables
- `GEMINI_API_KEY`: Your Google Gemini API key (required)

### Question Bank
Questions are stored in `data/questions.json` and can be customized:
- Easy, medium, and hard difficulty levels
- Multiple subjects: math, science, geography, general knowledge
- Automatic difficulty adjustment based on performance

## 🧪 Testing

Run the automated tests to verify functionality:
```bash
python -m pytest -q
```

## 📁 Project Structure

```
thinkbot/
├── api/                    # FastAPI backend
│   └── __init__.py        # Main API endpoints
├── data/                   # Student progress and questions
│   ├── questions.json     # Question bank
│   └── student_*.json     # Individual student data
├── static/                 # Frontend files
│   └── index.html         # Main web interface
├── main.py                # Core utilities and Gemini client
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🌐 Deployment

### Vercel (Recommended)
The project is Vercel-compatible and can be deployed with minimal configuration:
1. Connect your GitHub repository to Vercel
2. Set the `GEMINI_API_KEY` environment variable
3. Deploy automatically

### Other Platforms
- **Heroku**: Use the included `Procfile`
- **Railway**: Direct deployment from GitHub
- **Docker**: Use the provided Dockerfile

## 🔒 Privacy & Security

- Student data is stored locally in JSON files
- No personal information is sent to external services except for AI feedback
- All data remains under your control

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

Released under the MIT License. See [LICENSE](LICENSE) for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section in the documentation
2. Open an issue on GitHub
3. Review the API documentation at `/docs` when running locally

---

**ThinkBot - Making learning intelligent, adaptive, and engaging!** 🎓✨
