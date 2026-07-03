# ats_engine.py
import re
from difflib import SequenceMatcher
from services.constants import (
    EMAIL_PATTERN, PHONE_PATTERN, STANDARD_HEADERS, TECH_KEYWORDS,
    SOFT_KEYWORDS, STRONG_VERBS, WEAK_VERBS, DEGREE_KEYWORDS,
    SCHOOL_KEYWORDS, LOCATIONS, SEMANTIC_GROUPS, XYZ_PATTERNS,
    PORTFOLIO_PATTERNS, PORTFOLIO_KEYWORDS
)

class ATSEngine:
    """ATS 评分引擎"""

    def __init__(self):
        self.ats_patterns = {
            "workday": {
                "patterns": ["workday", "myworkdayjobs", "wd5.myworkday", "wday.com"],
                "tips": [
                    "Workday 系统重视关键词精确匹配",
                    "确保技能名称与 JD 完全一致",
                    "使用标准的章节标题"
                ]
            },
            "lever": {
                "patterns": ["lever.co", "jobs.lever", "lever.co/"],
                "tips": [
                    "Lever 系统重视格式简洁",
                    "避免使用表格和复杂格式",
                    "保持简历简洁明了"
                ]
            },
            "greenhouse": {
                "patterns": ["greenhouse.io", "boards.greenhouse", "greenhouse.com"],
                "tips": [
                    "Greenhouse 重视技能标签",
                    "在技能列表中明确列出技术栈",
                    "使用标准的职位名称"
                ]
            },
            "icims": {
                "patterns": ["icims.com", "jobs.icims", "icims.com/"],
                "tips": [
                    "iCIMS 系统解析能力较强",
                    "保持标准格式即可",
                    "确保关键词自然分布"
                ]
            },
            "taleo": {
                "patterns": ["taleo", "oracle.com/taleo", "talent.oracle"],
                "tips": [
                    "Taleo 系统较为严格",
                    "避免使用特殊字符",
                    "使用标准的章节标题"
                ]
            },
            "smartrecruiters": {
                "patterns": ["smartrecruiters", "smartrecruiters.com"],
                "tips": [
                    "SmartRecruiters 重视关键词匹配",
                    "确保技能与 JD 匹配",
                    "保持格式简洁"
                ]
            },
            "bamboohr": {
                "patterns": ["bamboohr.com", "bamboo hr", "bamboohr"],
                "tips": [
                    "BambooHR 系统界面友好",
                    "保持格式简洁清晰",
                    "确保联系方式完整"
                ]
            },
            "successfactors": {
                "patterns": ["successfactors", "sap.com/careers", "sapsf"],
                "tips": [
                    "SuccessFactors 重视结构化数据",
                    "使用标准的职位名称和技能术语",
                    "确保日期格式一致"
                ]
            },
            "jobvite": {
                "patterns": ["jobvite.com", "jobvite"],
                "tips": [
                    "JobVite 重视社交招聘",
                    "确保 LinkedIn 链接可访问",
                    "使用行业标准关键词"
                ]
            },
            "applicantstack": {
                "patterns": ["applicantstack.com", "applicantstack"],
                "tips": [
                    "ApplicantStack 重视关键词匹配",
                    "确保技能与职位要求一致",
                    "使用标准格式"
                ]
            },
            "bullhorn": {
                "patterns": ["bullhorn.com", "bullhorn"],
                "tips": [
                    "Bullhorn 用于招聘机构",
                    "确保简历格式标准化",
                    "关键词要与职位描述匹配"
                ]
            },
            "clearcompany": {
                "patterns": ["clearcompany.com", "clearcompany"],
                "tips": [
                    "ClearCompany 重视人才匹配",
                    "突出与职位相关的成就",
                    "使用量化数据"
                ]
            }
        }
        self.weights = {
            "formatting": 20,
            "keywords": 35,
            "experience": 25,
            "education": 10,
            "contact": 10
        }
    
    def analyze(self, resume_text, jd_text):
        """分析简历的 ATS 兼容性"""
        # 执行所有检查
        formatting = self.check_formatting(resume_text)
        keywords = self.check_keywords(resume_text, jd_text)
        semantic = self.check_semantic_match(resume_text, jd_text)
        experience = self.check_experience(resume_text)
        education = self.check_education(resume_text)
        contact = self.check_contact(resume_text)
        portfolio = self.check_portfolio(resume_text)
        ats_type = self.identify_ats(jd_text)

        # 合并关键词和语义匹配分数
        combined_keyword_score = int((keywords["score"] * 0.6 + semantic["score"] * 0.4))

        # 计算加权总分
        total_score = (
            formatting["score"] * self.weights["formatting"] / 100 +
            combined_keyword_score * self.weights["keywords"] / 100 +
            experience["score"] * self.weights["experience"] / 100 +
            education["score"] * self.weights["education"] / 100 +
            contact["score"] * self.weights["contact"] / 100 +
            portfolio["score"] * 5  # 作品集加分（最多5分）
        )

        # 生成改进建议
        improvements = self._generate_improvements(
            formatting, keywords, semantic, experience, education, contact, portfolio, ats_type
        )

        return {
            "ats_score": min(100, round(total_score)),
            "breakdown": {
                "formatting": formatting,
                "keywords": keywords,
                "semantic_match": semantic,
                "experience": experience,
                "education": education,
                "contact": contact,
                "portfolio": portfolio
            },
            "improvements": improvements,
            "ats_type": ats_type
        }

    def _generate_improvements(self, formatting, keywords, semantic, experience, education, contact, portfolio, ats_type):
        """生成改进建议"""
        improvements = []

        # 按优先级添加建议
        if keywords["missing"]:
            improvements.append(f"添加缺失的关键词: {', '.join(keywords['missing'][:5])}")

        if semantic.get("related_missing"):
            groups = list(semantic["related_missing"].keys())[:3]
            improvements.append(f"考虑补充相关技能组: {', '.join(groups)}")

        if formatting["issues"]:
            improvements.extend(formatting["issues"][:2])

        if experience["issues"]:
            improvements.extend(experience["issues"][:2])

        if education["issues"]:
            improvements.extend(education["issues"][:1])

        if contact["issues"]:
            improvements.extend(contact["issues"][:1])

        if portfolio["issues"]:
            improvements.extend(portfolio["issues"][:1])

        # 添加 ATS 特定建议
        if ats_type["type"] != "unknown" and ats_type["tips"]:
            improvements.append(f"针对 {ats_type['type']} 系统: {ats_type['tips'][0]}")

        return improvements[:8]  # 最多返回 8 条建议

    def check_formatting(self, resume_text):
        """检查简历格式兼容性"""
        score = 100
        issues = []

        # 检查标准章节标题
        found_headers = [h for h in STANDARD_HEADERS if h in resume_text.lower()]
        if len(found_headers) < 2:
            score -= 15
            issues.append("缺少标准章节标题（Experience, Education, Skills）")

        # 检查联系方式格式
        if not re.search(EMAIL_PATTERN, resume_text):
            score -= 10
            issues.append("缺少有效的电子邮件地址")

        if not re.search(PHONE_PATTERN, resume_text):
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
        all_keywords = TECH_KEYWORDS + SOFT_KEYWORDS
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

    def check_semantic_match(self, resume_text, jd_text):
        """语义匹配检查 - 使用相似度算法和技能组匹配"""
        resume_lower = resume_text.lower()
        jd_lower = jd_text.lower()

        # 1. 文本相似度
        similarity = SequenceMatcher(None, resume_lower, jd_lower).ratio()
        text_score = min(100, int(similarity * 100 * 2))  # 归一化到0-100

        # 2. 技能组匹配
        matched_groups = []
        related_missing = {}

        for group_name, keywords in SEMANTIC_GROUPS.items():
            jd_has = [kw for kw in keywords if kw in jd_lower]
            resume_has = [kw for kw in keywords if kw in resume_lower]

            if jd_has:
                overlap = len(set(jd_has) & set(resume_has))
                coverage = overlap / len(jd_has) if jd_has else 0

                if coverage > 0.5:
                    matched_groups.append(group_name)
                elif coverage > 0:
                    matched_groups.append(f"{group_name} (部分)")
                else:
                    related_missing[group_name] = jd_has

        # 3. 计算语义分数
        group_score = min(100, int(len(matched_groups) / max(1, len(related_missing) + len(matched_groups)) * 100))

        # 综合分数
        semantic_score = min(100, int(text_score * 0.4 + group_score * 0.6))

        return {
            "score": semantic_score,
            "text_similarity": round(similarity * 100, 1),
            "matched_groups": matched_groups,
            "related_missing": related_missing
        }

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

        # 检查量化数据（X-Y-Z格式）
        quantified = 0
        xyz_formatted = 0
        for bullet in bullets:
            if re.search(r'\d+%|\$[\d,]+|\d+ (users|customers|projects|team)', bullet, re.IGNORECASE):
                quantified += 1
            for pattern in XYZ_PATTERNS:
                if re.search(pattern, bullet, re.IGNORECASE):
                    xyz_formatted += 1
                    break

        if len(bullets) > 0:
            quantified_rate = quantified / len(bullets)
            if quantified_rate < 0.3:
                score -= 20
                issues.append("缺少量化数据，建议使用 X-Y-Z 格式：做了什么(X) + 怎么做(Y) + 结果(Z)")

            # X-Y-Z 格式加分
            if xyz_formatted / len(bullets) > 0.5:
                score = min(100, score + 5)  # 鼓励 X-Y-Z 格式

        # 检查动词强度
        strong_count = 0
        weak_count = 0
        for bullet in bullets:
            bullet_lower = bullet.lower()
            for verb in STRONG_VERBS:
                if bullet_lower.startswith(verb):
                    strong_count += 1
                    break
            for verb in WEAK_VERBS:
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

        return {"score": max(0, score), "issues": issues, "xyz_count": xyz_formatted}

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
        has_degree = any(d in resume_lower for d in DEGREE_KEYWORDS)
        if not has_degree:
            score -= 30
            issues.append("未找到学位信息")

        # 检查学校
        if not any(school in resume_lower for school in SCHOOL_KEYWORDS):
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
        if re.search(EMAIL_PATTERN, resume_text):
            score += 25
        else:
            issues.append("缺少有效的电子邮件地址")

        # 电话 (25分)
        if re.search(PHONE_PATTERN, resume_text):
            score += 25
        else:
            issues.append("缺少有效的电话号码")

        # LinkedIn (25分)
        if "linkedin" in resume_text.lower():
            score += 25
        else:
            issues.append("建议添加 LinkedIn 个人主页链接")

        # 地点 (25分)
        if any(loc in resume_text.lower() for loc in LOCATIONS):
            score += 25
        else:
            issues.append("建议添加所在城市")

        return {"score": score, "issues": issues}

    def identify_ats(self, jd_text):
        """从 JD 识别 ATS 类型"""
        jd_lower = jd_text.lower()

        for ats_name, config in self.ats_patterns.items():
            for pattern in config["patterns"]:
                if pattern in jd_lower:
                    return {
                        "type": ats_name,
                        "confidence": 0.85,
                        "tips": config["tips"]
                    }

        return {
            "type": "unknown",
            "confidence": 0,
            "tips": [
                "无法识别具体 ATS 系统",
                "建议使用标准格式和关键词",
                "保持简历简洁明了"
            ]
        }

    def check_portfolio(self, resume_text):
        """检查作品集和在线链接"""
        score = 0
        issues = []
        found_links = []

        # 检查常见的作品集链接
        for pattern in PORTFOLIO_PATTERNS:
            matches = re.findall(pattern, resume_text, re.IGNORECASE)
            found_links.extend(matches)

        # 检查作品集关键词
        has_portfolio_keyword = any(kw in resume_text.lower() for kw in PORTFOLIO_KEYWORDS)

        if found_links:
            score = min(25, len(found_links) * 10)
        elif has_portfolio_keyword:
            score = 15
        else:
            issues.append("建议添加作品集链接（GitHub、个人网站等）")

        # 检查 LinkedIn
        if "linkedin.com/in/" in resume_text.lower():
            score = min(50, score + 25)

        return {"score": score, "issues": issues, "links": found_links}
