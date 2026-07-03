// ResumeForge AI - ATS Type Detector Popup Script

const API_BASE = 'https://resumeforge.ai';

// ATS patterns for detection
const ATS_PATTERNS = {
    workday: { patterns: ['workday', 'myworkdayjobs', 'wd5.myworkday', 'wday.com'], name: 'Workday' },
    taleo: { patterns: ['taleo', 'oracle.com/taleo', 'talent.oracle'], name: 'Taleo' },
    greenhouse: { patterns: ['greenhouse.io', 'boards.greenhouse', 'greenhouse.com'], name: 'Greenhouse' },
    lever: { patterns: ['lever.co', 'jobs.lever', 'lever.co/'], name: 'Lever' },
    icims: { patterns: ['icims.com', 'jobs.icims', 'icims.com/'], name: 'iCIMS' },
    smartrecruiters: { patterns: ['smartrecruiters', 'smartrecruiters.com'], name: 'SmartRecruiters' },
    bamboohr: { patterns: ['bamboohr.com', 'bamboo hr', 'bamboohr'], name: 'BambooHR' },
    successfactors: { patterns: ['successfactors', 'sap.com/careers', 'sapsf'], name: 'SuccessFactors' },
    jobvite: { patterns: ['jobvite.com', 'jobvite'], name: 'JobVite' },
    applicantstack: { patterns: ['applicantstack.com', 'applicantstack'], name: 'ApplicantStack' },
    bullhorn: { patterns: ['bullhorn.com', 'bullhorn'], name: 'Bullhorn' },
    clearcompany: { patterns: ['clearcompany.com', 'clearcompany'], name: 'ClearCompany' }
};

// Tips for each ATS
const ATS_TIPS = {
    workday: ['Use PDF format', 'Exact keyword matching matters', 'Standard section headers required'],
    taleo: ['Word format preferred', 'Avoid special characters', 'Simple formatting works best'],
    greenhouse: ['Both PDF and Word work', 'Skills section is crucial', 'Use industry-standard terms'],
    lever: ['Keep formatting clean', 'Single column layout', 'Avoid graphics and tables'],
    icims: ['Standard format works', 'Natural keyword distribution', 'Clear contact information'],
    smartrecruiters: ['Keyword matching is key', 'Match skills to job description', 'Keep format simple'],
    bamboohr: ['Simple, clean format', 'Complete contact info', 'Standard headings'],
    successfactors: ['Structured data preferred', 'Standard job titles', 'Consistent date format'],
    jobvite: ['Clean formatting', 'Industry-standard keywords', 'Social links helpful'],
    applicantstack: ['Keyword matching important', 'Standard format', 'Clear section headers'],
    bullhorn: ['Standardized format', 'Keyword alignment', 'Professional layout'],
    clearcompany: ['Highlight achievements', 'Quantified results', 'Skills-first approach']
};

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (tab) {
        detectATSFromUrl(tab.url);
    }
});

// Detect ATS from URL
function detectATSFromUrl(url) {
    if (!url) {
        showUnknown();
        return;
    }

    const urlLower = url.toLowerCase();
    
    for (const [key, config] of Object.entries(ATS_PATTERNS)) {
        for (const pattern of config.patterns) {
            if (urlLower.includes(pattern)) {
                showDetected(key, config.name);
                return;
            }
        }
    }
    
    showUnknown();
}

// Show detected ATS
function showDetected(type, name) {
    const badge = document.getElementById('atsBadge');
    const atsType = document.getElementById('atsType');
    const atsLabel = document.getElementById('atsLabel');
    const tipsSection = document.getElementById('tipsSection');
    const tipsList = document.getElementById('tipsList');

    badge.className = 'ats-badge detected';
    atsType.textContent = name;
    atsType.className = 'ats-type';
    atsLabel.textContent = 'ATS Detected on This Page';

    // Show tips
    const tips = ATS_TIPS[type] || [];
    tipsList.innerHTML = tips.map(tip => `<div class="tip-item">${tip}</div>`).join('');
    tipsSection.style.display = 'block';
}

// Show unknown ATS
function showUnknown() {
    const badge = document.getElementById('atsBadge');
    const atsType = document.getElementById('atsType');
    const atsLabel = document.getElementById('atsLabel');

    badge.className = 'ats-badge unknown';
    atsType.textContent = 'Unknown ATS';
    atsType.className = 'ats-type unknown';
    atsLabel.textContent = 'Could not detect ATS from this page';
}

// Check resume
async function checkResume() {
    const resumeText = document.getElementById('resumeInput').value.trim();
    
    if (!resumeText) {
        alert('Please paste your resume first');
        return;
    }

    // Get current page content for JD
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    let jobDescription = '';
    
    if (tab) {
        try {
            const response = await chrome.tabs.sendMessage(tab.id, { action: 'getPageContent' });
            jobDescription = response?.content || '';
        } catch (e) {
            // Content script might not be loaded
        }
    }

    // Open full tool in new tab
    chrome.tabs.create({ 
        url: `${API_BASE}/?resume=${encodeURIComponent(resumeText)}&jd=${encodeURIComponent(jobDescription)}`
    });
}

// Open full tool
function openFullTool() {
    chrome.tabs.create({ url: API_BASE });
}
