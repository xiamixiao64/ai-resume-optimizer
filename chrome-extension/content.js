// ResumeForge AI - Content Script
// Runs on job posting pages to detect ATS and extract job description

(function() {
    'use strict';

    // Listen for messages from popup
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === 'getPageContent') {
            const content = extractJobDescription();
            sendResponse({ content });
        }
        return true;
    });

    // Extract job description from page
    function extractJobDescription() {
        // Try common job description selectors
        const selectors = [
            '.job-description',
            '.job-details',
            '[data-automation="jobDescription"]',
            '#jobDescription',
            '.description',
            '.content',
            'article',
            'main'
        ];

        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element && element.textContent.length > 100) {
                return element.textContent.trim().substring(0, 5000);
            }
        }

        // Fallback: get main content
        const main = document.querySelector('main') || document.body;
        return main.textContent.trim().substring(0, 5000);
    }

    // Add floating button (optional - can be enabled later)
    function addFloatingButton() {
        const button = document.createElement('div');
        button.id = 'resumeforge-btn';
        button.innerHTML = '🔍';
        button.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 9999;
            box-shadow: 0 4px 12px rgba(168, 85, 247, 0.4);
            font-size: 24px;
            transition: transform 0.2s;
        `;
        
        button.addEventListener('mouseenter', () => {
            button.style.transform = 'scale(1.1)';
        });
        
        button.addEventListener('mouseleave', () => {
            button.style.transform = 'scale(1)';
        });
        
        button.addEventListener('click', () => {
            // Open popup or trigger action
            chrome.runtime.sendMessage({ action: 'openPopup' });
        });

        document.body.appendChild(button);
    }

    // Uncomment to enable floating button
    // addFloatingButton();
})();
