# SkillIQ - AI-Powered Student Performance Platform

**Version 2.0** - Now with AI Insights, Teacher Tools, and Live Testing

SkillIQ is a comprehensive web application that uses artificial intelligence to analyze student performance, generate personalized learning recommendations, and provide teachers with actionable insights to improve classroom outcomes.

## ✨ Key Features

### 🎓 For Students
- **AI-Powered Insights** - Personalized recommendations based on performance
- **Learning Resources** - Curated videos, articles, and books matched to your skills
- **Performance Tracking** - Monitor progress across all assessments
- **Self-Paced Learning** - Take tests anytime, anywhere
- **Skill Development** - Receive action items for improvement

### 👨‍🏫 For Teachers
- **Test Management** - Create, edit, and publish tests easily
- **Class Analytics** - See detailed performance metrics for all students
- **Student Results** - View individual and class-wide statistics
- **Live Testing** - Host real-time tests with instant feedback
- **Performance Reports** - Export comprehensive analytics reports
- **Resource Library** - Add and manage learning materials

### 🤖 AI Engine
- **Performance Analysis** - Intelligent assessment of student abilities
- **Skill Gap Detection** - Automatic identification of improvement areas
- **Personalized Recommendations** - Custom action plans for each student
- **Resource Matching** - Smart connection between skills and learning materials
- **Trend Analysis** - Track improvement over time
- **Confidence Scoring** - AI confidence levels for all recommendations

### 🔐 Security & Access Control
- **JWT Authentication** - Secure token-based login
- **Role-Based Access** - Student, Teacher, and Admin roles
- **Data Privacy** - Isolated student data by design
- **Encrypted Passwords** - Industry-standard bcrypt hashing

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Windows/Linux/Mac
- Modern web browser

### Installation (Windows PowerShell)

```powershell
# Navigate to project
cd P:\SkillIQ

# Create virtual environment
python -m venv .venv

# Activate environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run server
python .\server.py
```

### Access the App

```
Frontend: http://127.0.0.1:8000
Auth:     http://127.0.0.1:8000/auth.html
API Docs: http://127.0.0.1:8000/docs
```

---

## 📁 Project Structure

```
SkillIQ/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application & endpoints
│   ├── auth.py              # Authentication & JWT
│   ├── models.py            # Database models (7 tables)
│   ├── schemas.py           # Pydantic schemas (15+ types)
│   ├── database.py          # SQLAlchemy setup
│   ├── ml.py                # Machine learning models
│   └── insights.py          # AI insights engine
├── frontend/
│   ├── index.html           # Home page
│   ├── auth.html            # Login/Register
│   ├── student.html         # Student dashboard
│   ├── teacher.html         # Teacher dashboard
│   ├── admin.html           # Admin panel
│   ├── css/
│   │   ├── glass.css        # Glass morphism styles
│   │   └── style.css        # Main styles
│   └── js/
│       ├── app.js           # Main app logic
│       ├── data.js          # Questions & data
│       └── glass-shared.js  # Shared utilities
├── model_artifacts/         # ML model files
├── scripts/                 # Utility scripts
├── data/                    # Sample datasets
├── requirements.txt         # Python dependencies
├── server.py               # Flask server
├── QUICK_START.md          # 30-second setup guide
└── IMPLEMENTATION_GUIDE.md # Complete documentation
```

---

## 🗄️ Database Schema

### Core Tables

**users** - User accounts
```
id, username, email, password_hash, role, is_active, created_at
```

**tests** - Teacher-created tests
```
id, created_by, title, description, test_type, difficulty, 
duration_minutes, passing_score, is_published, is_live, created_at
```

**test_questions** - Questions within tests
```
id, test_id, question_text, question_type, options, correct_answer,
explanation, difficulty, skill_tag, points, order
```

**test_attempts** - Student test submissions
```
id, test_id, student_id, status, score, percentage, answers,
start_time, submit_time, time_taken_seconds, is_passed
```

**ai_insights** - Generated recommendations
```
id, user_id, insight_type, skill_name, current_score, benchmark_score,
recommendation_text, confidence_score, action_items, resource_id,
priority_level, is_read, created_at
```

**learning_resources** - Educational materials
```
id, title, description, resource_type, skill_tag, difficulty,
url, duration_minutes, instructor, rating, views, is_verified
```

**performance_metrics** - Aggregate statistics
```
id, user_id, test_id, metric_type, category, total_attempts,
successful_attempts, average_score, highest_score, improvement_rate
```

---

## 🔌 API Endpoints

### Authentication
```
POST   /api/auth/register              - Create account
POST   /api/auth/login                 - Login (returns JWT)
GET    /api/auth/me                    - Current user info
PATCH  /api/auth/update-profile        - Update profile
```

### Tests
```
POST   /api/tests                      - Create test (teacher)
GET    /api/tests                      - List tests
GET    /api/tests/{id}                 - Get test details
PATCH  /api/tests/{id}                 - Update test
DELETE /api/tests/{id}                 - Delete test
POST   /api/tests/{id}/publish         - Publish to students
GET    /api/tests/{id}/attempts        - Get all attempts
```

### Test Attempts
```
POST   /api/tests/{id}/attempt/start   - Start test (student)
POST   /api/test-attempts/{id}/submit  - Submit answers
GET    /api/test-attempts/{id}         - Get attempt details
```

### AI Insights
```
GET    /api/insights                   - Get insights
POST   /api/insights/generate          - Generate new insights
PATCH  /api/insights/{id}/read         - Mark as read
GET    /api/insights/analyze           - Performance analysis
```

### Learning Resources
```
GET    /api/learning-resources         - List resources
POST   /api/learning-resources         - Create (admin)
PATCH  /api/learning-resources/{id}    - Update
POST   /api/learning-resources/{id}/view - Record view
```

### Analytics
```
GET    /api/analytics/student          - Student dashboard metrics
GET    /api/analytics/teacher/test/{id} - Test analytics (teacher)
```

---

## 🎯 Usage Examples

### Student Workflow
1. **Register** as Student
2. **Login** to get access token
3. **Browse** available tests
4. **Start** a test
5. **Answer** questions
6. **Submit** and get results
7. **View** AI insights
8. **Access** learning resources

### Teacher Workflow
1. **Register** as Teacher
2. **Login** to dashboard
3. **Create** a test with questions
4. **Publish** to make visible
5. **Monitor** student attempts
6. **View** analytics and results
7. **Guide** based on performance

### API Usage
```javascript
// Login
const response = await fetch('/api/auth/login?username=user&password=pass', {
  method: 'POST'
});
const {access_token} = await response.json();

// Create test
const test = await fetch('/api/tests', {
  method: 'POST',
  headers: {'Authorization': `Bearer ${access_token}`},
  body: JSON.stringify({
    title: "Math Quiz",
    questions: [...],
    test_type: "homework"
  })
});

// Start test attempt
const attempt = await fetch('/api/tests/1/attempt/start', {
  method: 'POST',
  headers: {'Authorization': `Bearer ${access_token}`}
});

// Get insights
const insights = await fetch('/api/insights', {
  headers: {'Authorization': `Bearer ${access_token}`}
});
```

---

## 🤖 AI Insights System

### How It Works

1. **Data Collection**
   - Gathers all assessments and test attempts
   - Analyzes performance across skills
   - Tracks improvement trends

2. **Analysis**
   - Compares scores to benchmarks
   - Identifies skill gaps
   - Detects improvement patterns
   - Recognizes strengths

3. **Insight Generation**
   - Creates personalized messages
   - Generates action items
   - Matches learning resources
   - Sets priority levels

4. **Delivery**
   - Displays to student
   - Tracks as read/unread
   - Updates periodically

### Example Insights
```json
{
  "insight_type": "skill_gap",
  "skill_name": "Mathematics",
  "current_score": 62,
  "benchmark_score": 70,
  "recommendation_text": "Your Math score is below benchmark. Focus on foundational concepts and practice problems regularly.",
  "action_items": [
    "Review algebra basics",
    "Practice 5-10 problems daily",
    "Watch video tutorials",
    "Take practice tests weekly"
  ],
  "priority_level": "high",
  "confidence_score": 0.85
}
```

---

## 📊 Model Training & Prediction

### ML Model Pipeline

```python
# Train with labeled data
POST /api/train                    # Trains linear regression model

# Predict student performance
POST /api/predict                  # Estimates target score
{
  "selected_skills_count": 5,
  "total_questions": 20,
  "total_correct": 18,
  "accuracy_pct": 90,
  ...
}
```

### Requirements
- Minimum 12 labeled assessment records
- Uses scikit-learn for regression
- Model artifacts stored in `model_artifacts/`

---

## 🔐 Authentication

### Registration
```json
POST /api/auth/register
{
  "username": "john_student",
  "email": "john@example.com",
  "full_name": "John Student",
  "password": "SecurePass123",
  "role": "student"
}
```

### Login
```json
POST /api/auth/login?username=john_student&password=SecurePass123
Response: {
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {...}
}
```

### Token Usage
```
Authorization: Bearer <access_token>
```

---

## 🛠️ Configuration

### Environment Variables
```powershell
$env:SECRET_KEY = "your-secret-key-for-jwt"
$env:DATABASE_URL = "sqlite:///skilliq.db"
```

### Server Settings
```python
app = FastAPI(title="SkillIQ API", version="2.0.0")

# CORS enabled for all origins (configure for production)
# JWT token expires in 24 hours
# SQLite database with auto-migration
```

---

## 📈 Analytics & Reports

### Student Dashboard
- Total assessments completed
- Average scores
- Skills breakdown
- Performance trends
- Recent insights

### Teacher Dashboard
- Class metrics
- Test creation count
- Student attempt count
- Average class score
- Pass rate

### Detailed Analytics
- Skill-by-skill breakdown
- Performance trends over time
- Improvement rates
- Lowest and highest performers
- Time-to-completion statistics

---

## 🚀 Deployment

### Development
```powershell
python .\server.py
```

### Production Setup
```bash
# Use PostgreSQL instead of SQLite
pip install psycopg2-binary

# Set strong SECRET_KEY
export SECRET_KEY="your-very-secure-key"

# Run with production ASGI server
pip install gunicorn
gunicorn -w 4 app.main:app
```

### Docker (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

---

## 📚 Documentation

- **Quick Start**: See `QUICK_START.md`
- **Implementation Guide**: See `IMPLEMENTATION_GUIDE.md`
- **API Documentation**: Visit `/docs` when server is running
- **Code Comments**: Review source files for detailed comments

---

## 🧪 Testing

### Run Tests
```powershell
pytest tests/ -v
```

### Test Coverage
```powershell
pytest --cov=app tests/
```

### Manual Testing Checklist
- [ ] User registration
- [ ] User login
- [ ] Test creation
- [ ] Test publication
- [ ] Test attempt submission
- [ ] AI insights generation
- [ ] Resource recommendations
- [ ] Analytics display

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 in use | Use different port: `python server.py --port 8001` |
| Database locked | Delete `skilliq.db` and restart |
| Module errors | Run `pip install -r requirements.txt` |
| CORS errors | Already configured; check domain settings |
| Token expired | Re-login to get new token |

---

## 🗺️ Roadmap

### Completed ✅
- User authentication system
- Test management platform
- Student test attempts
- AI insights generation
- Learning resource integration
- Performance analytics
- Role-based access control

### Planned 🔄
- Live testing with WebSockets
- Real-time notifications
- Mobile application
- Advanced reporting & exports
- Video tutorial integration
- Collaborative features
- Grade book integration
- Parent portal
- Achievement badges

---

## 📝 Changelog

### v2.0 (Current)
- Complete data model redesign
- JWT authentication system
- AI insights engine
- Teacher management tools
- Performance analytics
- Learning resource database
- Role-based access control
- 60+ new API endpoints
- Student & teacher dashboards
- Admin panel
- Comprehensive documentation

### v1.0
- Basic assessment tool
- SkillIQ database
- Model training pipeline
- Prediction API

---

## 📞 Support & Contributing

### Documentation
- API Docs: `http://localhost:8000/docs`
- Quick Start: `QUICK_START.md`
- Full Guide: `IMPLEMENTATION_GUIDE.md`

### Code Structure
- Backend: `app/` folder
- Frontend: `frontend/` folder
- Database: `skilliq.db`
- Models: `model_artifacts/`

### Getting Help
1. Check documentation
2. Review API docs at `/docs`
3. Check code comments
4. Review error messages in server logs

---

## 📄 License

SkillIQ is provided as-is for educational purposes.

---

## 🎓 Educational Value

SkillIQ demonstrates:
- ✅ Full-stack web development
- ✅ RESTful API design
- ✅ Database design & SQLAlchemy ORM
- ✅ JWT authentication
- ✅ Machine learning integration
- ✅ Frontend-backend communication
- ✅ Data analysis & visualization
- ✅ Role-based access control
- ✅ Real-time processing
- ✅ Production deployment

---

## 🙏 Acknowledgments

Built with modern technologies:
- **FastAPI** - Fast web framework
- **SQLAlchemy** - ORM database
- **Pydantic** - Data validation
- **PyJWT** - Authentication
- **scikit-learn** - Machine learning
- **Chart.js** - Data visualization

---

**Welcome to SkillIQ 2.0!** 

Start by reading `QUICK_START.md` for immediate setup, or dive into `IMPLEMENTATION_GUIDE.md` for complete details.

Made with ❤️ for educators and students
	- `participation_score`
	- `study_hours_per_week`
	- `previous_gpa`
- Or send a normal SkillIQ payload (same fields as `/api/predict`), and backend will derive external features automatically.

Response includes:

- `predicted_score` (from `score_predictor.json`)
- `risk_assessment` label + class probabilities (from `risk_assessor.json`)
- `grade_classification` grade + class probabilities (from `grade_classifier.json`)

UI integration:

- Use `Predict (External)` button on assessment completion card.

## Added Dataset Profiles

This project now includes two ready-to-run dataset preparation scripts:

- `scripts/prepare_student_performance_dataset.py` for `student-mat.csv` style data.
- `scripts/prepare_student_performance_10k.py` for `Student_performance_10k.csv` style data.

Example for the 10k CSV:

```powershell
cd P:\SkillIQ
c:/python314/python.exe .\scripts\prepare_student_performance_10k.py --input "C:\Users\Parre Pratyush\Downloads\archive (1)\Student_performance_10k.csv" --output .\data\student_performance_10k_skilliq.csv
c:/python314/python.exe .\scripts\kaggle_import.py --csv .\data\student_performance_10k_skilliq.csv --map .\kaggle_column_map.student_performance.json --train
```

## External Model Artifacts

Attached model files can be stored under:

- `model_artifacts/external_models/`

Use API endpoint `GET /api/external-models` to list synced JSON/PKL artifacts and file details.

## API Endpoints

- `GET /api/health`
- `POST /api/assessments`
- `GET /api/assessments`
- `PATCH /api/assessments/{assessment_id}/label`
- `POST /api/train`
- `POST /api/predict`

## Notes

- Database file: `skilliq.db`
- Trained model artifact: `model_artifacts/linear_model.json`
- Existing AI insights and plan calls in the frontend remain unchanged.
