"""Shared constants for resume analysis"""

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

# Tech keywords in display case (for user-facing output)
TECH_KEYWORDS_DISPLAY = [
    "Python", "Java", "JavaScript", "TypeScript", "React", "Vue", "Angular",
    "Node.js", "Django", "Flask", "Spring", "Spring Boot", "Express",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD",
    "Git", "GitHub", "GitLab", "REST API", "GraphQL", "Microservices",
    "Agile", "Scrum", "TDD", "Linux", "Nginx", "Apache"
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

# Default skills to suggest when list is too short
DEFAULT_SKILLS = [
    "Python", "JavaScript", "SQL", "Git", "REST APIs", "Agile",
    "Problem Solving", "Team Collaboration"
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

# Synonym groups for keyword matching
SYNONYM_GROUPS = {
    "manage": ["lead", "led", "direct", "oversee", "supervise", "coordinate"],
    "develop": ["build", "built", "create", "created", "design", "designed", "implement", "implemented", "construct"],
    "improve": ["enhance", "enhanced", "optimize", "optimized", "upgrade", "refine", "boost", "increased"],
    "reduce": ["decrease", "minimize", "cut", "lower", "streamline", "reduced", "decreased"],
    "increase": ["grow", "expanded", "raise", "raised", "elevate", "scale", "scaled"],
    "analyze": ["evaluate", "assess", "review", "examine", "audit"],
    "communicate": ["present", "report", "convey", "articulate", "express"],
    "collaborate": ["partner", "team up", "work with", "coordinate with"],
}

# X-Y-Z format patterns for quantified achievements
XYZ_PATTERNS = [
    # X (action) - Y (context) - Z (result)
    r'(?:led|built|developed|implemented|designed|created|launched|managed|optimized|reduced|increased|improved|delivered)\s+.+?(?:resulting in|leading to|which achieved|with|for)\s+\d+',
    # Percentage improvements
    r'(?:increased|improved|reduced|decreased|boosted|enhanced)\s+.+?\d+%',
    # Revenue/money impact
    r'(?:saved|generated|reduced|increased)\s+.+?\$[\d,]+',
    # Scale/users
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

# Stronger action verbs for X-Y-Z format
XYZ_ACTION_VERBS = [
    "architected", "automated", "conceptualized", "consolidated", "coordinate",
    "catalyzed", "championed", "ciphered", "commissioned", "communicated",
    "condensed", "conceived", "concluded", "conducted", "constructed",
    "consulted", "contracted", "converted", "coordinated", "corrected",
    "counseled", "created", "critiqued", "customized", "debated",
    "decreased", "defined", "delegated", "demonstrated", "deployed",
    "designed", "determined", "developed", "devised", "diagnosed",
    "directed", "discovered", "dispensed", "displayed", "distinguished",
    "distributed", "drafted", "drove", "earned", "edited",
    "eliminated", "employed", "enabled", "encouraged", "engineered",
    "enhanced", "established", "estimated", "evaluated", "exceeded",
    "executed", "expanded", "expedite", "facilitated", "fashioned",
    "forecasted", "forged", "formalized", "formulated", "fostered",
    "fulfilled", "generated", "governed", "grouped", "guided",
    "halved", "handled", "harmonized", "hastened", "headquartered",
    "heightened", "helped", "heralded", "honed", "identified",
    "illustrated", "implemented", "improved", "incorporated", "increased",
    "influenced", "informed", "initiated", "innovated", "integrated",
    "intensified", "interpreted", "introduced", "invented", "invited",
    "isolated", "justified", "launched", "lectured", "legislated",
    "leveraged", "lifted", "limited", "litigated", "localized",
    "located", "maintained", "managed", "manipulated", "marketed",
    "maximized", "measured", "mediated", "mentored", "merged",
    "migrated", "minimized", "mitigated", "modeled", "modified",
    "monitored", "negotiated", "notified", "obtained", "operated",
    "orchestrated", "ordered", "organized", "originated", "overhauled",
    "oversaw", "participated", "partnered", "performed", "persuaded",
    "piloted", "pinpointed", "planned", "pledged", "positioned",
    "predicted", "prioritized", "procured", "produced", "programmed",
    "projected", "promoted", "proposed", "proved", "provided",
    "published", "pursued", "qualified", "quantified", "raised",
    "ratified", "reached", "reconciled", "reduced", "refined",
    "reinforced", "relocated", "remedied", "rendered", "reorganized",
    "replaced", "reported", "represented", "reproduced", "resolved",
    "responded", "restored", "restructured", "retained", "reversed",
    "revamped", "reviewed", "revitalized", "revolved", "rigged",
    "routed", "saved", "scoped", "secured", "segmented",
    "selected", "serviced", "set", "settled", "shaped",
    "shifted", "simplified", "sized", "sketched", "slashed",
    "solved", "spearheaded", "specified", "standardized", "steered",
    "stimulated", "streamlined", "strengthened", "strived", "structured",
    "substituted", "summarized", "superseded", "supervised", "supplemented",
    "surveyed", "symbolized", "systematized", "tabulated", "targeted",
    "taught", "team-taught", "terminated", "tested", "theorized",
    "totaled", "tracked", "traded", "trained", "transferred",
    "transformed", "translated", "transmitted", "transported", "traveled",
    "treated", "trimmed", "troubleshoot", "turned", "typified",
    "underlined", "undertook", "unified", "uncovered", "underwrote",
    "updated", "upgraded", "utilized", "validated", "verified",
    "violated", "visited", "volunteered", "weighed", "widened",
    "won", "wrote", "yielded"
]

# Portfolio/online presence keywords
PORTFOLIO_KEYWORDS = [
    "portfolio", "github", "behance", "dribbble", "personal website",
    "personal site", "online portfolio", "work samples", "projects"
]
