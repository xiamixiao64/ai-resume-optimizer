// ResumeForge AI - Background Service Worker

// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
    console.log('ResumeForge AI ATS Checker installed');
});

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'detectATS') {
        // ATS detection logic
        const url = request.url || '';
        const detected = detectATS(url);
        sendResponse({ detected });
    }
    return true;
});

// Detect ATS from URL
function detectATS(url) {
    const urlLower = url.toLowerCase();
    
    const patterns = {
        workday: ['workday', 'myworkdayjobs', 'wd5.myworkday', 'wday.com'],
        taleo: ['taleo', 'oracle.com/taleo', 'talent.oracle'],
        greenhouse: ['greenhouse.io', 'boards.greenhouse', 'greenhouse.com'],
        lever: ['lever.co', 'jobs.lever', 'lever.co/'],
        icims: ['icims.com', 'jobs.icims', 'icims.com/'],
        smartrecruiters: ['smartrecruiters', 'smartrecruiters.com'],
        bamboohr: ['bamboohr.com', 'bamboo hr', 'bamboohr'],
        successfactors: ['successfactors', 'sap.com/careers', 'sapsf'],
        jobvite: ['jobvite.com', 'jobvite'],
        applicantstack: ['applicantstack.com', 'applicantstack'],
        bullhorn: ['bullhorn.com', 'bullhorn'],
        clearcompany: ['clearcompany.com', 'clearcompany']
    };

    for (const [key, patternList] of Object.entries(patterns)) {
        for (const pattern of patternList) {
            if (urlLower.includes(pattern)) {
                return { type: key, detected: true };
            }
        }
    }
    
    return { type: 'unknown', detected: false };
}
