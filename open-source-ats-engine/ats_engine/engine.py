"""
ATS Engine - Open Source Resume Analyzer

A Python library for analyzing resumes against ATS (Applicant Tracking Systems).
Supports 12+ ATS types including Workday, Taleo, Greenhouse, Lever, and more.

Usage:
    from ats_engine import ATSEngine
    
    engine = ATSEngine()
    result = engine.analyze(resume_text, job_description)
    print(f"ATS Score: {result['ats_score']}/100")
"""

import re
from difflib import SequenceMatcher

# ==================== Constants ====================

# Regex patterns for validation
EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
PHONE_PATTERN = r'(\+?1?[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'

# Standard resume section headers
STANDARD_HEADERS = ["experience", "education", "skills", "summary", "objective"]

# Tech keywords for matching (lowercase for case-insensitive comparison)
TECH_KEYWORDS = [
    "python", "java", "javascript", "typescript", "react", "vue", "angular",
    "node.js", "django", "flask", "spring", "spring boot", "express",
    "postgresql", "mysql", "mongodb", "redis", "sqlite",
    "docker", "kubernetes", "aws", "azure", "gcp", "ci/cd",
    "git", "github", "gitlab", "rest api", "graphql", "microservices",
    "agile", "scrum", "tdd", "linux", "nginx", "apache"
]

# Soft skills keywords
SOFT_KEYWORDS = [
    "communication", "teamwork", "leadership", "problem solving",
    "analytical", "creative", "organized", "detail-oriented"
]

# Strong action verbs for experience evaluation
STRONG_VERBS = [
    "led", "built", "increased", "reduced", "delivered", "launched",
    "managed", "developed", "implemented", "optimized", "designed"
]

# Weak verbs to avoid
WEAK_VERBS = ["helped", "assisted", "was responsible", "did", "worked on"]

# Common degree abbreviations
DEGREE_KEYWORDS = [
    "bs", "ba", "b.s", "b.a", "ms", "ma", "m.s", "m.a", "mba", "phd",
    "bachelor", "master"
]

# School/institution keywords
SCHOOL_KEYWORDS = ["university", "college", "institute"]

# Location keywords for contact check
LOCATIONS = [
    "san francisco", "new york", "seattle", "austin", "boston", "chicago",
    "los angeles", "denver", "atlanta", "miami", "remote"
]

# Semantic keyword groups - related terms that ATS systems understand
SEMANTIC_GROUPS = {
    "frontend": ["react", "vue", "angular", "html", "css", "javascript", "typescript", "svelte", "next.js", "nuxt"],
    "backend": ["python", "java", "node.js", "django", "flask", "spring", "express", "ruby", "go", "rust"],
    "database": ["postgresql", "mysql", "mongodb", "redis", "sqlite", "elasticsearch", "dynamodb", "cassandra"],
    "cloud": ["aws", "azure", "gcp", "google cloud", "heroku", "vercel", "netlify"],
    "devops": ["docker", "kubernetes", "ci/cd", "jenkins", "terraform", "ansible", "github actions"],
    "data": ["sql", "pandas", "numpy", "spark", "hadoop", "tableau", "power bi", "machine learning", "ai"],
    "mobile": ["ios", "android", "react native", "flutter", "swift", "kotlin"],
    "security": ["oauth", "jwt", "encryption", "firewall", "penetration testing", "owasp"],
    "methodology": ["agile", "scrum", "kanban", "tdd", "bdd", "pair programming", "code review"],
}

# X-Y-Z format patterns for quantified achievements
XYZ_PATTERNS = [
    r'(?:led|built|developed|implemented|designed|created|launched|managed|optimized|reduced|increased|improved|delivered)\s+.+?(?:resulting in|leading to|which achieved|with|for)\s+\d+',
    r'(?:increased|improved|reduced|decreased|boosted|enhanced)\s+.+?\d+%',
    r'(?:saved|generated|reduced|increased)\s+.+?\$[\d,]+',
    r'(?:serving|supporting|managing|handling)\s+\d+[\s+]?(?:users|customers|clients|requests|transactions)',
]

# Portfolio link patterns
PORTFOLIO_PATTERNS = [
    r'github\.com/[\w-]+',
    r'linkedin\.com/in/[\w-]+',
    r'behance\.net/[\w-]+',
    r'dribbble\.com/[\w-]+',
    r'portfolio\.\w+',
    r'[\w-]+\.dev',
    r'[\w-]+\.io',
]

# Portfolio/online presence keywords
PORTFOLIO_KEYWORDS = [
    "portfolio", "github", "behance", "dribbble", "personal website",
    "personal site", "online portfolio", "work samples", "projects"
]


# ==================== ATSEngine Class ====================

class ATSEngine:
    """ATS Resume Analysis Engine"""
    
    def __init__(self):
        self.ats_patterns = {
            "workday": {
                "patterns": ["workday", "myworkdayjobs", "wd5.myworkday", "wday.com"],
                "tips": [
                    "Workday systems prioritize exact keyword matching",
                    "Ensure skill names match the job description exactly",
                    "Use standard section headers"
                ]
            },
            "lever": {
                "patterns": ["lever.co", "jobs.lever", "lever.co/"],
                "tips": [
                    "Lever systems prefer clean formatting",
                    "Avoid tables and complex layouts",
                    "Keep resume concise and clear"
                ]
            },
            "greenhouse": {
                "patterns": ["greenhouse.io", "boards.greenhouse", "greenhouse.com"],
                "tips": [
                    "Greenhouse values skill tags",
                    "List your tech stack clearly in skills section",
                    "Use standard job titles"
                ]
            },
            "icims": {
                "patterns": ["icims.com", "jobs.icims", "icims.com/"],
                "tips": [
                    "iCIMS has strong parsing capabilities",
                    "Standard formatting works well",
                    "Ensure natural keyword distribution"
                ]
            },
            "taleo": {
                "patterns": ["taleo", "oracle.com/taleo", "talent.oracle"],
                "tips": [
                    "Taleo systems are quite strict",
                    "Avoid special characters",
                    "Use standard section headers"
                ]
            },
            "smartrecruiters": {
                "patterns": ["smartrecruiters", "smartrecruiters.com"],
                "tips": [
                    "SmartRecruiters values keyword matching",
                    "Ensure skills match the job description",
                    "Keep formatting simple"
                ]
            },
            "bamboohr": {
                "patterns": ["bamboohr.com", "bamboo hr", "bamboohr"],
                "tips": [
                    "BambooHR has a user-friendly interface",
                    "Keep formatting clean and simple",
                    "Ensure contact information is complete"
                ]
            },
            "successfactors": {
                "patterns": ["successfactors", "sap.com/careers", "sapsf"],
                "tips": [
                    "SuccessFactors values structured data",
                    "Use standard job titles and skill terminology",
                    "Ensure consistent date formatting"
                ]
            },
            "jobvite": {
                "patterns": ["jobvite.com", "jobvite"],
                "tips": [
                    "JobVite focuses on social recruiting",
                    "Ensure LinkedIn link is accessible",
                    "Use industry-standard keywords"
                ]
            },
            "applicantstack": {
                "patterns": ["applicantstack.com", "applicantstack"],
                "tips": [
                    "ApplicantStack values keyword matching",
                    "Ensure skills align with job requirements",
                    "Use standard formatting"
                ]
            },
            "bullhorn": {
                "patterns": ["bullhorn.com", "bullhorn"],
                "tips": [
                    "Bullhorn is used by recruiting agencies",
                    "Ensure resume format is standardized",
                    "Keywords should match job descriptions"
                ]
            },
            "clearcompany": {
                "patterns": ["clearcompany.com", "clearcompany"],
                "tips": [
                    "ClearCompany values talent matching",
                    "Highlight achievements relevant to the role",
                    "Use quantified results"
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
        """Analyze resume for ATS compatibility"""
        # Run all checks
        formatting = self.check_formatting(resume_text)
        keywords = self.check_keywords(resume_text, jd_text)
        semantic = self.check_semantic_match(resume_text, jd_text)
        experience = self.check_experience(resume_text)
        education = self.check_education(resume_text)
        contact = self.check_contact(resume_text)
        portfolio = self.check_portfolio(resume_text)
        ats_type = self.identify_ats(jd_text)

        # Combine keyword and semantic scores
        combined_keyword_score = int((keywords["score"] * 0.6 + semantic["score"] * 0.4))

        # Calculate weighted total score
        total_score = (
            formatting["score"] * self.weights["formatting"] / 100 +
            combined_keyword_score * self.weights["keywords"] / 100 +
            experience["score"] * self.weights["experience"] / 100 +
            education["score"] * self.weights["education"] / 100 +
            contact["score"] * self.weights["contact"] / 100 +
            portfolio["score"] * 5  # Portfolio bonus (max 5 points)
        )

        # Generate improvement suggestions
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
        """Generate improvement suggestions"""
        improvements = []

        # Add suggestions by priority
        if keywords["missing"]:
            improvements.append(f"Add missing keywords: {', '.join(keywords['missing'][:5])}")

        if semantic.get("related_missing"):
            groups = list(semantic["related_missing"].keys())[:3]
            improvements.append(f"Consider adding skill groups: {', '.join(groups)}")

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

        # Add ATS-specific suggestions
        if ats_type["type"] != "unknown" and ats_type["tips"]:
            improvements.append(f"For {ats_type['type']} system: {ats_type['tips'][0]}")

        return improvements[:8]  # Return max 8 suggestions

    def check_formatting(self, resume_text):
        """Check resume formatting compatibility"""
        score = 100
        issues = []

        # Check standard section headers
        found_headers = [h for h in STANDARD_HEADERS if h in resume_text.lower()]
        if len(found_headers) < 2:
            score -= 15
            issues.append("Missing standard section headers (Experience, Education, Skills)")

        # Check contact information format
        if not re.search(EMAIL_PATTERN, resume_text):
            score -= 10
            issues.append("Missing valid email address")

        if not re.search(PHONE_PATTERN, resume_text):
            score -= 10
            issues.append("Missing valid phone number")

        # Check for table formatting (tabs)
        if '\t' in resume_text:
            score -= 5
            issues.append("Using tabs may affect ATS parsing")

        # Check content length
        words = resume_text.split()
        if len(words) < 20:
            score -= 10
            issues.append("Resume content too short,建议 at least 20 words")
        elif len(words) > 1000:
            score -= 5
            issues.append("Resume content too long,建议 keep under 1000 words")

        return {"score": max(0, score), "issues": issues}

    def check_keywords(self, resume_text, jd_text):
        """Check keyword matching"""
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
        """Extract keywords from text"""
        all_keywords = TECH_KEYWORDS + SOFT_KEYWORDS
        text_lower = text.lower()

        found = [kw for kw in all_keywords if kw in text_lower]

        words = text.split()
        for word in words:
            if word.isupper() and len(word) > 2 and word.lower() not in found:
                found.append(word)

        return found

    def _calculate_position_bonus(self, matched_keywords, resume_text):
        """Calculate bonus based on keyword position"""
        bonus = 0
        resume_lower = resume_text.lower()

        if "skills" in resume_lower:
            skills_section = resume_lower.split("skills")[1][:500]
            for kw in matched_keywords:
                if kw.lower() in skills_section:
                    bonus += 1

        return min(10, bonus)

    def check_semantic_match(self, resume_text, jd_text):
        """Semantic matching check using similarity algorithm"""
        resume_lower = resume_text.lower()
        jd_lower = jd_text.lower()

        # 1. Text similarity
        similarity = SequenceMatcher(None, resume_lower, jd_lower).ratio()
        text_score = min(100, int(similarity * 100 * 2))

        # 2. Skill group matching
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
                    matched_groups.append(f"{group_name} (partial)")
                else:
                    related_missing[group_name] = jd_has

        # 3. Calculate semantic score
        group_score = min(100, int(len(matched_groups) / max(1, len(related_missing) + len(matched_groups)) * 100))

        # Combined score
        semantic_score = min(100, int(text_score * 0.4 + group_score * 0.6))

        return {
            "score": semantic_score,
            "text_similarity": round(similarity * 100, 1),
            "matched_groups": matched_groups,
            "related_missing": related_missing
        }

    def check_experience(self, resume_text):
        """Check work experience quality"""
        score = 100
        issues = []

        bullets = self._extract_bullets(resume_text)

        if len(bullets) == 0:
            return {"score": 30, "issues": ["No work experience found"]}

        # Check bullet point count
        if len(bullets) < 3:
            score -= 15
            issues.append("Too few bullet points,建议 3-5 per job")

        # Check quantified data (X-Y-Z format)
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
                issues.append("Missing quantified data, use X-Y-Z format: What(X) + How(Y) + Result(Z)")

            # X-Y-Z format bonus
            if xyz_formatted / len(bullets) > 0.5:
                score = min(100, score + 5)

        # Check verb strength
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
            issues.append("Using weak verbs, use stronger action verbs (Led, Built, Increased)")

        # Check length
        avg_length = sum(len(b.split()) for b in bullets) / len(bullets) if bullets else 0
        if avg_length < 6:
            score -= 10
            issues.append("Bullet points too short, aim for 10-20 words each")
        elif avg_length > 30:
            score -= 5
            issues.append("Bullet points too long, keep under 20 words")

        return {"score": max(0, score), "issues": issues, "xyz_count": xyz_formatted}

    def _extract_bullets(self, text):
        """Extract bullet points"""
        bullets = []
        lines = text.split('\n')
        in_experience = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect experience section start
            if 'experience' in line.lower() or 'work history' in line.lower():
                in_experience = True
                continue

            # Detect other section start
            if line.isupper() and len(line) > 3:
                in_experience = False
                continue

            # Extract bullet points
            if in_experience and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                bullet = line.lstrip('-•* ').strip()
                if len(bullet) > 10:
                    bullets.append(bullet)

        return bullets

    def check_education(self, resume_text):
        """Check education background"""
        score = 100
        issues = []

        resume_lower = resume_text.lower()

        # Check for education section
        if "education" not in resume_lower:
            return {"score": 50, "issues": ["Missing education section"]}

        # Check for degree
        has_degree = any(d in resume_lower for d in DEGREE_KEYWORDS)
        if not has_degree:
            score -= 30
            issues.append("Degree information not found")

        # Check for school
        if not any(school in resume_lower for school in SCHOOL_KEYWORDS):
            score -= 20
            issues.append("School name not found")

        # Check for graduation year
        if not re.search(r'20\d{2}', resume_text):
            score -= 10
            issues.append("Graduation year not found")

        return {"score": max(0, score), "issues": issues}

    def check_contact(self, resume_text):
        """Check contact information"""
        score = 0
        issues = []

        # Email (25 points)
        if re.search(EMAIL_PATTERN, resume_text):
            score += 25
        else:
            issues.append("Missing valid email address")

        # Phone (25 points)
        if re.search(PHONE_PATTERN, resume_text):
            score += 25
        else:
            issues.append("Missing valid phone number")

        # LinkedIn (25 points)
        if "linkedin" in resume_text.lower():
            score += 25
        else:
            issues.append("Consider adding LinkedIn profile link")

        # Location (25 points)
        if any(loc in resume_text.lower() for loc in LOCATIONS):
            score += 25
        else:
            issues.append("Consider adding your city/location")

        return {"score": score, "issues": issues}

    def check_portfolio(self, resume_text):
        """Check for portfolio and online links"""
        score = 0
        issues = []
        found_links = []

        # Check for common portfolio links
        for pattern in PORTFOLIO_PATTERNS:
            matches = re.findall(pattern, resume_text, re.IGNORECASE)
            found_links.extend(matches)

        # Check for portfolio keywords
        has_portfolio_keyword = any(kw in resume_text.lower() for kw in PORTFOLIO_KEYWORDS)

        if found_links:
            score = min(25, len(found_links) * 10)
        elif has_portfolio_keyword:
            score = 15
        else:
            issues.append("Consider adding portfolio links (GitHub, personal website)")

        # Check for LinkedIn
        if "linkedin.com/in/" in resume_text.lower():
            score = min(50, score + 25)

        return {"score": score, "issues": issues, "links": found_links}

    def identify_ats(self, jd_text):
        """Identify ATS type from job description"""
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
                "Could not identify specific ATS system",
                "Use standard formatting and keywords",
                "Keep resume clean and simple"
            ]
        }
