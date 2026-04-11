# JARVIS Validation Guide — Prove It Works

> **For sales people who want to verify JARVIS works before committing to it.**

---

## Pre-Flight Checks

Before running validation, verify:

✅ Python 3.9+ installed
✅ `python install.py` completed successfully
✅ `.env` file has NVIDIA API key (`NVIDIA_API_KEY=nvapi-...`)
✅ Claude Desktop is restarted (or Claude Code is open with JARVIS folder)
✅ ACCOUNTS folder exists at `~/JARVIS/ACCOUNTS/`

---

## Quick Validation (5 Minutes)

### Test 1: Create Account
**What it proves:** JARVIS can scaffold account folders

In Claude, run:
```
"Create test account TestCorp.
Target market: Mid-market.
ARR goal: $150k.
Competing with Competitor1."
```

**Check:**
- ✅ `~/JARVIS/ACCOUNTS/TestCorp/` folder created
- ✅ Contains: `deal_stage.json`, `discovery.md`, `company_research.md`, `CLAUDE.md`
- ✅ Files have correct content (not empty)

**Result:** ✅ Account scaffolding works

---

### Test 2: Get Account Summary
**What it proves:** JARVIS can read deal files and generate context

In Claude, run:
```
"Get account summary for TestCorp"
```

**Check:**
- ✅ Claude reads the account files
- ✅ Shows deal stage, ARR, stakeholders
- ✅ Summary is non-generic (references your account data)
- ✅ Suggests next actions

**Example response:**
```
TESTCORP — Account Summary
Stage: Discovery
ARR: $150k
Health: AMBER (early stage, many unknowns)
Target Market: Mid-market

Stakeholders: [from deal_stage.json]
- Account: TestCorp
- Stage: discovery

MEDDPICC Signals: Minimal (need more discovery)
Next Action: Schedule discovery call to gather MEDDPICC signals
```

**Result:** ✅ Context detection works

---

### Test 3: Extract Intelligence
**What it proves:** JARVIS can parse natural language and extract deal signals

In Claude, paste:
```
"Update TestCorp: 
I called today with John Smith, VP Operations.
He said: 'We spend $200k/year on 3 different solutions, 
but need something unified. They're evaluating us, 
Competitor1, and Competitor2. 
Need decision by end of Q2.
Security is critical — they're ISO 27001 certified.'"
```

**Check:**
- ✅ Claude extracts MEDDPICC signals:
  - **M** (Metrics): $200k spend identified
  - **I** (Implications): Fragmentation pain identified
  - **D** (Decision Criteria): ISO 27001 requirement
  - **D** (Decision Process): End of Q2 timeline
  - **C** (Competition): Competitor1, Competitor2 identified
- ✅ `discovery.md` updated with timestamped note
- ✅ Claude suggests next action

**Result:** ✅ Intelligence extraction works

---

### Test 4: Run MEDDPICC Scoring
**What it proves:** JARVIS can analyze all 8 dimensions and provide actionable guidance

In Claude, run:
```
"Score MEDDPICC for TestCorp"
```

**Check:**
- ✅ Output scores all 8 dimensions:
  - **M**etrics: Status + Evidence
  - **E**conomic Buyer: Status + Evidence
  - **D**ecision Criteria: Status + Evidence
  - **D**ecision Process: Status + Evidence
  - **P**aper Process: Status + Evidence
  - **I**mplications/Pain: Status + Evidence
  - **C**hampion: Status + Evidence
  - **C**ompetition: Status + Evidence
- ✅ Each has RED/AMBER/GREEN status
- ✅ Shows evidence (references actual things you said)
- ✅ Identifies biggest gaps
- ✅ File saved to `meddpicc.md`

**Example output:**
```
TESTCORP — MEDDPICC Scoring

M — Metrics: AMBER
  Evidence: $200k annual spend identified
  Gap: Need to confirm ROI expectations

E — Economic Buyer: RED
  Evidence: Only talked to VP Operations
  Gap: Need to identify CFO/finance buyer

D — Decision Criteria: AMBER
  Evidence: ISO 27001 critical (security requirement)
  Gap: Need complete evaluation criteria

...

Top 3 Gaps to Close:
1. Get CFO/economic buyer engaged (RED)
2. Get complete evaluation criteria (AMBER)
3. Confirm decision timeline (AMBER)
```

**Result:** ✅ MEDDPICC analysis works

---

### Test 5: Get Risk Report
**What it proves:** JARVIS can assess deal health and identify risks

In Claude, run:
```
"Risk report for TestCorp"
```

**Check:**
- ✅ Overall health assessed: RED/AMBER/GREEN
- ✅ Lists specific risks with evidence
- ✅ Severity levels assigned
- ✅ Mitigation recommendations provided
- ✅ Next 3 actions listed

**Example output:**
```
TESTCORP — Risk Assessment

Overall Health: AMBER (moderate risk)

Risks:
1. [RED] No economic buyer engaged
   Impact: Can't close without CFO approval
   Mitigation: Get VP Ops to intro CFO this week

2. [AMBER] Competing with 2 solutions
   Impact: May lose on features or price
   Mitigation: Run competitive battlecard

3. [AMBER] Decision timeline tight (end of Q2)
   Impact: 8 weeks to close, limited time
   Mitigation: Accelerate evaluation, demo next week

Top 3 Actions:
1. Schedule CFO meeting (URGENT)
2. Run competitive analysis (HIGH)
3. Prepare ROI model (HIGH)
```

**Result:** ✅ Risk analysis works

---

## Full Workflow Test (20 Minutes)

### Scenario: Real-World Deal

Create an account mimicking your actual deal:

**Step 1: Create Account**
```
"Create account RealDeal.
They're a 1000-person SaaS company.
Evaluating us for their enterprise product.
Budget is $500k.
Timeline is aggressive: 60 days.
Currently using OldSolution1 and OldSolution2."
```

**Step 2: Add Discovery Notes**
```
"Update RealDeal with these notes from discovery call:
- Spoke with Susan Lee, Director of Product
- Pain: Takes 3 weeks to do things that should take 1 week
- Using 2 solutions that don't talk to each other
- Budget approved by CFO ($500k annual)
- Need demo for executive team next week
- Evaluating us and Competitor1
- Security requirement: SOC2 Type 2
- Go-live needed by Q3 (90 days)"
```

**Step 3: Run Full Analysis**
```
"Give me full analysis for RealDeal:
1. MEDDPICC score
2. Risk report
3. Battlecard vs Competitor1
4. Demo strategy for executive team"
```

**Check Each Output:**

✅ **MEDDPICC** shows all 8 dimensions with evidence from your notes  
✅ **Risk report** identifies real risks (timeline, competition, security)  
✅ **Battlecard** shows your edge vs Competitor1  
✅ **Demo strategy** tailored to executive concerns  

**All outputs should:**
- Reference specific things you said (Susan Lee, 3 weeks, SOC2, etc.)
- Not be generic (use your deal data)
- Provide actionable next steps

**Result:** ✅ Full workflow works end-to-end

---

## Success Metrics

After validation, you should see:

| Metric | Target | Check |
|--------|--------|-------|
| Account creation | < 30 sec | ✅ |
| MEDDPICC scoring | < 60 sec | ✅ |
| Context accuracy | 100% (references your data) | ✅ |
| Risk identification | Identifies real deal threats | ✅ |
| Actionability | Provides next steps | ✅ |
| Output quality | Better than templates | ✅ |

---

## Troubleshooting Validation

### Issue: "Account not created"
**Solution:** Check that `python install.py` completed. Check `~/JARVIS/ACCOUNTS/` exists.

### Issue: "Claude doesn't recognize the account"
**Solution:** Make sure account folder name matches what you told Claude (exact spelling). Restart Claude Desktop if in Claude Desktop.

### Issue: "MEDDPICC output is generic"
**Solution:** Make sure you provided deal data. Generic output means Claude isn't reading your account files. Check files exist and have content.

### Issue: "API key errors"
**Solution:** 
1. Check `.env` has `NVIDIA_API_KEY=nvapi-...`
2. Check key is valid (go to build.nvidia.com, verify it exists)
3. Add more keys if rate-limited:
   ```
   NVIDIA_API_KEY=nvapi-key1
   NVIDIA_API_KEY_2=nvapi-key2
   ```

### Issue: "Claude Code doesn't detect JARVIS"
**Solution:**
- Make sure you opened the project root folder (contains install.py)
- Make sure `.claude/CLAUDE.md` exists
- Restart Claude Code

---

## What Success Looks Like

After running validation, you should feel:

✅ **Confident** — JARVIS understands my deals  
✅ **Impressed** — Outputs are way better than templates  
✅ **Excited** — I can see how much time this saves  
✅ **Ready** — This will actually help me close deals  

If you don't feel these things, there's a problem. Report it.

---

## Go/No-Go Decision

After validation, ask yourself:

1. **Does JARVIS understand my deals?** → YES / NO
2. **Are the outputs better than templates?** → YES / NO
3. **Would this actually save me time?** → YES / NO
4. **Am I confident it works?** → YES / NO

If **all YES**: Deploy to your real pipeline. You're ready.

If **any NO**: Something is wrong. Check troubleshooting above or contact support.

---

## Next Steps

Once validated:

1. **Rename your test accounts** to real deal names (or delete them)
2. **Create your actual pipeline** in ACCOUNTS/
3. **Use Claude Code or Desktop** for your real deals
4. **Run skills on every call** (MEDDPICC, risk report, meeting prep)
5. **Track time saved** — you'll be surprised how much

---

## Support

If validation fails:
- Check README.md
- Check FINAL_DELIVERY.md
- Verify setup with: `python install.py` (run again)
- Restart Claude (close and reopen)

JARVIS should work. If it doesn't, there's a fixable problem.
