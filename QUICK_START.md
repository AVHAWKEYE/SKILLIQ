# SkillIQ Quick Start Guide

## ⚡ 30-Second Setup

### 1. Install Dependencies
```powershell
cd P:\SkillIQ
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run Server
```powershell
python .\server.py
```
Or:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Open Browser
```
http://127.0.0.1:8000/auth.html
```

---

## 🎯 First Test Run

### **As a Teacher**

1. Go to `http://127.0.0.1:8000/auth.html`
2. Click "Register"
3. Select **Teacher** role
4. Fill in details:
   - Full Name: Test Teacher
   - Email: teacher@test.com
   - Username: testteacher
   - Password: Test123!
5. Click "Create Account"
6. Login with credentials
7. Redirects to `teacher.html`
8. Click "Create New Test"
9. Fill in test details and publish
10. View results when students take it

### **As a Student**

1. Go to `http://127.0.0.1:8000/auth.html`
2. Click "Register"
3. Select **Student** role
4. Fill in details:
   - Full Name: Test Student
   - Email: student@test.com
   - Username: teststudent
   - Password: Test123!
5. Click "Create Account"
6. Login with credentials
7. Redirects to `student.html`
8. See "Available Tests" tab
9. Click "Start Test"
10. Answer questions
11. Submit and see AI insights

---

## 📚 Key Features to Try

### **For Students**
- ✅ Take tests
- ✅ View AI insights
- ✅ Access learning resources
- ✅ Track performance

### **For Teachers**
- ✅ Create tests with questions
- ✅ Publish to students
- ✅ View student results
- ✅ See class analytics

### **AI Insights Demo**
- After taking a test, click "AI Insights"
- See personalized recommendations
- View action items
- Access linked resources

---

## 🔗 Main URLs

| Page | URL |
|------|-----|
| Login/Register | `/auth.html` |
| Student Dashboard | `/student.html` |
| Teacher Dashboard | `/teacher.html` |
| API Documentation | `/docs` |
| Health Check | `/api/health` |

---

## 📊 API Quick Examples

### **Create a Test (cURL)**
```bash
curl -X POST "http://127.0.0.1:8000/api/tests" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Math Quiz",
    "description": "Basic math",
    "test_type": "homework",
    "difficulty": "medium",
    "duration_minutes": 30,
    "passing_score": 60,
    "questions": [
      {
        "question_text": "2+2=?",
        "question_type": "mcq",
        "options": ["3","4","5","6"],
        "correct_answer": "4",
        "explanation": "Simple addition",
        "difficulty": "easy",
        "skill_tag": "math",
        "points": 1
      }
    ]
  }'
```

### **Get AI Insights (cURL)**
```bash
curl -X GET "http://127.0.0.1:8000/api/insights" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **Start Test (JavaScript)**
```javascript
const token = localStorage.getItem('authToken');
const response = await fetch('/api/tests/1/attempt/start', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
const attempt = await response.json();
console.log('Started attempt:', attempt.id);
```

---

## 🔐 Default Test Accounts

**After first run, create these:**

| Role | Username | Email | Password |
|------|----------|-------|----------|
| Admin | admin | admin@skilliq.com | Admin123! |
| Teacher | teacher1 | teacher@skilliq.com | Teacher123! |
| Student | student1 | student@skilliq.com | Student123! |

---

## 📝 Configuration

### **Change JWT Secret (Important for Production)**

Edit `app/auth.py` line ~12:
```python
SECRET_KEY = os.getenv("SECRET_KEY", "your-very-secure-secret-key-here")
```

Or set environment variable:
```powershell
$env:SECRET_KEY = "my-super-secret-key"
```

### **Change Token Expiration**

Edit `app/auth.py` line ~14:
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
```

---

## 📦 Database

### **Location**
`P:\SkillIQ\skilliq.db`

### **View Database** (using Python)
```python
import sqlite3
conn = sqlite3.connect('skilliq.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(table[0])
```

### **Reset Database**
Simply delete `skilliq.db` and restart server (will recreate)

---

## 🎨 Frontend Customization

### **Change App Colors**

In any HTML file, look for `:root` variables:
```css
:root {
    --purple: #6C63FF;
    --teal: #43E8D8;
    --pink: #FF6B9D;
    --bg: #f2f0ff;
}
```

Modify colors as desired.

---

## 🚀 Production Deployment

### **Before Going Live**

1. **Change Secret Key** ✅
2. **Use PostgreSQL** instead of SQLite
3. **Enable HTTPS** ✅
4. **Set CORS properly** ✅
5. **Use environment variables** for config
6. **Add logging** and monitoring
7. **Set up backups**
8. **Test thoroughly** ✅

### **Quick PostgreSQL Setup**

Update `app/database.py`:
```python
DATABASE_URL = "postgresql://user:password@localhost/skilliq"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Remove this for PostgreSQL
    pool_pre_ping=True,  # Add this
)
```

Install PostgreSQL driver:
```powershell
pip install psycopg2-binary
```

---

## 📞 Common Commands

### **Start Dev Server**
```powershell
python .\server.py
```

### **Start with Reload**
```powershell
uvicorn app.main:app --reload
```

### **Install Dependencies**
```powershell
pip install -r requirements.txt
```

### **View API Docs**
Open `http://127.0.0.1:8000/docs` in browser

### **Test API Endpoint**
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health"
```

---

## 🧪 Testing Checklist

- [ ] User registration works
- [ ] Login returns JWT token
- [ ] Teacher can create test
- [ ] Teacher can publish test
- [ ] Student can see published test
- [ ] Student can start test
- [ ] Student can submit test
- [ ] Results show correct score
- [ ] AI insights generate
- [ ] Insights contain recommendations
- [ ] Analytics dashboard loads
- [ ] API docs page works

---

## 🆘 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | Change port: `--port 8001` |
| Module not found | Run `pip install -r requirements.txt` |
| Database locked | Delete `skilliq.db` and restart |
| No insights showing | Try `POST /api/insights/generate` |
| Can't login | Check username/password in response |
| CORS error | Already enabled in `main.py` |

---

## 📖 Next Steps

1. **Read** `IMPLEMENTATION_GUIDE.md` for full details
2. **Review** API documentation at `/docs`
3. **Explore** code in `app/` folder
4. **Customize** as needed for your use case
5. **Deploy** when ready

---

## 🎓 Learning Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://www.sqlalchemy.org/
- **JWT Auth**: https://jwt.io/
- **Pydantic**: https://pydantic-ai.jina.ai/

---

**Enjoy using SkillIQ!** 🚀
