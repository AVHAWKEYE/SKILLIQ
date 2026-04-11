"""AI Insights and Recommendations Engine"""
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .models import (
    User, Assessment, TestAttempt, Test, AIInsight, LearningResource, PerformanceMetric
)


def _to_float(value: object, default: float = 0.0) -> float:
    """Safely convert potentially ORM-typed values to float."""
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            return float(value)
        return default
    except (TypeError, ValueError):
        return default


def _to_bool(value: object) -> bool:
    """Safely convert potentially ORM-typed values to bool."""
    return bool(value)


class InsightsEngine:
    """Generate AI-powered insights and recommendations for CSE students"""

    def __init__(self, db: Session):
        self.db = db
        self.skill_thresholds = {
            "math": 72,
            "logic": 74,
            "aptitude": 70,
            "problem_solving": 75,
            "reasoning": 70,
        }

    def analyze_student_performance(self, user_id: int) -> Dict:
        """Comprehensive analysis of student performance"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}

        # Get all assessments and test attempts
        assessments = self.db.query(Assessment).filter(Assessment.user_id == user_id).all()
        test_attempts = self.db.query(TestAttempt).filter(
            TestAttempt.student_id == user_id
        ).all()

        analysis = {
            "user_id": user_id,
            "total_assessments": len(assessments),
            "total_tests_attempted": len(test_attempts),
            "skills_analysis": self._analyze_skills(assessments),
            "test_performance": self._analyze_test_performance(test_attempts),
            "improvement_trends": self._calculate_improvement_trends(assessments, test_attempts),
            "strengths": self._identify_strengths(assessments, test_attempts),
            "weaknesses": self._identify_weaknesses(assessments, test_attempts),
        }

        return analysis

    def _analyze_skills(self, assessments: List[Assessment]) -> Dict:
        """Analyze performance across different skills"""
        if not assessments:
            return {"message": "No assessment data available"}

        avg_data = {
            "math": [],
            "logic": [],
            "aptitude": [],
            "problem_solving": [],
        }

        for a in assessments:
            avg_data["math"].append(a.math_score)
            avg_data["logic"].append(a.logic_score)
            avg_data["aptitude"].append(a.aptitude_score)
            avg_data["problem_solving"].append(a.problem_score)

        skills_analysis = {}
        for skill, scores in avg_data.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                skills_analysis[skill] = {
                    "average_score": round(avg_score, 2),
                    "total_attempts": len(scores),
                    "highest_score": max(scores),
                    "lowest_score": min(scores),
                    "needs_improvement": avg_score < self.skill_thresholds.get(skill, 70),
                }

        return skills_analysis

    def _analyze_test_performance(self, test_attempts: List[TestAttempt]) -> Dict:
        """Analyze performance on teacher-created tests"""
        if not test_attempts:
            return {"message": "No test attempts available"}

        completed = [t for t in test_attempts if str(t.status) in {"submitted", "graded"}]
        if not completed:
            return {"message": "No completed tests"}

        scores = [_to_float(t.percentage) for t in completed if t.percentage is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        pass_count = sum(1 for t in completed if _to_bool(t.is_passed))

        return {
            "total_attempts": len(completed),
            "average_score": round(avg_score, 2),
            "pass_count": pass_count,
            "pass_rate": round((pass_count / len(completed) * 100), 2) if completed else 0,
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0,
        }

    def _calculate_improvement_trends(
        self, assessments: List[Assessment], test_attempts: List[TestAttempt]
    ) -> Dict:
        """Calculate improvement trends over time"""
        # Sort by date
        assessments = sorted(assessments, key=lambda x: x.created_at)
        completed_tests = sorted(
            [t for t in test_attempts if t.status in ["submitted", "graded"]],
            key=lambda x: x.start_time
        )

        trends: Dict[str, object] = {"assessment_trend": [], "test_trend": []}

        # Assessment trend
        if len(assessments) >= 2:
            first_avg = _to_float(assessments[0].overall_score)
            last_avg = _to_float(assessments[-1].overall_score)
            improvement = last_avg - first_avg
            trends["assessment_improvement"] = round(improvement, 2)
            trends["assessment_improvement_percentage"] = round((improvement / first_avg * 100), 2) if first_avg > 0 else 0

        # Test trend
        if len(completed_tests) >= 2:
            first_score = _to_float(completed_tests[0].percentage)
            last_score = _to_float(completed_tests[-1].percentage)
            improvement = last_score - first_score
            trends["test_improvement"] = round(improvement, 2)
            trends["test_improvement_percentage"] = round((improvement / first_score * 100), 2) if first_score > 0 else 0

        return trends

    def _identify_strengths(
        self, assessments: List[Assessment], test_attempts: List[TestAttempt]
    ) -> List[Dict]:
        """Identify student's strong areas"""
        strengths = []
        skills_analysis = self._analyze_skills(assessments)

        threshold = 80
        for skill, data in skills_analysis.items():
            if isinstance(data, dict) and data.get("average_score", 0) >= threshold:
                strengths.append({
                    "skill": skill,
                    "score": data["average_score"],
                    "confidence": min(100, (data["average_score"] - threshold + 20)),
                })

        return sorted(strengths, key=lambda x: x["score"], reverse=True)

    def _identify_weaknesses(
        self, assessments: List[Assessment], test_attempts: List[TestAttempt]
    ) -> List[Dict]:
        """Identify student's areas needing improvement"""
        weaknesses = []
        skills_analysis = self._analyze_skills(assessments)

        threshold = 70
        for skill, data in skills_analysis.items():
            if isinstance(data, dict) and data.get("average_score", 0) < threshold:
                weaknesses.append({
                    "skill": skill,
                    "score": data["average_score"],
                    "gap": threshold - data["average_score"],
                    "priority": "high" if data["average_score"] < 50 else "medium",
                })

        return sorted(weaknesses, key=lambda x: x["gap"], reverse=True)

    def generate_insights(self, user_id: int) -> List[AIInsight]:
        """Generate comprehensive AI insights for a student"""
        analysis = self.analyze_student_performance(user_id)

        if "error" in analysis:
            return []

        insights = []

        # Generate weakness insights
        for weakness in analysis.get("weaknesses", []):
            skill = weakness["skill"]
            gap = weakness["gap"]

            recommendation = self._generate_recommendation_text(skill, weakness["score"])
            action_items = self._generate_action_items(skill)

            # Find relevant learning resources
            resources = self.db.query(LearningResource).filter(
                LearningResource.skill_tag.ilike(f"%{skill}%")
            ).order_by(
                LearningResource.rating.desc()
            ).limit(1).all()

            resource_id = resources[0].id if resources else None

            insight = AIInsight(
                user_id=user_id,
                insight_type="skill_gap",
                skill_name=skill,
                current_score=round(weakness["score"], 2),
                benchmark_score=self.skill_thresholds.get(skill, 70),
                recommendation_text=recommendation,
                confidence_score=0.85,
                action_items=json.dumps(action_items),
                resource_id=resource_id,
                priority_level=weakness["priority"],
            )
            insights.append(insight)

        # Generate strength insights
        for strength in analysis.get("strengths", [])[:2]:  # Top 2 strengths
            skill = strength["skill"]
            recommendation = f"You are performing excellently in {skill}. Keep up the great work! Consider challenging yourself with advanced problems or helping peers."

            insight = AIInsight(
                user_id=user_id,
                insight_type="strength",
                skill_name=skill,
                current_score=round(strength["score"], 2),
                benchmark_score=self.skill_thresholds.get(skill, 70),
                recommendation_text=recommendation,
                confidence_score=0.90,
                action_items=json.dumps(["Practice advanced problems", "Help peers", "Explore related topics"]),
                priority_level="low",
            )
            insights.append(insight)

        # Generate improvement insights from trends
        trends = analysis.get("improvement_trends", {})
        if trends.get("assessment_improvement", 0) > 0:
            recommendation = f"Great progress! Your performance has improved by {trends.get('assessment_improvement_percentage', 0)}%. Maintain this momentum by consistently practicing and focusing on weak areas."
            insight = AIInsight(
                user_id=user_id,
                insight_type="improvement",
                skill_name="Overall Performance",
                recommendation_text=recommendation,
                confidence_score=0.80,
                priority_level="low",
            )
            insights.append(insight)

        return insights

    def _generate_recommendation_text(self, skill: str, current_score: float) -> str:
        """Generate personalized recommendation text"""
        gap = self.skill_thresholds.get(skill, 70) - current_score
        urgency = "immediately" if current_score < 50 else "soon"

        recommendations = {
            "math": f"Your Data Structures and Algorithms base score ({current_score}) is below benchmark. Practice arrays, strings, trees, and dynamic programming for {max(20, int(gap / 2))} minutes daily.",
            "logic": f"Your algorithmic reasoning score ({current_score}) needs improvement. Solve pattern-based coding problems and explain your logic before writing code.",
            "aptitude": f"Your CS fundamentals score ({current_score}) can improve. Revise DBMS, OS, and Computer Networks with timed topic quizzes.",
            "problem_solving": f"Your debugging and problem-solving score ({current_score}) is low. Use step-by-step dry runs, edge-case testing, and post-mortems for mistakes.",
            "reasoning": f"Strengthen your reasoning ability ({current_score}) with weekly mock tests and mixed difficulty question sets.",
        }

        return recommendations.get(
            skill,
            f"Your {skill.title()} performance ({current_score}) is below our benchmark of {self.skill_thresholds.get(skill, 70)}. Please focus on this area {urgency}."
        )

    def _generate_action_items(self, skill: str) -> List[str]:
        """Generate actionable steps for improvement"""
        action_templates = {
            "math": [
                "Review fundamental concepts for 30 minutes daily",
                "Solve 5-10 practice problems daily",
                "Watch video tutorials on weak topics",
                "Take a full practice test weekly",
            ],
            "logic": [
                "Practice logic puzzles for 20 minutes daily",
                "Study logical operators and truth tables",
                "Analyze reasoning patterns in questions",
                "Join study group sessions on logic",
            ],
            "aptitude": [
                "Take timed practice tests regularly",
                "Focus on time management techniques",
                "Learn shortcuts and tricks",
                "Analyze previous attempts to identify patterns",
            ],
            "problem_solving": [
                "Solve problems step by step, don't rush",
                "Study different problem-solving strategies",
                "Practice with increasing difficulty levels",
                "Review solutions of similar problems",
            ],
        }

        return action_templates.get(skill, [
            f"Focus on {skill} daily for 20-30 minutes",
            "Take multiple practice tests",
            "Review weak areas systematically",
            "Seek help from instructors or peers",
        ])

    def get_recommended_resources(self, user_id: int, skill: Optional[str] = None, limit: int = 5) -> List[LearningResource]:
        """Get recommended learning resources for a student"""
        query = self.db.query(LearningResource).filter(
            LearningResource.is_verified == True
        )

        if skill:
            query = query.filter(LearningResource.skill_tag.ilike(f"%{skill}%"))

        resources = query.order_by(
            LearningResource.rating.desc(),
            LearningResource.views.desc()
        ).limit(limit).all()

        return resources

    def update_performance_metrics(self, user_id: int, test_id: Optional[int] = None) -> None:
        """Update performance metrics after each test/assessment"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or str(user.role) != "user":
            return

        # Overall performance metric
        assessments = self.db.query(Assessment).filter(Assessment.user_id == user_id).all()
        if assessments:
            assessment_scores = [_to_float(a.overall_score) for a in assessments]
            avg_score = sum(assessment_scores) / len(assessment_scores)
            highest_score = max(assessment_scores)
            successful_attempts = sum(1 for score in assessment_scores if score >= 70)
            
            metric = self.db.query(PerformanceMetric).filter(
                PerformanceMetric.user_id == user_id,
                PerformanceMetric.metric_type == "overall",
                PerformanceMetric.category == "Overall"
            ).first()
            
            if metric:
                setattr(metric, "total_attempts", len(assessments))
                setattr(metric, "average_score", avg_score)
                setattr(metric, "highest_score", highest_score)
                setattr(metric, "last_attempt_date", datetime.utcnow())
            else:
                metric = PerformanceMetric(
                    user_id=user_id,
                    metric_type="overall",
                    category="Overall",
                    total_attempts=len(assessments),
                    average_score=avg_score,
                    highest_score=highest_score,
                    successful_attempts=successful_attempts,
                    last_attempt_date=datetime.utcnow(),
                )
                self.db.add(metric)

        # Test-wise performance metrics
        if test_id:
            test_attempts = self.db.query(TestAttempt).filter(
                TestAttempt.student_id == user_id,
                TestAttempt.test_id == test_id
            ).all()
            
            if test_attempts:
                test = self.db.query(Test).filter(Test.id == test_id).first()
                completed = [t for t in test_attempts if t.percentage is not None]
                
                if completed:
                    completed_scores = [_to_float(t.percentage) for t in completed]
                    avg_score = sum(completed_scores) / len(completed_scores)
                    passed = sum(1 for t in completed if _to_bool(t.is_passed))
                    highest_score = max(completed_scores)
                    
                    metric = self.db.query(PerformanceMetric).filter(
                        PerformanceMetric.user_id == user_id,
                        PerformanceMetric.test_id == test_id
                    ).first()
                    
                    if metric:
                        setattr(metric, "total_attempts", len(test_attempts))
                        setattr(metric, "average_score", avg_score)
                        setattr(metric, "successful_attempts", passed)
                        setattr(metric, "last_attempt_date", datetime.utcnow())
                    else:
                        metric = PerformanceMetric(
                            user_id=user_id,
                            test_id=test_id,
                            metric_type="test",
                            category=test.title if test else f"Test {test_id}",
                            total_attempts=len(test_attempts),
                            average_score=avg_score,
                            successful_attempts=passed,
                            highest_score=highest_score,
                            last_attempt_date=datetime.utcnow(),
                        )
                        self.db.add(metric)

        self.db.commit()
