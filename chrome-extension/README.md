# ResumeForge AI - ATS Resume Checker Chrome Extension

Check your resume against ATS systems directly from job posting pages.

## Features

- **ATS Type Detection**: Automatically detects which ATS (Workday, Taleo, Greenhouse, etc.) the company uses
- **Optimization Tips**: Shows specific tips for the detected ATS system
- **Quick Resume Check**: Paste your resume and get instant feedback
- **One-Click Access**: Open the full ResumeForge AI tool from any job posting

## Supported ATS Systems

- Workday
- Taleo (Oracle)
- Greenhouse
- Lever
- iCIMS
- SmartRecruiters
- BambooHR
- SuccessFactors
- JobVite
- ApplicantStack
- Bullhorn
- ClearCompany

## Installation

### From Chrome Web Store (Coming Soon)

1. Visit the Chrome Web Store
2. Search for "ResumeForge AI"
3. Click "Add to Chrome"

### Manual Installation (Developer Mode)

1. Download or clone this repository
2. Open Chrome and go to `chrome://extensions/`
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select the `chrome-extension` folder

## Usage

1. Visit any job posting page
2. Click the ResumeForge AI icon in your toolbar
3. The extension will automatically detect the ATS type
4. View optimization tips specific to that ATS
5. Paste your resume to check your ATS score

## Development

### File Structure

```
chrome-extension/
├── manifest.json      # Extension configuration
├── popup.html         # Popup UI
├── popup.js           # Popup logic
├── background.js      # Service worker
├── content.js         # Content script for job pages
├── content.css        # Content script styles
├── icons/             # Extension icons
└── README.md          # This file
```

### Testing

1. Load the extension in developer mode
2. Visit a job posting page (e.g., Workday, Greenhouse)
3. Click the extension icon
4. Verify ATS detection works

## Privacy

- No data is collected without your consent
- Resume text is only sent to resumeforge.ai when you click "Check ATS Score"
- No browsing history is tracked

## Support

- Website: https://resumeforge.ai
- Email: xiamixiao64@gmail.com

## License

MIT License
