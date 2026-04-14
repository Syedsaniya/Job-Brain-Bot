# AI Intelligence Layer Implementation

## Overview
This implementation adds an AI intelligence layer to Job Brain Bot for job analysis, skill gap identification, and networking message generation.

## New Features

### 1. Job Description Analysis (`/analyze`)
AI-powered analysis of job postings to extract:
- Required and preferred skills
- Experience level requirements
- Role category classification
- Key responsibilities
- Soft skills mentioned
- Certifications required/recommended
- Potential red flags

### 2. Skill Gap Analysis (`/skills`)
Compares user profile against job requirements:
- Calculates skill coverage percentage
- Identifies missing critical skills
- Prioritizes skills by importance (critical, high, medium, low)
- Estimates learning hours for each skill
- Suggests learning resources (courses, books)
- Recommends relevant certifications
- Provides personalized preparation timeline

### 3. Networking Message Generator (`/network`)
Generates personalized cold outreach messages:
- LinkedIn connection requests
- Email to hiring managers
- Industry professional outreach
- Includes subject lines and body text
- Provides follow-up templates
- Gives tips for successful networking

### 4. Referral Request Generator (`/referral`)
Creates referral request messages for:
- Former colleagues
- Alumni connections
- Mutual connections
- Professional tone with easy opt-out

## Architecture

### New Modules Created

#### `src/job_brain_bot/ai_intelligence/__init__.py`
Package initialization with exports.

#### `src/job_brain_bot/ai_intelligence/analyzer.py`
Job description analyzer using pattern matching:
- Extracts skills from job text
- Identifies experience levels
- Detects certifications
- Extracts responsibilities
- Identifies soft skills
- Detects red flags

Key classes:
- `JobAnalysis` - Structured analysis result

#### `src/job_brain_bot/ai_intelligence/skill_ontology_expanded.py`
Expanded skill database with learning pathways:
- 50+ skills with learning resources
- Beginner/Intermediate/Advanced pathways
- Certification recommendations per skill
- Career tracks for different roles
- Certification details (cost, level, validity)

Key classes:
- `SkillPathway` - Learning resources for a skill
- `CareerTrack` - Role progression with skill requirements

Skills covered:
- Programming: Python, JavaScript, TypeScript, SQL
- Frontend: React, Angular, Vue
- Backend: Node.js, databases
- Cloud/DevOps: AWS, Azure, Docker, Kubernetes
- Cybersecurity: Network security, SIEM, Penetration testing
- Data: Machine Learning, Data Analysis

#### `src/job_brain_bot/ai_intelligence/skill_gap.py`
Skill gap analyzer and recommender:
- Compares user skills vs job requirements
- Calculates skill coverage
- Prioritizes missing skills
- Estimates learning difficulty
- Generates learning paths
- Suggests certifications

Key classes:
- `SkillGap` - Individual skill gap with resources
- `GapAnalysis` - Complete gap analysis result

#### `src/job_brain_bot/ai_intelligence/networking.py`
Networking message generator:
- Cold message templates for different scenarios
- Referral request templates
- Follow-up message templates
- LinkedIn connection notes

Key classes:
- `NetworkingMessage` - Generated message with metadata

## Telegram Commands

### New Commands Added

| Command | Description | Usage |
|---------|-------------|-------|
| `/analyze [job#]` | Analyze job requirements with AI | `/analyze` or `/analyze 2` |
| `/skills [job#]` | Skill gap analysis vs your profile | `/skills` or `/skills 3` |
| `/network [job#] [name]` | Generate cold outreach message | `/network` or `/network 2 John` |
| `/referral [job#] [name]` | Generate referral request | `/referral` or `/referral 1 Jane` |

### Updated Commands

| Command | Changes |
|---------|---------|
| `/start` | Now shows AI features section |
| `/jobs` | Added time parameter support (from previous PR) |

## Configuration

Add to `.env` file:
```env
# AI Intelligence Settings
AI_ANALYSIS_ENABLED=true
NETWORKING_GENERATOR_ENABLED=true
AI_PROVIDER=pattern  # Options: pattern, openai, anthropic
OPENAI_API_KEY=      # Optional - for future OpenAI integration
ANTHROPIC_API_KEY=   # Optional - for future Claude integration
```

## Files Modified

### `src/job_brain_bot/types.py`
Added new dataclasses:
- `AIJobAnalysis`
- `SkillGapResult`
- `NetworkingMessageResult`

### `src/job_brain_bot/config.py`
Added AI settings:
- `openai_api_key`
- `anthropic_api_key`
- `ai_provider`
- `ai_analysis_enabled`
- `networking_generator_enabled`

### `src/job_brain_bot/telegram/bot.py`
Added command handlers:
- `analyze()` - Job analysis command
- `skills()` - Skill gap command
- `network()` - Networking message command
- `referral()` - Referral request command

Updated imports to include AI modules.

### `src/job_brain_bot/telegram/formatters.py`
Added formatter functions:
- `format_job_analysis()` - Formats JobAnalysis for display
- `format_skill_gap()` - Formats GapAnalysis for display
- `format_networking_message()` - Formats NetworkingMessage for display

## Example Usage

### Analyze a Job
```
User: /analyze 1
Bot: 🤖 AI Analysis for: SOC Analyst at XYZ Corp

📋 Role Category: Cybersecurity
🎯 Experience Level: Fresher

🔧 Required Skills:
siem, splunk, python, linux, incident response

⭐ Preferred Skills:
network security, threat hunting, vulnerability assessment

📜 Certifications Mentioned:
CompTIA Security+, CEH

🤝 Soft Skills:
communication, problem solving

📝 Key Responsibilities:
1. Monitor security alerts and investigate incidents...
```

### Skill Gap Analysis
```
User: /skills 1
Bot: 📊 Skill Gap Analysis: Your Profile vs SOC Analyst

✅ Strong Match! You have most of the required skills...

📊 Skill Coverage: 75%
⏱ Estimated Prep Time: 1-2 weeks

✅ You Have (6):
python, linux, networking, sql, git, basics

📚 Skills to Learn (3):
🔴 siem (critical, ~60h)
   📖 Splunk Fundamentals, Elastic SIEM Guide
🟠 incident response (high, ~100h)
   📖 Incident Response Basics, NIST SP 800-61
🟡 threat hunting (medium, ~80h)

🎓 Certifications to Consider:
• CompTIA Security+ (Entry, $370)
• CEH (Intermediate, $1,199)

🎯 Suggested Learning Order:
1. siem (~60h)
2. incident response (~100h)
3. threat hunting (~80h)
```

### Generate Networking Message
```
User: /network 1 Sarah
Bot: 💬 Networking Message for SOC Analyst at XYZ Corp

Subject: SOC Analyst candidate interested in XYZ Corp

Message:
```
Hi Sarah,

I came across your profile while researching XYZ Corp and was impressed by your experience in cybersecurity.

I'm a Security Analyst with experience in python, linux, and networking. I'm very interested in the SOC Analyst role at XYZ Corp and would love to learn more about the team and culture.

Would you be open to a brief chat? I'd really appreciate any insights you could share.

Best regards,
[Your Name]
```

💡 Tips:
• Personalize the message with specific details from their profile
• Keep it under 150 words for LinkedIn connection requests
• Follow up once after 5-7 days if no response

🔄 Follow-up:
...
```

## Key Features

### Skill Prioritization
- **Critical**: Core technical skills (Python, SQL for data roles)
- **High**: Role-specific essential skills
- **Medium**: Preferred/nice-to-have skills
- **Low**: Bonus skills

### Learning Resources
Each skill includes:
- Beginner resources (courses, tutorials)
- Intermediate resources (books, advanced courses)
- Advanced resources (specialized topics)
- Certifications available
- Estimated learning hours

### Career Tracks
Pre-defined tracks for:
- Frontend Developer
- Backend Developer
- Full Stack Developer
- DevOps Engineer
- Security Analyst
- Data Scientist

Each track includes entry/mid/senior skill requirements and recommended certifications.

## Testing
All 19 existing tests pass. The AI layer uses pattern matching by default (no API keys required), with hooks for future OpenAI/Anthropic integration.

## Future Enhancements
- Integration with OpenAI/Anthropic for more sophisticated analysis
- Resume tailoring suggestions based on job analysis
- Interview question generator based on job requirements
- Company culture analysis from reviews
- Salary range estimation
- Automated job application tracking
