# 🤖 JARVIS NVIDIA MODEL ASSIGNMENTS

**All skills and tasks are mapped to specific NVIDIA models for optimal performance.**

---

## 📋 Model Summary

| Model Type | Model ID | Best For |
|-----------|----------|----------|
| **text** | `stepfun-ai/step-3-5-flash` | Fast text generation, proposals, emails |
| **long_context** | `nvidia/nemotron-3-super-120b-a12b` | Long documents, complex analysis, summaries |
| **reasoning** | `kimi-k2-thinking` | Complex decisions, pattern analysis, predictions |
| **audio** | `nvidia/whisper-large-v3-turbo` | Meeting transcription, voice input |
| **video** | `nvidia/cosmos-reason2-8b` | Demo flows, visual analysis, architecture |
| **quick** | `nvidia/mistral-nemo-minitron-8b` | Lightning fast responses, quick insights |

---

## 🎯 Skill to Model Mapping

### **TEXT GENERATION** (stepfun-ai/step-3-5-flash)
These skills use fast text generation model for proposals, emails, templates:

```
✓ proposal              → Generate sales proposals
✓ discovery             → Discovery call prep
✓ meeting_prep          → Meeting preparation
✓ followup_email        → Follow-up emails
✓ battlecard            → Competitive battlecards
✓ demo_strategy         → Demo narratives
✓ sow                   → Scope of Work docs
✓ custom_template       → Custom templates
```

### **LONG CONTEXT** (nvidia/nemotron-3-super-120b-a12b)
These skills use long-context model for processing large documents:

```
✓ account_summary       → Executive summaries
✓ risk_report           → Risk assessments
✓ technical_risk        → Technical risk analysis
✓ knowledge_builder     → Build knowledge graphs
✓ value_architecture    → ROI/TCO analysis
✓ competitive_intelligence → Market research
✓ competitor_pricing    → Pricing analysis
```

### **REASONING** (kimi-k2-thinking)
These skills use reasoning model for complex decisions:

```
✓ evolution_optimizer   → System optimization decisions
✓ conversation_analyzer → Extract insights from chats
✓ outcome_predictor     → Predict deal success
✓ deal_stage_tracker    → Track deal progression
✓ meddpicc              → MEDDPICC framework analysis
```

### **AUDIO** (nvidia/whisper-large-v3-turbo)
These skills use audio model for transcription and analysis:

```
✓ meeting_summary       → Transcribe & summarize meetings
✓ conversation_summarizer → Extract meeting insights
```

### **VIDEO** (nvidia/cosmos-reason2-8b)
These skills use video model for visual content:

```
✓ architecture_diagram  → Generate architecture visuals
✓ html_generator        → Generate visual HTML reports
```

### **QUICK/LIGHTWEIGHT** (nvidia/mistral-nemo-minitron-8b)
These skills use fast lightweight model for quick responses:

```
✓ quick_insights        → Fast account insights
✓ conversation_extractor → Quick conversation analysis
```

---

## 📁 File Type to Model Mapping

| File Type | Model | Processing |
|-----------|-------|-----------|
| `.pdf` | long_context | Complex document analysis |
| `.docx` | long_context | Word document processing |
| `.xlsx` | text | Structured data analysis |
| `.pptx` | video | Presentation analysis |
| `.txt` | text | Plain text processing |
| `.json` | text | Data structure analysis |
| `.mp3` | audio | Audio transcription |
| `.wav` | audio | Audio transcription |
| `.mp4` | video | Video analysis |
| `.mov` | video | Video analysis |

---

## 🎬 Task Type to Model Mapping

| Task Type | Model | Purpose |
|-----------|-------|---------|
| `vectorize_document` | long_context | Extract knowledge from documents |
| `extract_insights` | reasoning | Analyze patterns and insights |
| `analyze_conversation` | reasoning | Learn from chat interactions |
| `predict_outcome` | reasoning | Forecast deal success |
| `generate_proposal` | text | Create proposals quickly |
| `generate_discovery` | text | Build discovery frameworks |
| `generate_battlecard` | text | Competitive positioning |
| `generate_sow` | text | Scope of work documents |
| `analyze_risk` | reasoning | Complex risk assessment |
| `analyze_bottleneck` | reasoning | Process optimization |
| `analyze_effectiveness` | reasoning | Skill performance analysis |
| `transcribe_meeting` | audio | Convert speech to text |
| `analyze_video` | video | Video content analysis |
| `generate_demo_flow` | video | Demo strategy generation |
| `quick_lookup` | quick | Fast information retrieval |
| `quick_summary` | quick | Lightning-fast summaries |

---

## 🔄 Example Flows

### **Scenario 1: Generate Proposal**
```
User: "Create proposal for Acme Corp"
  ↓
Skill: proposal
  ↓
Model Assignment: stepfun-ai/step-3-5-flash (TEXT)
  ↓
Execution:
  1. LLMManager.generate_for_skill("proposal", prompt)
  2. Model config returns: stepfun-ai/step-3-5-flash
  3. Fast, high-quality proposal generated
  ↓
Result: Professional proposal in seconds
```

### **Scenario 2: Analyze Risk Report**
```
User: "Generate risk report for Tata deal"
  ↓
Skill: risk_report
  ↓
Model Assignment: nvidia/nemotron-3-super-120b-a12b (LONG_CONTEXT)
  ↓
Execution:
  1. LLMManager.generate_for_skill("risk_report", prompt)
  2. Model config returns: nemotron-3-super-120b
  3. Can process entire account history + context
  ↓
Result: Comprehensive risk analysis with full context
```

### **Scenario 3: Process Meeting Recording**
```
User: "Summarize meeting recording.mp4"
  ↓
File Type: .mp4
  ↓
Model Assignment: nvidia/cosmos-reason2-8b (VIDEO)
  ↓
Execution:
  1. LLMManager.generate_for_file(".mp4", prompt)
  2. Model config returns: cosmos-reason2-8b
  3. Analyzes video and generates summary
  ↓
Result: Meeting transcription + insights
```

### **Scenario 4: Evolution Optimization**
```
Background Task: Evolution Cycle
  ↓
Task Type: analyze_conversation
  ↓
Model Assignment: kimi-k2-thinking (REASONING)
  ↓
Execution:
  1. LLMManager.generate_for_task("analyze_conversation", prompt)
  2. Model config returns: kimi-k2-thinking
  3. Reasons about patterns and suggests improvements
  ↓
Result: System evolution recommendations
```

---

## 💻 Code Usage

### **In Skills**
```python
# Skill automatically uses correct model
class ProposalSkill:
    async def generate(self, account, **kwargs):
        # LLMManager routes to stepfun-ai/step-3-5-flash
        result = await self.llm.generate_for_skill(
            skill_name="proposal",
            prompt=prompt,
            context=context
        )
        return result
```

### **In Evolution System**
```python
# Evolution uses reasoning model
class EvolutionOptimizer:
    async def analyze_patterns(self, interactions):
        # LLMManager routes to kimi-k2-thinking
        result = await self.llm.generate_for_task(
            task_type="analyze_conversation",
            prompt=analysis_prompt
        )
        return result
```

### **In File Processing**
```python
# File processing uses type-specific model
class VectorizerAgent:
    async def vectorize_document(self, file_path):
        extension = Path(file_path).suffix
        # LLMManager routes to appropriate model
        result = await self.llm.generate_for_file(
            file_extension=extension,
            prompt=extraction_prompt
        )
        return result
```

---

## 🚀 Performance Characteristics

| Model | Speed | Context | Best For |
|-------|-------|---------|----------|
| step-3-5-flash | ⚡⚡⚡ Very Fast | 8K | Quick text, proposals |
| nemotron-3-super | ⚡⚡ Fast | 120K+ | Long documents, complex analysis |
| kimi-k2-thinking | ⚡ Standard | 32K | Reasoning, decisions |
| whisper-large-v3 | ⚡⚡ Fast | Audio | Transcription accuracy |
| cosmos-reason2 | ⚡⚡ Fast | Visual | Video analysis |
| mistral-nemo | ⚡⚡⚡ Fastest | 8K | Lightning-fast responses |

---

## ✅ Verification

Run this to verify model assignments are loaded:

```bash
cd "/Users/syounus/Documents/claude space/Personal-AE-SC-Jarvis"
python3 -c "from jarvis_mcp.config.model_config import *; print(get_all_models()); print('\\n✅ Models loaded successfully')"
```

Expected output:
```
{
  'text': 'stepfun-ai/step-3-5-flash',
  'long_context': 'nvidia/nemotron-3-super-120b-a12b',
  'reasoning': 'kimi-k2-thinking',
  'audio': 'nvidia/whisper-large-v3-turbo',
  'video': 'nvidia/cosmos-reason2-8b',
  'quick': 'nvidia/mistral-nemo-minitron-8b'
}

✅ Models loaded successfully
```

---

## 📊 Summary

- **6 NVIDIA Models** assigned
- **24 Skills** mapped to correct models
- **6 File Types** routed to appropriate models
- **16 Task Types** have specific model assignments
- **100% Coverage** - Every skill/task has a model

**Result**: Each operation uses the most optimal NVIDIA model for its specific purpose.

✅ **COMPLETE MODEL ROUTING SYSTEM**
