# ats_engine.py
import re

class ATSEngine:
    """ATS 评分引擎"""
    
    def __init__(self):
        self.weights = {
            "formatting": 20,
            "keywords": 35,
            "experience": 25,
            "education": 10,
            "contact": 10
        }
    
    def analyze(self, resume_text, jd_text):
        """分析简历的 ATS 兼容性"""
        # 基础实现，返回占位结果
        return {
            "ats_score": 0,
            "breakdown": {
                "formatting": {"score": 0, "issues": []},
                "keywords": {"score": 0, "issues": []},
                "experience": {"score": 0, "issues": []},
                "education": {"score": 0, "issues": []},
                "contact": {"score": 0, "issues": []}
            },
            "improvements": [],
            "ats_type": None
        }

    def check_formatting(self, resume_text):
        """检查简历格式兼容性"""
        score = 100
        issues = []

        # 检查标准章节标题
        standard_headers = ["experience", "education", "skills", "summary", "objective"]
        found_headers = [h for h in standard_headers if h in resume_text.lower()]
        if len(found_headers) < 2:
            score -= 15
            issues.append("缺少标准章节标题（Experience, Education, Skills）")

        # 检查联系方式格式
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if not re.search(email_pattern, resume_text):
            score -= 10
            issues.append("缺少有效的电子邮件地址")

        phone_pattern = r'(\+?1?[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        if not re.search(phone_pattern, resume_text):
            score -= 10
            issues.append("缺少有效的电话号码")

        # 检查是否使用表格格式（制表符）
        if '\t' in resume_text:
            score -= 5
            issues.append("使用了制表符，可能影响 ATS 解析")

        # 检查关键词密度（简单估算）
        words = resume_text.split()
        if len(words) < 20:
            score -= 10
            issues.append("简历内容过短，建议至少 20 词")
        elif len(words) > 1000:
            score -= 5
            issues.append("简历内容过长，建议控制在 1000 词以内")

        return {"score": max(0, score), "issues": issues}

    def check_keywords(self, resume_text, jd_text):
        """检查关键词匹配度"""
        jd_keywords = self._extract_keywords(jd_text)
        resume_lower = resume_text.lower()

        matched = []
        missing = []

        for keyword in jd_keywords:
            if keyword.lower() in resume_lower:
                matched.append(keyword)
            else:
                missing.append(keyword)

        if len(jd_keywords) == 0:
            score = 70
        else:
            match_rate = len(matched) / len(jd_keywords)
            score = min(100, int(match_rate * 100))

        bonus = self._calculate_position_bonus(matched, resume_text)
        score = min(100, score + bonus)

        return {
            "score": score,
            "matched": matched,
            "missing": missing
        }

    def _extract_keywords(self, text):
        """从文本中提取关键词"""
        tech_keywords = [
            "python", "java", "javascript", "typescript", "react", "vue", "angular",
            "node.js", "django", "flask", "spring", "postgresql", "mysql", "mongodb",
            "redis", "docker", "kubernetes", "aws", "azure", "gcp", "ci/cd",
            "git", "github", "gitlab", "rest api", "graphql", "microservices",
            "agile", "scrum", "tdd", "linux", "nginx", "apache"
        ]

        soft_keywords = [
            "communication", "teamwork", "leadership", "problem solving",
            "analytical", "creative", "organized", "detail-oriented"
        ]

        all_keywords = tech_keywords + soft_keywords
        text_lower = text.lower()

        found = [kw for kw in all_keywords if kw in text_lower]

        words = text.split()
        for word in words:
            if word.isupper() and len(word) > 2 and word.lower() not in found:
                found.append(word)

        return found

    def _calculate_position_bonus(self, matched_keywords, resume_text):
        """根据关键词位置计算加分"""
        bonus = 0
        resume_lower = resume_text.lower()

        if "skills" in resume_lower:
            skills_section = resume_lower.split("skills")[1][:500]
            for kw in matched_keywords:
                if kw.lower() in skills_section:
                    bonus += 1

        return min(10, bonus)
