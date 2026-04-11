# Self-Evolution - Truly Autonomous Learning

JARVIS learns from every interaction and automatically evolves CLAUDE.md settings.

## How It Works

### Automatic Tracking
Every time you use a skill:
```
User: @jarvis discovery for Acme

JARVIS Records:
- Skill: discovery
- Quality: 4.8/5
- Timestamp: 2026-04-01T20:30:00
- Metadata: Saved to .claude_metadata.json
```

This happens **automatically, no action needed**.

### Pattern Analysis
Every 5 interactions, JARVIS analyzes patterns:

```
Interactions tracked: 5
- discovery used: 4 times
- Average quality: 4.8/5
- Consistency: 80%

Pattern detected: High-quality, consistent skill usage
```

This happens **automatically, no action needed**.

### Auto-Apply to CLAUDE.md
When patterns are detected, JARVIS **automatically updates** CLAUDE.md:

```markdown
## Learned Preferences
- **discovery**: text (quality: 4.8/5)

## Learned Enhancements
- **discovery**: Auto-enabled (used 4 times)
```

This happens **automatically, no approval needed**.

## Real Example

### Timeline

**Interaction 1:** User calls discovery skill for Acme
```
Quality: 4.8/5
Record: ✓
```

**Interaction 2:** User calls discovery skill again  
```
Quality: 4.9/5
Record: ✓
```

**Interaction 3:** User calls discovery skill again
```
Quality: 4.7/5
Record: ✓
```

**Interaction 4:** User calls battlecard skill
```
Quality: 4.5/5
Record: ✓
```

**Interaction 5:** User calls discovery skill again
```
Quality: 4.9/5
Record: ✓

ANALYSIS TRIGGERED (5 interactions completed)
✓ Analyzed patterns
✓ Found: discovery = 4 uses, 4.8 avg quality
✓ AUTO-UPDATED CLAUDE.md with learned preferences
```

**Interaction 6 onwards:** User benefits from learned preferences automatically

---

## What Gets Learned

### Model Preferences
If you consistently use a skill with high quality:
```
LEARNED: discovery → Use text model (4.8/5 quality)
APPLIED: Automatically to CLAUDE.md
EFFECT: Future discovery calls use learned preference
```

### Skill Enablement
If you use a skill multiple times successfully:
```
LEARNED: discovery is high-quality (4 uses, 4.8/5)
APPLIED: Auto-enabled in Learned Enhancements
EFFECT: Claude recommends it for relevant contexts
```

### Optimization Patterns
If certain skills are used together:
```
LEARNED: discovery + battlecard combo = high success
APPLIED: Suggested workflow optimization
EFFECT: Better recommendations for deal workflows
```

---

## How It's Stored

### Metadata File
Location: `~/ACCOUNTS/[AccountName]/.claude_metadata.json`

```json
{
  "version": "1.0",
  "interactions": [
    {
      "timestamp": "2026-04-01T20:30:00",
      "skill": "discovery",
      "model_type": "text",
      "quality": 4.8,
      "feedback": ""
    }
  ],
  "learned_preferences": [
    "discovery: text (4.8/5)"
  ]
}
```

### CLAUDE.md Updates
Location: `~/ACCOUNTS/[AccountName]/CLAUDE.md`

Automatically adds sections:

```markdown
## Learned Preferences
Auto-learned from interaction patterns.
- **discovery**: text (quality: 4.8/5)

## Learned Enhancements
Auto-discovered optimizations.
- **discovery**: Auto-enabled (used 4 times)
```

---

## The Complete Cycle

```
User Action
    ↓
Interaction Tracked (automatic)
    ↓
Every 5 interactions:
    ├─ Analyze patterns (automatic)
    ├─ Detect high-quality skills (automatic)
    ├─ Identify consistent usage (automatic)
    └─ Update CLAUDE.md (automatic, NO APPROVAL)
    ↓
Benefits Applied Immediately
    ↓
Next interactions use learned preferences
```

**No user approval needed. No clicks. No configuration. Just automatic evolution.**

---

## Examples of Learning

### Example 1: Successful Skill Discovery
```
You use "discovery" skill 5 times with 4.8+ quality

System learns: This is your best skill
System does: Auto-enables it in CLAUDE.md
Result: Claude prioritizes discovery for this account
```

### Example 2: Model Preference Learning
```
You use "proposal" skill 4 times with Sonnet model
Results: 4.7 quality consistently

System learns: Sonnet is best for proposals
System does: Records in Learned Preferences
Result: Next proposals automatically use Sonnet
```

### Example 3: Workflow Pattern Learning
```
You use: discovery → battlecard → proposal (sequence)
Results: 4.8+ quality each time

System learns: This workflow is effective
System does: Suggests workflow optimization
Result: Claude recommends this sequence for future deals
```

---

## Safety & Control

### Automatic But Safe
- Only applies to CLAUDE.md (config file)
- Never changes account data (deal_stage.json, discovery.md)
- Never changes core code
- Changes are always reversible (edit CLAUDE.md manually)

### Override Anytime
If you disagree with learned preference:
```
Manual edit CLAUDE.md:
- Remove "## Learned Preferences" section
- Or edit specific preferences

Next evolution will learn new patterns
```

### View Learning Progress
```
@jarvis interaction_summary

Returns:
- Total interactions tracked
- Average quality scores
- Skills learned
- Preferences applied
```

---

## Why Autonomous?

You wanted: "Self-doing everything automatically"

Self-Evolution delivers:
- ✅ Tracks automatically (no config)
- ✅ Analyzes automatically (no manual review)
- ✅ Applies automatically (no approval)
- ✅ Improves over time (no intervention)
- ✅ Transparent (view .claude_metadata.json anytime)

No approval needed. No clicks. No friction. Just automatic improvement.

---

## In Production

Self-Evolution is **enabled by default** and:
- ✓ Runs automatically
- ✓ Learns from every interaction
- ✓ Applies improvements immediately
- ✓ Never requires user action
- ✓ Always improvable (manual edits override learned settings)

**Your JARVIS system gets smarter with every use.**
