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

    def check_experience(self, resume_text):
        """检查工作经验质量"""
        score = 100
        issues = []

        bullets = self._extract_bullets(resume_text)

        if len(bullets) == 0:
            return {"score": 30, "issues": ["未找到工作经历描述"]}

        # 检查 bullet point 数量
        if len(bullets) < 3:
            score -= 15
            issues.append("工作经历描述过少，建议每个职位 3-5 个 bullet points")

        # 检查量化数据
        quantified = 0
        for bullet in bullets:
            if re.search(r'\d+%|\$[\d,]+|\d+ (users|customers|projects|team)', bullet, re.IGNORECASE):
                quantified += 1

        if len(bullets) > 0:
            quantified_rate = quantified / len(bullets)
            if quantified_rate < 0.3:
                score -= 20
                issues.append("缺少量化数据，建议添加具体数字（百分比、金额、用户数）")

        # 检查动词强度
        strong_verbs = ["led", "built", "increased", "reduced", "delivered", "launched",
                       "managed", "developed", "implemented", "optimized", "designed"]
        weak_verbs = ["helped", "assisted", "was responsible", "did", "worked on"]

        strong_count = 0
        weak_count = 0
        for bullet in bullets:
            bullet_lower = bullet.lower()
            for verb in strong_verbs:
                if bullet_lower.startswith(verb):
                    strong_count += 1
                    break
            for verb in weak_verbs:
                if verb in bullet_lower:
                    weak_count += 1
                    break

        if weak_count > strong_count:
            score -= 15
            issues.append("使用了较弱的动词，建议使用更强的行动动词（Led, Built, Increased）")

        # 检查长度
        avg_length = sum(len(b.split()) for b in bullets) / len(bullets) if bullets else 0
        if avg_length < 6:
            score -= 10
            issues.append("Bullet points 过短，建议每个 10-20 词")
        elif avg_length > 30:
            score -= 5
            issues.append("Bullet points 过长，建议控制在 20 词以内")

        return {"score": max(0, score), "issues": issues}

    def _extract_bullets(self, text):
        """提取 bullet points"""
        bullets = []
        lines = text.split('\n')
        in_experience = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测经验章节开始
            if 'experience' in line.lower() or 'work history' in line.lower():
                in_experience = True
                continue

            # 检测其他章节开始
            if line.isupper() and len(line) > 3:
                in_experience = False
                continue

            # 提取 bullet points
            if in_experience and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                bullet = line.lstrip('-•* ').strip()
                if len(bullet) > 10:
                    bullets.append(bullet)

        return bullets

    def check_education(self, resume_text):
        """检查教育背景"""
        score = 100
        issues = []

        resume_lower = resume_text.lower()

        # 检查是否有教育章节
        if "education" not in resume_lower:
            return {"score": 50, "issues": ["缺少教育背景章节"]}

        # 检查学位
        degrees = ["bs", "ba", "b.s", "b.a", "ms", "ma", "m.s", "m.a", "mba", "phd", "bachelor", "master"]
        has_degree = any(d in resume_lower for d in degrees)
        if not has_degree:
            score -= 30
            issues.append("未找到学位信息")

        # 检查学校
        if "university" not in resume_lower and "college" not in resume_lower and "institute" not in resume_lower:
            score -= 20
            issues.append("未找到学校名称")

        # 检查年份
        if not re.search(r'20\d{2}', resume_text):
            score -= 10
            issues.append("未找到毕业年份")

        return {"score": max(0, score), "issues": issues}

    def check_contact(self, resume_text):
        """检查联系方式"""
        score = 0
        issues = []

        # 电子邮件 (25分)
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if re.search(email_pattern, resume_text):
            score += 25
        else:
            issues.append("缺少有效的电子邮件地址")

        # 电话 (25分)
        phone_pattern = r'(\+?1?[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        if re.search(phone_pattern, resume_text):
            score += 25
        else:
            issues.append("缺少有效的电话号码")

        # LinkedIn (25分)
        if "linkedin" in resume_text.lower():
            score += 25
        else:
            issues.append("建议添加 LinkedIn 个人主页链接")

        # 地点 (25分)
        locations = ["san francisco", "new york", "seattle", "austin", "boston", "chicago",
                     "los angeles", "denver", "atlanta", "miami", "remote"]
        if any(loc in resume_text.lower() for loc in locations):
            score += 25
        else:
            issues.append("建议添加所在城市")

        return {"score": score, "issues": issues}
