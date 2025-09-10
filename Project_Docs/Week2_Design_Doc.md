# Week 2: Design Doc + Data Collection/Preprocessing

## Project: ThinkBot - AI-Powered Adaptive Learning Platform
**Developer:** Aditya Kasyap  
**Week:** 2 of 4  
**Focus:** System Design, Architecture, and Data Pipeline

---

## 1. System Architecture Overview

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   AI Service    │
│   (HTML/CSS/JS) │◄──►│   (FastAPI)     │◄──►│   (Gemini AI)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Data Layer    │
                       │   (JSON Files)  │
                       └─────────────────┘
```

### Component Responsibilities

#### **Frontend Layer**
- **User Interface**: Modern, responsive web interface
- **Real-time Updates**: Dynamic content updates without page refresh
- **Session Management**: Track user interactions and session state
- **Analytics Display**: Visual representation of learning progress

#### **Backend API Layer**
- **Question Management**: Serve adaptive questions based on student profile
- **Answer Processing**: Validate and score student responses
- **Profile Management**: Track and update student learning profiles
- **Analytics Engine**: Generate learning insights and recommendations

#### **AI Service Layer**
- **Personalized Feedback**: Generate contextual feedback using Gemini AI
- **Learning Style Analysis**: Analyze behavioral patterns to identify learning preferences
- **Adaptive Recommendations**: Suggest next learning actions based on performance

#### **Data Layer**
- **Question Bank**: Structured question database with metadata
- **Student Profiles**: Individual learning progress and preferences
- **Session Data**: Detailed learning session records
- **Analytics Data**: Aggregated learning insights and trends

---

## 2. Detailed System Design

### 2.1 Database Schema Design

#### **Question Schema**
```json
{
  "id": "unique_identifier",
  "question": "question_text",
  "answer": "correct_answer",
  "topic": "subject_category",
  "difficulty": "easy|medium|hard",
  "hint": "contextual_hint",
  "explanation": "detailed_explanation",
  "learning_objectives": ["objective1", "objective2"],
  "prerequisites": ["required_knowledge"],
  "estimated_time": "seconds_to_complete"
}
```

#### **Student Profile Schema**
```json
{
  "name": "student_name",
  "learning_sessions": [
    {
      "question_id": "question_identifier",
      "difficulty": "question_difficulty",
      "answer": "student_answer",
      "correct": "boolean",
      "response_time": "seconds",
      "answer_changes": "number_of_edits",
      "hints_used": "number_of_hints",
      "timestamp": "iso_datetime",
      "topic": "question_topic"
    }
  ],
  "learning_style": "visual|auditory|kinesthetic|reading|unknown",
  "engagement_level": "highly_engaged|engaged|moderate|struggling|disengaged",
  "learning_pace": "fast|moderate|slow",
  "topic_preferences": {
    "topic_name": {
      "total": "questions_attempted",
      "correct": "correct_answers",
      "avg_time": "average_response_time"
    }
  },
  "difficulty_progression": ["easy", "medium", "hard"],
  "engagement_score": "0-100",
  "last_activity": "iso_datetime"
}
```

### 2.2 API Design

#### **Core Endpoints**

##### **Question Management**
```python
GET /question?student={name}&topic={optional}
# Returns: {id, question, difficulty, topic}

POST /answer
# Body: {student, question_id, answer, response_time, answer_changes, hints_used}
# Returns: {correct, feedback, accuracy, next_action, insights}
```

##### **Analytics Endpoints**
```python
GET /analytics/{student}
# Returns: Complete student learning profile and insights

GET /analytics
# Returns: Class-wide analytics and comparisons

GET /learning-style/{student}
# Returns: Detailed learning style analysis
```

##### **Session Management**
```python
POST /end-quiz-session?student={name}
# Ends current quiz session and updates statistics

DELETE /clear-student/{student}
# Clears all data for specific student
```

### 2.3 Adaptive Algorithm Design

#### **Difficulty Selection Algorithm**
```python
def select_question_difficulty(profile):
    recent_accuracy = calculate_recent_accuracy(profile, last_n=5)
    engagement_level = profile.engagement_level
    learning_pace = profile.learning_pace
    
    if engagement_level == "struggling" or recent_accuracy < 0.3:
        return "easy"
    elif engagement_level == "highly_engaged" and recent_accuracy > 0.8:
        return "hard"
    elif learning_pace == "fast" and recent_accuracy > 0.7:
        return "hard"
    elif learning_pace == "slow" and recent_accuracy < 0.6:
        return "easy"
    else:
        return "medium"
```

#### **Learning Style Detection Algorithm**
```python
def detect_learning_style(profile):
    scores = {
        'visual': 0,
        'auditory': 0,
        'kinesthetic': 0,
        'reading': 0
    }
    
    # Analyze performance patterns
    visual_questions = filter_by_topic(profile, ['geometry', 'colors', 'patterns'])
    if visual_questions:
        scores['visual'] += calculate_visual_score(visual_questions)
    
    # Analyze behavioral patterns
    scores['kinesthetic'] += profile.hint_dependency * 0.4
    scores['reading'] += calculate_reading_score(profile)
    
    return max(scores, key=scores.get)
```

---

## 3. Data Collection Strategy

### 3.1 Question Bank Development

#### **Phase 1: Core Question Set (200 questions)**
- **Arithmetic**: 50 questions (basic operations, number sense)
- **Fractions**: 30 questions (addition, subtraction, multiplication, division)
- **Geometry**: 40 questions (shapes, angles, area, perimeter)
- **Algebra**: 30 questions (basic equations, variables)
- **Colors**: 25 questions (color mixing, recognition)
- **Geography**: 25 questions (capitals, countries, landmarks)

#### **Phase 2: Expanded Question Set (500+ questions)**
- **Calculus**: 50 questions (derivatives, integrals, limits)
- **Exponents**: 30 questions (power rules, scientific notation)
- **Word Problems**: 40 questions (real-world applications)
- **Patterns**: 30 questions (sequences, logic patterns)
- **Science**: 50 questions (basic physics, chemistry, biology)

#### **Question Quality Standards**
- **Clarity**: Unambiguous wording and clear instructions
- **Appropriate Difficulty**: Validated difficulty levels
- **Educational Value**: Aligned with learning objectives
- **Diverse Formats**: Multiple question types and answer formats
- **Comprehensive Hints**: Helpful guidance without giving away answers

### 3.2 Data Preprocessing Pipeline

#### **Answer Normalization Process**
```python
def normalize_answer(answer):
    """Convert various answer formats to standardized form"""
    # Remove extra whitespace and convert to lowercase
    normalized = answer.strip().lower()
    
    # Handle mathematical expressions
    if '/' in normalized:
        try:
            return str(Fraction(normalized))
        except:
            pass
    
    # Handle decimal numbers
    try:
        return str(Decimal(normalized))
    except:
        pass
    
    return normalized

def is_mathematically_equivalent(answer1, answer2):
    """Check if two answers are mathematically equivalent"""
    # Direct string comparison
    if normalize_answer(answer1) == normalize_answer(answer2):
        return True
    
    # Mathematical equivalence check
    try:
        val1 = float(Fraction(answer1)) if '/' in answer1 else float(answer1)
        val2 = float(Fraction(answer2)) if '/' in answer2 else float(answer2)
        return abs(val1 - val2) < 1e-10
    except:
        return False
```

#### **Topic Classification System**
```python
TOPIC_MAPPING = {
    'arithmetic': ['addition', 'subtraction', 'multiplication', 'division'],
    'fractions': ['fraction_operations', 'equivalent_fractions', 'mixed_numbers'],
    'geometry': ['shapes', 'angles', 'area', 'perimeter', 'volume'],
    'algebra': ['equations', 'variables', 'expressions', 'inequalities'],
    'colors': ['color_mixing', 'color_recognition', 'color_theory'],
    'geography': ['capitals', 'countries', 'landmarks', 'continents']
}
```

### 3.3 Student Data Collection

#### **Session Data Collection**
```python
def record_learning_session(profile, question_id, difficulty, answer, 
                          correct, response_time, answer_changes=0, 
                          hints_used=0, topic="general"):
    """Record comprehensive learning session data"""
    session = {
        'question_id': question_id,
        'difficulty': difficulty,
        'answer': answer,
        'correct': correct,
        'response_time': response_time,
        'answer_changes': answer_changes,
        'hints_used': hints_used,
        'timestamp': datetime.now().isoformat(),
        'topic': topic
    }
    
    profile.learning_sessions.append(session)
    update_learning_metrics(profile)
    profile.save()
```

#### **Behavioral Metrics Collection**
- **Response Time**: Time taken to answer each question
- **Answer Changes**: Number of edits made before submission
- **Hint Usage**: Frequency and pattern of hint requests
- **Skip Rate**: Percentage of questions skipped
- **Session Frequency**: How often student engages with the platform
- **Topic Preferences**: Performance patterns across different subjects

---

## 4. Data Storage and Management

### 4.1 File Structure
```
data/
├── questions.json          # Question bank
├── student_*.json         # Individual student profiles
└── analytics_cache.json   # Cached analytics data
```

### 4.2 Data Persistence Strategy
- **JSON Format**: Human-readable, easy to debug and modify
- **Local Storage**: No external database dependencies
- **Atomic Writes**: Ensure data integrity during updates
- **Backup Strategy**: Regular data exports for safety

### 4.3 Data Privacy and Security
- **Local Processing**: All data remains on user's system
- **No Personal Information**: Only learning-related data collected
- **Data Ownership**: Users maintain full control over their data
- **Export Capability**: Easy data export for portability

---

## 5. Performance Considerations

### 5.1 Response Time Optimization
- **Question Caching**: Pre-load questions for faster delivery
- **Lazy Loading**: Load analytics data only when needed
- **Efficient Algorithms**: Optimized difficulty selection and style detection
- **Minimal API Calls**: Reduce external service dependencies

### 5.2 Scalability Design
- **Stateless API**: Easy horizontal scaling
- **Efficient Data Structures**: Optimized for fast lookups
- **Memory Management**: Careful handling of large datasets
- **Caching Strategy**: Reduce redundant calculations

### 5.3 Error Handling
- **Graceful Degradation**: System continues working with reduced functionality
- **User-Friendly Messages**: Clear error communication
- **Logging System**: Comprehensive error tracking
- **Recovery Mechanisms**: Automatic retry and fallback options

---

## 6. Testing Strategy

### 6.1 Unit Testing
- **Answer Matching**: Test mathematical equivalence detection
- **Profile Management**: Test student data operations
- **API Endpoints**: Test all API functionality
- **Learning Algorithms**: Test adaptive difficulty and style detection

### 6.2 Integration Testing
- **End-to-End Workflows**: Complete user journeys
- **Data Consistency**: Ensure data integrity across operations
- **Performance Testing**: Load testing and response time validation
- **Cross-Platform Testing**: Browser and device compatibility

### 6.3 User Acceptance Testing
- **Usability Testing**: Interface and user experience validation
- **Educational Effectiveness**: Learning outcome assessment
- **Accessibility Testing**: Support for different learning needs
- **Feedback Integration**: User feedback incorporation

---

## 7. Implementation Timeline

### Week 2 Deliverables
- ✅ **System Architecture**: Complete technical design
- ✅ **Database Schema**: Detailed data models
- ✅ **API Specification**: Complete endpoint documentation
- ✅ **Data Pipeline**: Question preprocessing and student data collection
- 🔄 **Core Implementation**: Basic API and frontend structure

### Week 3 Preparation
- **Advanced Features**: AI integration and personalization
- **Analytics Engine**: Learning insights and recommendations
- **UI/UX Enhancement**: Modern interface and user experience
- **Testing Framework**: Comprehensive test suite

---

## 8. Risk Mitigation

### Technical Risks
- **AI Service Dependencies**: Implement fallback mechanisms
- **Performance Bottlenecks**: Optimize algorithms and caching
- **Data Integrity**: Implement robust error handling and validation

### Educational Risks
- **Learning Style Misclassification**: Use confidence scoring and multiple indicators
- **Over-Personalization**: Maintain educational standards and diversity
- **Engagement Measurement**: Use multi-dimensional metrics

---

## 9. Success Metrics

### Technical Metrics
- **API Response Time**: <2 seconds for all endpoints
- **Answer Matching Accuracy**: >95% correct identification
- **System Uptime**: >99% availability
- **Test Coverage**: >90% code coverage

### Educational Metrics
- **Learning Progression**: Measurable improvement over time
- **Engagement Levels**: Increased session frequency and duration
- **Adaptive Effectiveness**: Correlation between difficulty adjustment and performance
- **User Satisfaction**: Positive feedback on personalized experience

---

## 10. Next Steps

### Immediate Actions
1. **Implement Core API**: Basic question serving and answer processing
2. **Develop Frontend**: Essential user interface components
3. **Create Test Suite**: Automated testing framework
4. **Data Validation**: Ensure question bank quality and consistency

### Week 3 Preparation
1. **AI Integration**: Implement Gemini AI for personalized feedback
2. **Analytics Engine**: Build comprehensive learning insights
3. **Advanced UI**: Enhance user experience and visual design
4. **Performance Optimization**: Ensure smooth operation under load

---

**Conclusion**: This design document provides a comprehensive foundation for implementing ThinkBot's core functionality. The modular architecture, robust data pipeline, and adaptive algorithms will ensure a scalable and effective learning platform that can evolve with user needs and educational requirements.

**Next Phase**: Proceed to Week 3 for prototype implementation and advanced feature development.
