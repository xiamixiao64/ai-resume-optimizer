"""Interview preparation knowledge base"""
from typing import Dict, List

# Technical interview questions by skill
TECHNICAL_QUESTIONS = {
    "python": [
        {
            "question": "Explain the difference between a list and a tuple in Python.",
            "answer_guide": "Lists are mutable (can be changed), tuples are immutable. Lists use [], tuples use (). Tuples are faster and use less memory. Use tuples for fixed data, lists for dynamic collections.",
            "difficulty": "easy"
        },
        {
            "question": "How does Python handle memory management?",
            "answer_guide": "Python uses reference counting and a garbage collector. Objects are deallocated when reference count reaches 0. The GC handles circular references.",
            "difficulty": "medium"
        },
        {
            "question": "Explain GIL and its impact on multithreading.",
            "answer_guide": "GIL (Global Interpreter Lock) prevents multiple threads from executing Python bytecodes simultaneously. Use multiprocessing for CPU-bound tasks, threading for I/O-bound tasks.",
            "difficulty": "hard"
        }
    ],
    "javascript": [
        {
            "question": "Explain the difference between let, const, and var.",
            "answer_guide": "var is function-scoped, let is block-scoped, const is block-scoped and immutable. Use const by default, let when reassignment is needed, avoid var.",
            "difficulty": "easy"
        },
        {
            "question": "What is the event loop in JavaScript?",
            "answer_guide": "Event loop handles asynchronous callbacks. Call stack executes code, Web APIs handle async operations, callback queue holds callbacks, event loop moves them to stack when stack is empty.",
            "difficulty": "medium"
        },
        {
            "question": "Explain closures and their use cases.",
            "answer_guide": "Closure is a function that remembers its lexical scope. Used for data privacy, function factories, memoization, and maintaining state in callbacks.",
            "difficulty": "hard"
        }
    ],
    "react": [
        {
            "question": "What is the difference between state and props?",
            "answer_guide": "Props are read-only data passed from parent to child. State is mutable data managed within a component. Props flow down, state updates trigger re-renders.",
            "difficulty": "easy"
        },
        {
            "question": "Explain React hooks and their rules.",
            "answer_guide": "Hooks are functions that let you use state and lifecycle in functional components. Rules: only call at top level, only call from React functions. Common hooks: useState, useEffect, useContext.",
            "difficulty": "medium"
        },
        {
            "question": "What is virtual DOM and how does React use it?",
            "answer_guide": "Virtual DOM is a lightweight copy of real DOM. React compares virtual DOM with previous version (diffing), then updates only changed parts (reconciliation). This is faster than direct DOM manipulation.",
            "difficulty": "hard"
        }
    ],
    "aws": [
        {
            "question": "What is the difference between S3 and EBS?",
            "answer_guide": "S3 is object storage (files, images, backups). EBS is block storage (like a hard drive for EC2). S3 is for static assets, EBS for databases and OS.",
            "difficulty": "easy"
        },
        {
            "question": "Explain the difference between IAM roles and policies.",
            "answer_guide": "Policies are JSON documents defining permissions. Roles are identities that can be assumed by users or services. Attach policies to roles, then assign roles to entities.",
            "difficulty": "medium"
        },
        {
            "question": "How would you design a scalable architecture on AWS?",
            "answer_guide": "Use ELB for load balancing, Auto Scaling Groups for EC2, RDS for database, S3 for static assets, CloudFront for CDN. Implement caching with ElastiCache.",
            "difficulty": "hard"
        }
    ],
    "docker": [
        {
            "question": "What is the difference between a Docker image and a container?",
            "answer_guide": "Image is a read-only template with instructions. Container is a running instance of an image. Multiple containers can run from one image.",
            "difficulty": "easy"
        },
        {
            "question": "Explain Dockerfile best practices.",
            "answer_guide": "Use multi-stage builds, minimize layers, order by frequency of change, use .dockerignore, don't run as root, use specific version tags.",
            "difficulty": "medium"
        }
    ],
    "sql": [
        {
            "question": "What is the difference between WHERE and HAVING?",
            "answer_guide": "WHERE filters rows before GROUP BY. HAVING filters groups after GROUP BY. Use WHERE for row conditions, HAVING for aggregate conditions.",
            "difficulty": "easy"
        },
        {
            "question": "Explain database indexing and when to use it.",
            "answer_guide": "Index speeds up queries by creating a lookup structure. Use on columns in WHERE, JOIN, ORDER BY. Don't over-index: slows writes and uses storage.",
            "difficulty": "medium"
        }
    ]
}

# Behavioral interview questions by category
BEHAVIORAL_QUESTIONS = {
    "leadership": [
        {
            "question": "Tell me about a time you led a team through a difficult project.",
            "answer_guide": "STAR: Situation (project context), Task (your role), Action (specific steps you took), Result (measurable outcome). Focus on decision-making and team motivation.",
            "category": "leadership"
        },
        {
            "question": "Describe a situation where you had to make a tough decision without all the information.",
            "answer_guide": "STAR: Show your decision-making process, how you gathered available data, and the outcome. Emphasize risk assessment and communication.",
            "category": "leadership"
        }
    ],
    "teamwork": [
        {
            "question": "Tell me about a time you disagreed with a coworker.",
            "answer_guide": "STAR: Focus on how you resolved the conflict professionally. Show active listening, compromise, and maintaining relationship.",
            "category": "teamwork"
        },
        {
            "question": "Describe a project where you collaborated with people from different departments.",
            "answer_guide": "STAR: Highlight communication skills, understanding different perspectives, and achieving common goals.",
            "category": "teamwork"
        }
    ],
    "problem-solving": [
        {
            "question": "Tell me about a time you solved a complex problem.",
            "answer_guide": "STAR: Show your analytical process, how you broke down the problem, and the solution you implemented.",
            "category": "problem-solving"
        },
        {
            "question": "Describe a situation where you had to learn a new technology quickly.",
            "answer_guide": "STAR: Show your learning process, resources used, and how you applied the new knowledge.",
            "category": "problem-solving"
        }
    ],
    "failure": [
        {
            "question": "Tell me about a time you failed.",
            "answer_guide": "STAR: Be honest about the failure, show what you learned, and how you applied that learning. Focus on growth, not blame.",
            "category": "failure"
        }
    ],
    "achievement": [
        {
            "question": "What's your proudest professional achievement?",
            "answer_guide": "STAR: Choose something relevant to the role. Quantify the impact. Show how it demonstrates your skills.",
            "category": "achievement"
        }
    ]
}

# Company research questions
COMPANY_QUESTIONS = {
    "culture": [
        {
            "question": "Can you describe the team culture here?",
            "why_ask": "Shows you care about fit, not just the role",
            "good_answer": "Listen for: collaboration style, work-life balance, growth opportunities"
        },
        {
            "question": "How does the team handle disagreements?",
            "why_ask": "Reveals conflict resolution culture",
            "good_answer": "Look for: open communication, data-driven decisions, respect for different opinions"
        }
    ],
    "growth": [
        {
            "question": "What does success look like in this role in the first 90 days?",
            "why_ask": "Shows you're thinking about impact, not just tasks",
            "good_answer": "Clear milestones, measurable outcomes, learning opportunities"
        },
        {
            "question": "What are the biggest challenges facing the team right now?",
            "why_ask": "Shows strategic thinking and interest in contributing",
            "good_answer": "Specific challenges that match your skills"
        }
    ],
    "role": [
        {
            "question": "What does a typical day look like in this role?",
            "why_ask": "Helps you understand daily responsibilities",
            "good_answer": "Clear breakdown of tasks, meetings, and focus time"
        },
        {
            "question": "How is success measured in this position?",
            "why_ask": "Shows you care about results, not just tasks",
            "good_answer": "Clear KPIs, regular reviews, measurable outcomes"
        }
    ]
}

# Questions to ask the interviewer
INTERVIEWER_QUESTIONS = [
    {
        "question": "What's the biggest challenge the team is facing right now?",
        "purpose": "Shows strategic thinking and desire to contribute"
    },
    {
        "question": "How do you see this role evolving in the next year?",
        "purpose": "Shows interest in growth and long-term commitment"
    },
    {
        "question": "What does success look like in the first 90 days?",
        "purpose": "Shows you're thinking about impact from day one"
    },
    {
        "question": "Can you tell me about the team I'd be working with?",
        "purpose": "Shows interest in collaboration and culture fit"
    },
    {
        "question": "What's the most challenging project the team is working on?",
        "purpose": "Shows technical curiosity and problem-solving interest"
    },
    {
        "question": "How does the company support professional development?",
        "purpose": "Shows growth mindset and long-term commitment"
    }
]

# Interview tips by category
INTERVIEW_TIPS = {
    "general": [
        "Research the company thoroughly before the interview",
        "Prepare specific examples using the STAR method",
        "Practice your answers out loud",
        "Prepare thoughtful questions to ask",
        "Dress professionally (even for video interviews)",
        "Arrive 5-10 minutes early (or log in 5 minutes early for video)"
    ],
    "technical": [
        "Review the job description for required skills",
        "Practice coding problems if applicable",
        "Be ready to explain your technical decisions",
        "Show your problem-solving process, not just the answer",
        "Admit when you don't know something - show eagerness to learn"
    ],
    "behavioral": [
        "Use the STAR method for every answer",
        "Prepare 3-5 stories that demonstrate different skills",
        "Quantify your achievements whenever possible",
        "Show self-awareness about your weaknesses",
        "Demonstrate how you've grown from challenges"
    ],
    "remote": [
        "Test your technology before the interview",
        "Ensure good lighting and professional background",
        "Minimize distractions and interruptions",
        "Show strong communication skills",
        "Demonstrate self-motivation and time management"
    ]
}


def get_technical_questions(skills: List[str]) -> List[Dict]:
    """Get technical questions based on skills.
    
    Args:
        skills: List of technical skills.
        
    Returns:
        List of relevant technical questions.
    """
    questions = []
    for skill in skills:
        skill_lower = skill.lower()
        if skill_lower in TECHNICAL_QUESTIONS:
            questions.extend(TECHNICAL_QUESTIONS[skill_lower][:2])
    return questions[:6]  # Return max 6 questions


def get_behavioral_questions(categories: List[str] = None) -> List[Dict]:
    """Get behavioral questions by category.
    
    Args:
        categories: List of categories (leadership, teamwork, etc.)
        
    Returns:
        List of behavioral questions.
    """
    if not categories:
        categories = ["leadership", "teamwork", "problem-solving"]
    
    questions = []
    for cat in categories:
        if cat in BEHAVIORAL_QUESTIONS:
            questions.extend(BEHAVIORAL_QUESTIONS[cat][:2])
    return questions[:6]


def get_company_questions(focus_areas: List[str] = None) -> List[Dict]:
    """Get company research questions.
    
    Args:
        focus_areas: List of focus areas (culture, growth, role)
        
    Returns:
        List of company questions.
    """
    if not focus_areas:
        focus_areas = ["culture", "growth", "role"]
    
    questions = []
    for area in focus_areas:
        if area in COMPANY_QUESTIONS:
            questions.extend(COMPANY_QUESTIONS[area][:2])
    return questions[:6]


def get_interviewer_questions(count: int = 4) -> List[Dict]:
    """Get questions to ask the interviewer.
    
    Args:
        count: Number of questions to return.
        
    Returns:
        List of questions.
    """
    import random
    return random.sample(INTERVIEWER_QUESTIONS, min(count, len(INTERVIEWER_QUESTIONS)))


def get_tips(category: str = "general") -> List[str]:
    """Get interview tips by category.
    
    Args:
        category: Tip category (general, technical, behavioral, remote)
        
    Returns:
        List of tips.
    """
    return INTERVIEW_TIPS.get(category, INTERVIEW_TIPS["general"])


def generate_interview_prep(skills: List[str], job_type: str = "technical") -> Dict:
    """Generate complete interview preparation package.
    
    Args:
        skills: List of candidate's skills.
        job_type: Type of job (technical, behavioral, mixed)
        
    Returns:
        Dictionary with all interview prep materials.
    """
    technical = get_technical_questions(skills)
    behavioral = get_behavioral_questions(["leadership", "teamwork", "problem-solving"])
    company = get_company_questions(["culture", "growth", "role"])
    your_questions = get_interviewer_questions(4)
    tips = get_tips("technical" if job_type == "technical" else "behavioral")
    
    # Add salary and remote questions
    salary_questions = SALARY_QUESTIONS[:2]
    remote_questions = REMOTE_QUESTIONS[:2]
    
    return {
        "technical_questions": technical,
        "behavioral_questions": behavioral,
        "company_questions": company,
        "your_questions": your_questions,
        "salary_questions": salary_questions,
        "remote_questions": remote_questions,
        "tips": tips
    }


# Common salary negotiation questions
SALARY_QUESTIONS = [
    {
        "question": "What are your salary expectations?",
        "answer_guide": "Research market rate first. Give a range based on experience. Say: 'Based on my research and experience, I'm looking for $X-Y, but I'm open to discussing the total compensation package.'",
        "category": "negotiation"
    },
    {
        "question": "What is your current salary?",
        "answer_guide": "Optional to answer depending on location laws. If asked: 'I'm focused on the value I can bring to this role rather than my current compensation. What's the budget for this position?'",
        "category": "negotiation"
    },
    {
        "question": "Why should we pay you more than other candidates?",
        "answer_guide": "Highlight unique value: specific skills, experience level, certifications, or accomplishments that justify higher compensation.",
        "category": "negotiation"
    }
]

# Remote work specific questions
REMOTE_QUESTIONS = [
    {
        "question": "How do you stay productive working remotely?",
        "answer_guide": "Mention: dedicated workspace, time blocking, communication tools (Slack, Zoom), regular check-ins, and work-life boundaries.",
        "category": "remote"
    },
    {
        "question": "How do you handle collaboration across time zones?",
        "answer_guide": "Discuss: async communication practices, overlap hours, documentation habits, and tools used for distributed teams.",
        "category": "remote"
    },
    {
        "question": "What's your home office setup?",
        "answer_guide": "Describe: dedicated space, reliable internet, necessary equipment, and how you minimize distractions.",
        "category": "remote"
    }
]

# Industry-specific questions
INDUSTRY_QUESTIONS = {
    "tech": [
        {
            "question": "Tell me about a time you debugged a complex production issue.",
            "answer_guide": "STAR: Describe the problem, your debugging process, tools used, and resolution.",
            "category": "technical"
        },
        {
            "question": "How do you stay current with new technologies?",
            "answer_guide": "Mention: blogs, courses, side projects, open source contributions, tech talks.",
            "category": "learning"
        }
    ],
    "finance": [
        {
            "question": "How do you ensure accuracy in financial reporting?",
            "answer_guide": "Discuss: attention to detail, verification processes, tools used, and error prevention.",
            "category": "accuracy"
        }
    ],
    "healthcare": [
        {
            "question": "How do you handle sensitive patient information?",
            "answer_guide": "Discuss: HIPAA compliance, data security practices, confidentiality protocols.",
            "category": "compliance"
        }
    ]
}
