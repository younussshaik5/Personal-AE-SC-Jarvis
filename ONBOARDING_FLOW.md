# JARVIS Onboarding Flow - End-to-End Learning System

## Vision
When a user forks/deploys JARVIS, the system **automatically learns about them** through an intelligent onboarding conversation. Zero manual setup, zero config files - just natural conversation that scaffolds everything.

## How It Works: The 5-Stage Flow

### Stage 1: Welcome
```
User: (Fork complete, first interaction)

JARVIS:
🎉 Welcome to JARVIS - Your Autonomous Sales AI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

I'm JARVIS, your 24/7 AI sales assistant. Over the next few minutes, 
I'll learn about:
  🏢 Your company and what you sell
  👤 Your role and sales challenges
  📊 Your sales process and goals

Ready? Just tell me about your company in a few sentences.

Examples:
  • "I'm at Acme Corp, a 50-person SaaS company in the HR space."
  • "We're a fintech startup offering payment solutions to SMBs."
```

**What Happens:**
- System detects this is first-time use
- No accounts exist yet
- Flow starts with welcome message

---

### Stage 2: Company Discovery
```
User: "I work at TataCommunications, we're a $100M+ enterprise telecom company 
        that provides connectivity solutions to businesses."

System (OnboardingInfoExtractor):
  ✓ Extracted: company_name = "TataCommunications"
  ✓ Extracted: industry = "Telecom"
  ✓ Extracted: revenue = "$100M+"
  ✓ Extracted: size = "enterprise"

JARVIS:
✓ Company: **TataCommunications**
✓ Industry: **Telecom**
✓ Size: **enterprise**
✓ Revenue: **$100M+**

Now, tell me about your role. Are you an AE, presales engineer, sales manager?
```

**What Happens Behind the Scenes:**
- `OnboardingInfoExtractor.extract_company_name()` uses regex patterns to find "TataCommunications"
- `extract_industry()` matches "telecom" to Telecom category
- `extract_company_size()` maps "enterprise" to enterprise tier
- `extract_revenue()` parses "$100M+" to $100M
- All extracted data stored in `extractor.extracted_info`

---

### Stage 3: Role Discovery
```
User: "I'm an Account Executive, managing 5-10 enterprise deals at any time."

System (OnboardingInfoExtractor):
  ✓ Extracted: role = "Sales Executive"
  ✓ Noted: "managing... deals" = active sales

JARVIS:
✓ Role: **Account Executive**

Perfect! Now, what do you sell? What are your main products or services?
```

**What Happens:**
- `extract_user_role()` matches "Account Executive" to Sales Executive category
- Role information captured for CLAUDE.md initial configuration
- Skills will be prioritized based on AE role

---

### Stage 4: Offerings Discovery
```
User: "We sell global connectivity, SD-WAN solutions, and managed network services 
       to enterprises and mid-market companies."

System (OnboardingInfoExtractor):
  ✓ Extracted: offerings = [
      "global connectivity",
      "SD-WAN solutions", 
      "managed network services"
    ]

JARVIS:
✓ Offerings: **global connectivity, SD-WAN solutions, managed network services**

Last question: What's your biggest sales challenge right now?
(Examples: long sales cycles, low win rates, slow discovery, proposal turnaround time)
```

**What Happens:**
- `extract_offerings()` parses the list of products
- Each offering stored separately for vectorization into knowledge base
- Will be used by knowledge_builder agent to create company-specific materials

---

### Stage 5: Challenge Discovery
```
User: "Our main challenge is the long discovery phase. Enterprise customers 
       need to understand our solutions before they're ready to move forward. 
       It's a 2-3 month process right now."

System (OnboardingInfoExtractor):
  ✓ Extracted: challenges = ["discovery", "long sales cycles"]
  ✓ Extracted: sales_process = "enterprise-deal"

JARVIS:
✓ Focus: **discovery, long sales cycles**

Perfect! Let me review what I learned:

📍 **Company**: TataCommunications (Telecom, enterprise)
👤 **Your Role**: Account Executive
📦 **You Sell**: global connectivity, SD-WAN solutions, managed network services
🎯 **Focus Area**: discovery, long sales cycles

Ready to create your account? Just confirm and I'll set everything up!
(Type: yes to confirm, or tell me what to change)
```

---

### Stage 6: Account Creation & Scaffolding
```
User: "Yes, set it up!"

System (OnboardingSkill._auto_complete_onboarding):
  1. Validates extracted company_name
  2. Calls AccountScaffolder.scaffold_account("TataCommunications", company_info)
  3. Creates folder: ACCOUNTS/TataCommunications/
  4. Populates company_research.md with extracted details
  5. Creates discovery.md template with Tata context
  6. Creates deal_stage.json with company name pre-filled
  7. Creates CLAUDE.md with extracted role/challenges
  8. Invalidates AccountHierarchy cache
  9. Loads ClaudeMdLoader config for new account

JARVIS:
✅ **Account Created!**

📁 **TataCommunications** is ready to go!

**Created files:**
  ✓ company_research.md - Your company overview
  ✓ discovery.md - Sales discovery template
  ✓ deal_stage.json - Deal pipeline tracker
  ✓ CLAUDE.md - Your account configuration

**What's Next?**

1️⃣ **Upload files** - Drop proposals, contracts, or competitor docs in cowork
2️⃣ **Start selling** - Use skills like:
   • /get_discovery - Plan discovery calls (since that's your challenge!)
   • /get_proposal - Generate proposals
   • /get_battlecard - Create competitor battlecards
   • /get_demo_strategy - Plan demos

3️⃣ **Keep improving** - I learn from every file and conversation

I'm learning about TataCommunications now. Drop files in cowork and I'll analyze them!
```

---

## Automatic Learning (After Account Creation)

Once the account is created, JARVIS continuously learns:

### File Analysis (Ongoing)
When user uploads files to cowork:
- Proposal PDFs → Extract pricing, value props, customer names
- Discovery notes → Learn how TataCommunications does discovery
- Competitor docs → Build competitive knowledge base
- Email templates → Learn communication style

### Conversation Analysis (Continuous)
From user's chats:
- Detects patterns: "discovery is mentioned 85% more than demos"
- Learns: "This AE spends 2x time on discovery vs industry average"
- Suggests: "Should we optimize get_discovery skill for this company?"

### Auto-Evolution (Self-Improving)
Every 7 days:
- CLAUDE.md evolves based on usage patterns
- "Since you spend lots of time on discovery, I've optimized get_discovery to focus on..."
- New skills suggested: "Found 3 ways to speed up discovery based on your approach"

## Information Flow Architecture

```
User Input (Natural Language)
    ↓
OnboardingInfoExtractor
    ├─ extract_company_name()
    ├─ extract_industry()
    ├─ extract_company_size()
    ├─ extract_revenue()
    ├─ extract_user_role()
    ├─ extract_offerings()
    ├─ extract_sales_process()
    ├─ extract_challenges()
    └─ Stores in: extractor.extracted_info{}
    ↓
OnboardingSkill Validates & Displays
    ├─ Confirms extraction with user
    ├─ Allows corrections if needed
    └─ Summarizes for confirmation
    ↓
AccountScaffolder
    ├─ Creates: ACCOUNTS/TataCommunications/
    ├─ Creates: company_research.md (pre-filled)
    ├─ Creates: discovery.md (template)
    ├─ Creates: deal_stage.json (pre-filled)
    └─ Creates: CLAUDE.md (role/challenge aware)
    ↓
AccountHierarchy
    └─ Invalidates cache, rebuilds account list
    ↓
ClaudeMdLoader
    └─ Loads account config for use in skills
    ↓
AgentOrchestrator (Background)
    ├─ FileAnalyzer - waits for cowork uploads
    ├─ ConversationAnalyzer - learns from chats
    ├─ ConfigEvolver - auto-improves CLAUDE.md
    └─ Updates company knowledge continuously
```

---

## Key Components

### OnboardingInfoExtractor (250 lines)
Intelligently parses natural language:
- 8 extraction methods (company, industry, size, revenue, role, offerings, process, challenges)
- Multiple regex patterns for each category (robust to language variations)
- Returns structured data ready for account creation

### OnboardingSkill (300 lines)
Interactive multi-stage flow:
- 5 conversation stages with context-aware prompts
- Displays extracted info for user confirmation
- Handles corrections/edits before account creation
- Auto-completes scaffolding and returns next steps

### Integration Points

**AccountScaffolder**:
- Takes extracted company_info dict
- Pre-fills templates with learned details
- Creates initial CLAUDE.md with role/challenge awareness

**AccountHierarchy**:
- Updated when new account created
- Enables fuzzy matching (Tata Communications → TataCommunications)
- Supports sub-accounts: TataTele, TataSky

**ClaudeMdLoader**:
- Loads account-specific config from newly created CLAUDE.md
- Makes initial configuration immediately available

---

## Example: Full Conversation Transcript

```
User: Hey, let's set this up for my company

Claude: 🎉 Welcome to JARVIS...
[Shows welcome message]

User: I work at Tata Communications, we're a $100M telecom company

Claude: ✓ Company: TataCommunications
        ✓ Industry: Telecom
        ✓ Revenue: $100M
        
        Now tell me your role...

User: I'm an AE managing enterprise deals

Claude: ✓ Role: Account Executive
        
        What do you sell?

User: We sell connectivity, SD-WAN, managed networks

Claude: ✓ Offerings: connectivity, SD-WAN, managed networks
        
        What's your biggest challenge?

User: Discovery takes forever, 2-3 months usually

Claude: ✓ Focus: discovery, long sales cycles
        
        [Shows summary]
        Ready to create account?

User: Yes

Claude: ✅ Account Created!
        📁 TataCommunications is ready
        
        Created:
        ✓ company_research.md
        ✓ discovery.md
        ✓ deal_stage.json
        ✓ CLAUDE.md
        
        Next steps:
        1. Upload files (proposals, discovery notes, etc.)
        2. Start using skills (I've optimized for discovery!)
        3. Watch me learn and improve
```

---

## Success Criteria

✅ User forks JARVIS
✅ First message triggers onboarding
✅ Natural conversation extracts company details
✅ Account auto-scaffolded with pre-filled info
✅ CLAUDE.md created with role-aware configuration
✅ User immediately ready to use system
✅ System learns from first files uploaded
✅ Zero manual setup required

---

## Future Enhancements

- **Multi-turn refinement**: "Tell me more about..." to dig deeper
- **Validation prompts**: "Did I get that right?" for uncertain extractions
- **Competitor mapping**: Auto-load competitor info based on industry
- **Peer insights**: "Other telecom companies struggle with X, want tips?"
- **Goal setting**: "What revenue/win-rate improvement are you targeting?"
