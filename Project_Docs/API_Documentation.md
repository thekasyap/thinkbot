# API Documentation - ThinkBot

## Overview
ThinkBot provides a RESTful API built with FastAPI for managing adaptive learning sessions, student profiles, and analytics.

**Base URL**: `http://localhost:8001`  
**API Version**: 1.0  
**Content Type**: `application/json`

---

## Authentication
Currently, the API does not require authentication. All endpoints are publicly accessible.

---

## Endpoints

### Question Management

#### Get Question
**GET** `/question`

Get an adaptive question for a student based on their learning profile.

**Query Parameters:**
- `student` (string, required): Student name
- `topic` (string, optional): Specific topic filter

**Response:**
```json
{
  "id": 1,
  "question": "What is 1/2 + 1/4?",
  "difficulty": "medium",
  "topic": "fractions"
}
```

**Example:**
```bash
curl "http://localhost:8001/question?student=Alice&topic=fractions"
```

#### Submit Answer
**POST** `/answer`

Submit a student's answer and receive personalized feedback.

**Request Body:**
```json
{
  "student": "Alice",
  "question_id": 1,
  "answer": "3/4",
  "response_time": 15.5,
  "answer_changes": 2,
  "hints_used": 1
}
```

**Response:**
```json
{
  "correct": true,
  "feedback": "Excellent work! You correctly added the fractions by finding a common denominator...",
  "accuracy": 85.5,
  "engagement_level": "engaged",
  "learning_style": "visual",
  "next_action": "continue_learning",
  "hint": "Find a common denominator first",
  "insights": {
    "recent_performance": 80.0,
    "consistency_score": 75.0,
    "learning_momentum": 5.2
  }
}
```

**Example:**
```bash
curl -X POST "http://localhost:8001/answer" \
  -H "Content-Type: application/json" \
  -d '{"student": "Alice", "question_id": 1, "answer": "3/4", "response_time": 15.5}'
```

### Analytics

#### Get Student Analytics
**GET** `/analytics/{student}`

Get comprehensive learning analytics for a specific student.

**Path Parameters:**
- `student` (string): Student name

**Response:**
```json
{
  "student_name": "Alice",
  "total_quizzes": 25,
  "accuracy": 78.5,
  "learning_style": "visual",
  "engagement_level": "engaged",
  "learning_pace": "moderate",
  "average_response_time": 22.3,
  "hesitation_score": 1.2,
  "engagement_score": 72.5,
  "recent_performance": 80.0,
  "consistency_score": 75.0,
  "learning_momentum": 5.2,
  "needs_attention": false,
  "topic_preferences": {
    "fractions": {"total": 8, "correct": 6, "avg_time": 18.5},
    "algebra": {"total": 12, "correct": 10, "avg_time": 25.2}
  },
  "difficulty_progression": ["easy", "medium", "hard"],
  "learning_sessions": [...],
  "quiz_sessions": 5
}
```

**Example:**
```bash
curl "http://localhost:8001/analytics/Alice"
```

#### Get All Analytics
**GET** `/analytics`

Get analytics for all students (class overview).

**Response:**
```json
{
  "total_students": 5,
  "students": [
    {
      "student_name": "Alice",
      "total_quizzes": 25,
      "accuracy": 78.5,
      "engagement_level": "engaged",
      "learning_style": "visual"
    }
  ],
  "summary": {
    "high_performers": 2,
    "struggling_students": 1,
    "average_accuracy": 72.3
  }
}
```

**Example:**
```bash
curl "http://localhost:8001/analytics"
```

#### Get Learning Style Analysis
**GET** `/learning-style/{student}`

Get detailed learning style analysis for a student.

**Path Parameters:**
- `student` (string): Student name

**Response:**
```json
{
  "primary_style": "visual",
  "confidence": "high",
  "reasoning": "Strong performance on visual/spatial tasks (score: 0.85)",
  "scores": {
    "visual": 0.85,
    "auditory": 0.45,
    "kinesthetic": 0.32,
    "reading": 0.28
  },
  "recommendations": [
    "Use diagrams and visual aids when studying",
    "Try drawing out problems before solving them",
    "Look for patterns and visual relationships in math problems"
  ]
}
```

**Example:**
```bash
curl "http://localhost:8001/learning-style/Alice"
```

### Session Management

#### End Quiz Session
**POST** `/end-quiz-session`

End a quiz session and update statistics.

**Query Parameters:**
- `student` (string, required): Student name

**Response:**
```json
{
  "message": "Quiz session ended successfully",
  "session_stats": {
    "questions_answered": 10,
    "correct_answers": 8,
    "accuracy": 80.0,
    "session_duration": 15.5
  }
}
```

**Example:**
```bash
curl -X POST "http://localhost:8001/end-quiz-session?student=Alice"
```

#### Clear Student Data
**DELETE** `/clear-student/{student}`

Clear all data for a specific student.

**Path Parameters:**
- `student` (string): Student name

**Response:**
```json
{
  "message": "Student data cleared successfully"
}
```

**Example:**
```bash
curl -X DELETE "http://localhost:8001/clear-student/Alice"
```

### Hints

#### Get Hint
**GET** `/hint/{question_id}`

Get a hint for a specific question.

**Path Parameters:**
- `question_id` (integer): Question ID

**Response:**
```json
{
  "question_id": 1,
  "hint": "Find a common denominator first",
  "topic": "fractions"
}
```

**Example:**
```bash
curl "http://localhost:8001/hint/1"
```

### Utility Endpoints

#### Test Math Equivalence
**GET** `/test-math`

Test the mathematical equivalence detection system.

**Response:**
```json
{
  "test": "0.5 == 1/2",
  "result": true
}
```

**Example:**
```bash
curl "http://localhost:8001/test-math"
```

#### Simple Test
**GET** `/test-simple`

Simple health check endpoint.

**Response:**
```json
{
  "message": "Simple test works"
}
```

**Example:**
```bash
curl "http://localhost:8001/test-simple"
```

---

## Error Handling

### HTTP Status Codes
- `200 OK`: Request successful
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Scenarios

#### Student Not Found
```json
{
  "detail": "Student profile not found"
}
```

#### Invalid Question ID
```json
{
  "detail": "Unknown question"
}
```

#### Missing Required Fields
```json
{
  "detail": [
    {
      "loc": ["body", "student"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Data Models

### Student Profile
```json
{
  "name": "string",
  "quizzes": "integer",
  "correct": "integer",
  "total_response_time": "float",
  "total_answer_changes": "integer",
  "total_hints_used": "integer",
  "total_skipped": "integer",
  "quiz_sessions": "integer",
  "learning_sessions": "array",
  "learning_style": "string",
  "preferred_difficulty": "string",
  "engagement_score": "float",
  "last_activity": "string",
  "streak_days": "integer",
  "improvement_trend": "float",
  "session_frequency": "float",
  "difficulty_progression": "array",
  "topic_preferences": "object"
}
```

### Learning Session
```json
{
  "question_id": "integer",
  "difficulty": "string",
  "answer": "string",
  "correct": "boolean",
  "response_time": "float",
  "answer_changes": "integer",
  "hints_used": "integer",
  "timestamp": "string",
  "topic": "string"
}
```

### Question
```json
{
  "id": "integer",
  "question": "string",
  "answer": "string",
  "topic": "string",
  "difficulty": "string",
  "hint": "string",
  "explanation": "string"
}
```

---

## Rate Limiting
Currently, there are no rate limits implemented. For production deployment, consider implementing rate limiting to prevent abuse.

---

## CORS
CORS is enabled for all origins. For production deployment, configure CORS to restrict access to specific domains.

---

## WebSocket Support
Currently, the API does not support WebSocket connections. All communication is through HTTP requests.

---

## API Versioning
The current API version is 1.0. Future versions will be available at `/api/v2/`, `/api/v3/`, etc.

---

## SDKs and Libraries
Currently, no official SDKs are available. The API can be consumed using any HTTP client library in any programming language.

### Python Example
```python
import requests

# Get a question
response = requests.get("http://localhost:8001/question?student=Alice")
question = response.json()

# Submit an answer
answer_data = {
    "student": "Alice",
    "question_id": question["id"],
    "answer": "3/4",
    "response_time": 15.5
}
response = requests.post("http://localhost:8001/answer", json=answer_data)
result = response.json()
```

### JavaScript Example
```javascript
// Get a question
const questionResponse = await fetch("http://localhost:8001/question?student=Alice");
const question = await questionResponse.json();

// Submit an answer
const answerResponse = await fetch("http://localhost:8001/answer", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    student: "Alice",
    question_id: question.id,
    answer: "3/4",
    response_time: 15.5
  })
});
const result = await answerResponse.json();
```

---

## Support
For API support and questions:
- Check the comprehensive documentation in `Project_Docs/`
- Search existing GitHub issues
- Use GitHub Discussions for questions
- Contact the developer for direct support

---

*This API documentation is part of the ThinkBot project documentation suite.*
