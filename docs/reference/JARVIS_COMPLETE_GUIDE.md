# JARVIS - Complete System Documentation

## Table of Contents
1. [Project Origin & Requirements](#1-project-origin--requirements)
2. [Architecture Deep Dive](#2-architecture-deep-dive)
3. [Component Specifications](#3-component-specifications)
4. [Communication & Data Flow](#4-communication--data-flow)
5. [Self-Evolution Mechanism](#5-self-evolution-mechanism)
6. [Persona & Deal Management](#6-persona--deal-management)
7. [Fireup Dynamic Adaptation](#7-fireup-dynamic-adaptation)
8. [MCP Autonomous Intelligence](#8-mcp-autonomous-intelligence)
9. [Safety & Approval System](#9-safety--approval-system)
10. [Implementation Details](#10-implementation-details)
11. [Deployment & Operations](#11-deployment--operations)
12. [API Reference](#12-api-reference)
13. [Testing Strategy](#13-testing-strategy)
14. [Troubleshooting Guide](#14-troubleshooting-guide)

> [!WARNING]
> **This 2000-line document is from an early design phase and contains extensive aspirational content** (Django/React skills, trust scores, A/B testing, schema migration, Docker deployment, etc.) that does not reflect the current system. For the current, accurate documentation, see:
> - [README.md](../../README.md) – Current system overview
> - [START_HERE.md](../getting-started/START_HERE.md) – Getting started guide
> - [Skills Overview](../skills/OVERVIEW.md) – All 15+ implemented skills
> - [Data Flow](../architecture/DATA_FLOW.md) – How the system actually works
>
> This file is preserved as a historical design reference only.

---

## 1. Project Origin & Requirements

### Original Request
Build an autonomous AI employee system (JARVIS) for OpenCode with these capabilities:
1. **Self-evolution and self-learning**
2. **Automatic detection of new folders/files and integration**
3. **Persona-based account/deal management**
4. **MCP autonomous intelligence**
5. **Dynamic fireup skill updates based on workspace contents**
6. **Complete system sync and orchestration**

### Key Requirements Derived
- Workspace scanner that detects all folders/files and categorizes them
- Meta-learning system that observes its own performance and improves
- Account/deal tracking per persona with manual + auto updates
- Enhanced MCP with sophisticated learning (beyond keywords)
- Self-modification capability for fireup and skills
- Comprehensive safety & backup systems
- Clear startup sequence: fireup → JARVIS init → MCP → observers → learners

### Design Principles Established
- **Safety First**: All modifications are backup-able and rollbackable
- **Progressive Enhancement**: Start conservative, increase autonomy with trust
- **Transparency**: Full audit logs, explainable decisions
- **Human-in-the-Loop**: Approval gates for high-risk operations
- **Modularity**: Components can be replaced/upgraded independently
- **Observability**: Comprehensive metrics and logs
- **Self-Limiting**: JARVIS knows its limits and asks for help when needed

---

## 2. Architecture Deep Dive

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         JARVIS CORE ENGINE                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │ Orchestrator│  │ Meta-Learner│  │ Safety Guard│  │ Sync Mgr    ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   OBSERVERS    │      │   LEARNERS     │      │   UPDATERS    │
├───────────────┤      ├───────────────┤      ├───────────────┤
│ • FileSys Obs │      │ • Pattern Rec │      │ • File Modder │
│ • DB Obs      │      │ • Pref Extr   │      │ • Code Gen    │
│ • Conv Obs    │      │ • Perf Analyzer│     │ • Config Updr │
│ • Git Obs     │      │ • Trend Detect│      │ • Schema Migr │
└───────────────┘      └───────────────┘      └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ACCOUNT & DEAL MANAGER                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │ Persona Mgr │  │ Deal Tracker│  │ History DB  │  │ Comm Log    ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MCP INTELLIGENCE LAYER                        │
│  • Context Understanding  • Autonomous Planning  • Skill Selection │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       WORKSACE SCANNER                             │
│  • Folder Categorization  • File Type Detection  • Integration    │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Interaction Patterns

**Event-Driven Architecture**:
- All components communicate via asynchronous message bus (EventBus)
- Publishers don't know subscribers - loose coupling
- Events are immutable and contain timestamp, source, correlation ID
- Components can subscribe to multiple event types

**Pipeline Pattern**:
```
Observer → Event → Learner → Suggestion → Updater → Execution
   ↓           ↓         ↓           ↓            ↓
File change  FILE_CREATED  Pattern  Modification  Modified file
detected                 recognized requested     completed
```

**Orchestration Pattern**:
- Orchestrator manages component lifecycles
- Handles startup/shutdown sequencing based on dependencies
- Schedules periodic tasks (scanning, learning, archiving)
- Monitors component health and triggers recovery

---

## 3. Component Specifications

### 3.1 Core Components (`core/`)

#### **Orchestrator** (`orchestrator.py`)
**Responsibilities**:
- Initialize all components in correct dependency order
- Start/stop lifecycle management
- Event routing based on event type
- Schedule periodic tasks (workspace scans, meta-learning, archiving)
- Component health monitoring and recovery

**Key Methods**:
- `initialize()`: Boot sequence following dependency graph
- `_start_schedulers()`: Launch async tasks with intervals
- `_execute_scheduled_task(task_name)`: Dispatch to handlers
- `shutdown()`: Graceful termination with state preservation

**Dependencies**: EventBus, Safety, SyncManager, all other components

#### **Meta-Learner** (`meta_learner.py`)
**Responsibilities**:
- Monitor JARVIS's own performance metrics
- Generate improvement hypotheses (what to change)
- A/B test changes in isolated environment
- Validate improvements before deployment
- Adjust learning parameters adaptively

**How It Works**:
1. Collect metrics: error rate, task completion time, user satisfaction, cost
2. Identify underperforming areas (>10% drop, baseline comparison)
3. Generate hypotheses (`{component: X, change: Y, expected: Z}`)
4. Test in sandbox with synthetic workload
5. If metrics improve enough (statistical significance), promote to production
6. Record effectiveness for future reference

**Example**:
```python
hypothesis = {
    "component": "pattern_recognition",
    "change": "lower_confidence_threshold",
    "from": 0.7,
    "to": 0.6,
    "expected": "+15% pattern discoveries",
    "risks": "+5% false positives"
}
# Test, measure, decide
```

#### **Safety Guard** (`safety.py`)
**Responsibilities**:
- Risk assessment for all modifications
- Approvals workflow (auto/PR/manual)
- Backup management and retention
- Impact analysis before execution
- Emergency kill switch monitoring

**Risk Assessment Factors**:
- File type (test/doc=low, refactor=med, schema=high, core=critical)
- Scope (1 file=low, module=med, multiple modules=high)
- Reversibility (additive=low, destructive=high)
- Historical failure rate for this action type

**Approval Logic**:
```python
risk_score = assess_risk(action)
persona_trust = get_trust_score(persona)

if risk_score == "low" and config.auto_approve_low_risk:
    allow_auto()
elif risk_score == "medium" or (risk_score == "high" and persona_trust > 0.8):
    create_pr_and_wait_for_ci()
else:
    require_human_approval_with_timeout(48h)
```

#### **Sync Manager** (`sync_manager.py`)
**Responsibilities**:
- Maintain consistency across distributed state
- Conflict resolution (last-write-wins, manual merge, persona priority)
- Transaction-like operations across multiple files
- Offline/online synchronization

---

### 3.2 Observers (`observers/`)

#### **FileSystem Observer** (`file_system.py`)
**Technology**: watchdog library (cross-platform)
**Monitors**:
- File creation, modification, deletion, movement
- Directory creation/deletion
- Attribute changes (permissions, timestamps)

**For each event**:
1. Filter by ignore patterns (`.git`, `node_modules`, `.jarvisignore`)
2. Extract metadata (size, type, encoding, shebang for scripts)
3. Categorize file (source, test, config, doc, data, asset)
4. Publish event with full context to message bus

**Example Event**:
```json
{
  "type": "file_created",
  "path": "/workspace/techcorp/src/payment.py",
  "size": 2048,
  "file_type": "python",
  "timestamp": "2025-03-18T14:32:10Z",
  "workspace_id": "techcorp_web"
}
```

#### **Git Observer** (`git.py`)
**Monitors**:
- Commits (message, author, changed files)
- Branches (create, delete, merge)
- Pull requests (open, update, merge, close)
- Tags and releases
- CI/CD status (GitHub Actions, Jenkins, etc.)

**Extracts**:
- Code review patterns (who reviews what)
- Commit frequency and times
- Merge vs rebase preferences
- Testing habits (do commits include tests?)
- Deployment triggers

#### **Conversation Observer** (`conversations.py`)
**Sources**:
- CLI interactions (jarvis commands)
- Chat interface logs (if API enabled)
- Email integration (if configured)
- Issue tracker comments (GitHub issues)

**Analyzes**:
- Sentiment (positive, negative, neutral)
- Task mentions ("need to fix", "please add")
- Deadline detection ("by Friday", "ASAP")
- Preference statements ("I prefer", "always do X")
- Corrections ("that's wrong", "actually it should")

#### **Database Observer** (`database.py`)
**Monitors**:
- Schema changes (ALTER TABLE, CREATE INDEX)
- Query execution times (slow queries)
- Connection pool statistics
- Migration scripts execution

**Use Cases**:
- Detect if schema change breaks application
- Suggest indexing for slow queries
- Learn typical query patterns for optimization

---

### 3.3 Learners (`learners/`)

#### **Pattern Recognition** (`pattern_recognition.py`)
**Goal**: Identify reusable code patterns

**Process**:
1. Parse files into AST (Abstract Syntax Tree)
2. Extract structural patterns (function signatures, class hierarchies, imports)
3. Cluster similar structures using embeddings
4. Assign pattern name and store in `data/patterns/`

**Example Discoveries**:
- "Django model with UUID primary key"
- "React component with useEffect cleanup"
- "Factory pattern for creating objects"
- "Configuration validator function"

**Storage Format**:
```json
{
  "pattern_id": "django_model_uuid_001",
  "name": "Django Model with UUID PK",
  "template": "class {name}(models.Model):\n    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)",
  "frequency": 15,
  "workspaces": ["techcorp", "beta_project"],
  "confidence": 0.92
}
```

#### **Preference Extractor** (`preference_extractor.py`)
**Learns From**:
- Code style from git blame (who wrote what)
- Configuration choices (black vs autopep8, pytest vs unittest)
- Framework selections (Django vs Flask, React vs Vue)
- Documentation habits (docstrings, README completeness)
- Testing practices (test location, naming, coverage)

**Builds Persona-Specific Preferences**:
```json
{
  "persona": "techcorp_team",
  "style": {
    "indentation": "spaces (4)",
    "max_line_length": 88,
    "import_ordering": "alphabetical"
  },
  "frameworks": {
    "backend": "django",
    "frontend": "react",
    "database": "postgresql"
  },
  "testing": {
    "framework": "pytest",
    "location": "tests/",
    "naming": "test_*.py"
  }
}
```

#### **Performance Analyzer** (`performance_analyzer.py`)
**Metrics Tracked**:
- Task completion time (from assignment to PR merge)
- Code review time (PR open → merge)
- Error rate (exceptions, test failures, CI failures)
- Resource usage (memory, CPU during builds)
- Cost (API calls, compute time)

**Analyzes**:
- Bottlenecks (which step takes longest?)
- Team performance trends (improving/declining?)
- Resource optimization opportunities
- Quality metrics (test coverage, lint errors)

#### **Trend Detector** (`trend_detector.py`)
**Scanning For**:
- New dependencies added to package.json/requirements.txt
- New frameworks/languages in workspace
- Deprecated library usage (via vulnerability databases)
- Emerging best practices (from tech blogs, GitHub trending)

**Signals Intelligence**:
- "Everyone is using FastAPI instead of Flask"
- "TypeScript adoption increasing"
- "pytest-xdist for parallel testing"
- "Moving from REST to GraphQL"

---

### 3.4 Updaters (`updaters/`)

#### **File Modder** (`file_modder.py`)
**Safety Features**:
- **Atomic operations**: Write to temp file → fsync → rename
- **Backup**: Preserve original in `.jarvis/backups/`
- **Format preservation**: Use Black/Prettier/lib2to3 to maintain style
- **Comment preservation**: Don't delete existing comments
- **Rollback**: Restore from backup on error

**Modification Types**:
- **Insert**: Add code at specific location (with context matching)
- **Replace**: Replace matching pattern with new code
- **Delete**: Remove code block (with backup)
- **Format**: Reformat without changing logic

**Example**:
```python
modder = FileModder()
modder.replace(
    file="settings.py",
    pattern=r'DEBUG\s*=\s*True',
    replacement='DEBUG = False',
    backup=True
)
```

#### **Code Generator** (`code_generator.py`)
**Generates**:
- Boilerplate: models, views, serializers, tests
- Configuration files: docker-compose.yml, nginx.conf, .env.example
- Documentation: README templates, API docs (from OpenAPI)
- Tests: pytest fixtures, mock data, assertion helpers

**Templates**: Jinja2-based with context variables
```jinja2
# {{ filename }}
"""
Purpose: {{ purpose }}
Author: {{ author }}
 created: {{ timestamp }}
"""

{% for import in imports %}
{{ import }}
{% endfor %}

class {{ class_name }}:
    """{{ docstring }}"""
    def __init__(self):
        pass
```

#### **Config Updater** (`config_updater.py`)
**Supported Files**:
- package.json (Node.js)
- requirements.txt, setup.py, pyproject.toml (Python)
- pom.xml (Java/Maven)
- build.gradle (Gradle)
- Dockerfile, docker-compose.yml
- .env.example
- CI/CD configs (.github/workflows, .gitlab-ci.yml)

**Operations**:
- Add dependency (with version constraint)
- Remove dependency (and update imports if needed)
- Update environment variable list
- Sync ports and connections between services

#### **Schema Migrator** (`schema_migrator.py`)
**Generates**:
- Migration scripts (Alembic for SQLAlchemy, Django migrations)
- Rollback scripts (inverse operation)
- Data transformation scripts

**Process**:
1. Compare current DB schema with desired state
2. Generate migration plan (add column, create index, etc.)
3. Write migration file with upgrade/downgrade
4. Test migration on copy of production DB
5. Deploy with backup and rollback ready

---

### 3.5 Persona & Deal Management (`persona/`)

#### **Persona Manager** (`persona_manager.py`)
**Manages Multiple Identities**:
- Separate configuration per persona
- Different preferences, learnings, and history
- Workspace-to-persona mapping
- Automatic persona switching based on current directory

**Persona Structure**:
```python
class Persona:
    id: str
    name: str
    description: str
    workspaces: List[Path]  # Directories belonging to this persona
    preferences: Dict      # Code style, frameworks, etc.
    learned_patterns: List  # Patterns specific to this persona
    knowledge_graph: KnowledgeGraph  # Domain concepts
    performance_history: List[PerformanceMetric]
    deals: List[Deal]
    trust_score: float     # 0.0 to 1.0
```

**Automatic Switching**:
```python
current_dir = Path.cwd()
for persona in personas:
    if current_dir in persona.workspaces or current_dir.is_relative_to(persona.workspaces):
        activate_persona(persona)
        break
```

#### **Deal Tracker** (`deal_tracker.py`)
**Deal Structure**:
```python
class Deal:
    id: str
    title: str
    client: str
    description: str
    deadline: datetime
    status: Literal["negotiation", "active", "on_hold", "completed", "cancelled"]
    budget: float
    currency: str
    tasks: List[Task]
    milestones: List[Milestone]
    stakeholders: List[Person]  # contacts
    communications: List[Communication]
```

**Auto-Updates From**:
- Git commits mentioning deal ID ("Fix for deal #123")
- Task completion events
- Manual status updates via CLI
- Calendar invites (meeting notes → update progress)
- Email parsing (if configured)

#### **History Database** (`history_db/`)
**SQLite Schema**:
```sql
CREATE TABLE actions (
    id TEXT PRIMARY KEY,
    timestamp DATETIME,
    persona_id TEXT,
    action_type TEXT,
    description TEXT,
    file_path TEXT,
    success BOOLEAN,
    duration_ms INTEGER,
    metadata JSON
);

CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    persona_id TEXT,
    metric_name TEXT,
    value REAL,
    tags JSON
);

CREATE TABLE patterns (
    id TEXT PRIMARY KEY,
    pattern TEXT,
    frequency INTEGER,
    first_seen DATETIME,
    last_seen DATETIME,
    confidence REAL,
    associated_workspace TEXT
);
```

---

### 3.6 Workspace Scanner (`scanner/`)

#### **Workspace Scanner** (`workspace_scanner.py`)
**Scanning Process**:
1. **Discovery**: Find all workspaces (directories with git repos, package.json, etc.)
2. **Classification**: Determine project type and technology stack
3. **Analysis**: Map structure (src/, tests/, docs/, config/)
4. **Integration**: Generate workspace manifest and register with system

**Project Type Detection**:
```python
def detect_project_type(path: Path) -> ProjectType:
    if (path / "package.json").exists():
        return ProjectType.NODE_JS
    if (path / "requirements.txt").exists() or (path / "setup.py").exists():
        return ProjectType.PYTHON
    if (path / "pom.xml").exists():
        return ProjectType.JAVA_MAVEN
    if (path / "build.gradle").exists():
        return ProjectType.JAVA_GRADLE
    if (path / "Cargo.toml").exists():
        return ProjectType.RUST
    if (path / "go.mod").exists():
        return ProjectType.GO
    # ... more
```

#### **Folder Categorizer** (`folder_categorizer.py`)
**Categorizes**:
- **src/source**: Application code
- **tests/**: Test files
- **docs/**: Documentation
- **config/**: Configuration files
- **scripts/**: Build/deploy scripts
- **data/**: Static assets, sample data
- **lib/vendor/**: Third-party code

#### **File Detector** (`file_detector.py`)
**Classifies Files**:
- Source code (.py, .js, .java, .go, .rs)
- Configuration (.json, .yaml, .toml, .ini, .env)
- Templates (.html, .jinja, .mustache)
- Styles (.css, .scss, .sass)
- Data (.csv, .json, .xml)
- Documentation (.md, .rst, .txt)
- Tests (test_*.py, *_test.js, spec/ directory)

---

### 3.7 MCP Intelligence Layer (`mcp/`)

#### **Context Engine** (`context_engine.py`)
**Beyond Keywords**:
- **Embeddings**: Convert code and queries to vector space using sentence-transformers
- **Semantic Search**: Find relevant code by meaning (not just text match)
- **Memory**: Persistent vector store (FAISS, ChromaDB) per persona
- **Context Window**: Dynamically manage size based on LLM context limits

**Example**:
Query: "How do we handle payment failures?"
- Not just searching "payment", "failure"
- Embedding understands webhook, retry, refund pattern
- Retrieves `payment_handler.py`, `retry_policy.py`, `webhook_receiver.js`

#### **Autonomous Planner** (`autonomous_planner.py`)
**Task Decomposition**:
Given: "Add Stripe payment integration"

1. **Research Phase**: 
   - Search existing payment code
   - Find Stripe docs in knowledge base
   - Identify similar integrations

2. **Planning Phase**:
   - Break down: setup account → install SDK → configure → implement webhook → test → deploy
   - Estimate complexity: medium
   - Select skills: `stripe_setup`, `dependency_adder`, `code_generator`, `test_writer`

3. **Execution Phase**:
   - Execute skill 1: Add Stripe to requirements.txt
   - Check success → if error, self-correct (maybe need API key)
   - Execute skill 2: Generate Stripe customer model
   - Execute skill 3: Create payment view
   - Execute skill 4: Add tests

4. **Completion Phase**:
   - Verify: existing tests pass, new tests added
   - Document: update README with Stripe setup steps
   - Report: "Completed Stripe integration. 4 files modified, 12 tests added."

#### **Skill Selector** (`skill_selector.py`)
**Skills Available**: (see `mcp/skills/`)
- Framework-specific: django_skills, react_skills, fastapi_skills
- Testing: pytest_skills, jest_skills, integration_testing
- Infrastructure: docker_skills, kubernetes_skills, terraform_skills
- Utilities: refactoring_skills, documentation_skills, security_scan

**Selection Process**:
```python
async def select_skills(task: Task, context: Context) -> List[Skill]:
    # 1. Get candidate skills from registry
    candidates = get_applicable_skills(task.tech_stack, task.action_type)
    
    # 2. Score each skill
    scores = []
    for skill in candidates:
        score = 0
        
        # Semantic similarity
        similarity = embedding_similarity(task.description, skill.description)
        score += similarity * 0.4
        
        # Historical success rate for this persona/project
        success_rate = get_success_rate(persona, skill.name)
        score += success_rate * 0.3
        
        # Relevance to context (files modified)
        context_overlap = len(set(skill.typical_files) & set(context.recent_files))
        score += context_overlap * 0.2
        
        # Resource cost penalty (prefer cheaper if similar score)
        cost = estimate_cost(skill)
        score -= cost * 0.1
        
        scores.append((skill, score))
    
    # 3. Rank and return top N
    scores.sort(key=lambda x: x[1], reverse=True)
    return [skill for skill, score in scores[:3]]
```

---

### 3.8 Fireup & Dynamic Adaptation (`fireup/`)

#### **Fireup** (`fireup.py`)
**Purpose**: Dynamic startup script that adapts to workspace

**Startup Sequence**:
```
1. Load configuration
2. Scan workspace (ORCHESTRATOR may have already done this)
3. Determine project types and tech stack
4. Select relevant skills from mcp/skills/
5. Build skill selection model with persona preferences
6. Initialize observers for this workspace
7. Start event processing
8. Report ready status
```

**Dynamic Skill Loading**:
```python
class Fireup:
    def __init__(self):
        self.loaded_skills = []
        self.workspace_profile = None
    
    async def initialize(self, workspace_path: Path):
        # 1. Scan workspace
        scanner = WorkspaceScanner()
        profile = await scanner.scan(workspace_path)
        self.workspace_profile = profile
        
        # 2. Select skills
        selector = SkillSelector()
        needed_skills = await selector.select_for_profile(profile)
        
        # 3. Load skills dynamically
        for skill_name in needed_skills:
            skill = self.load_skill(skill_name)
            self.loaded_skills.append(skill)
            logger.info(f"Loaded skill: {skill_name}")
        
        # 4. Update config for future
        self.update_fireup_config(profile, needed_skills)
    
    def load_skill(self, name: str) -> BaseSkill:
        # Dynamic import from mcp/skills/
        module = importlib.import_module(f"mcp.skills.{name}")
        return getattr(module, f"{name.title()}Skill")()
```

#### **Auto-Learning on New Files/Folders**
**When New File Detected**:
1. FileSystem Observer → EVENT: FILE_CREATED
2. Learner components:
   - PatternRecognition: Parse and extract structural patterns
   - PreferenceExtractor: Update style preferences based on content
   - TrendDetector: Check if it's a new technology/file type
3. Fireup updates:
   - If many new files of type X appear → load X-related skills
   - If file in new directory → add to workspace profile
   - Update skill registry effectiveness scores

**When New Folder Detected**:
1. Scanner categorizes folder (by contents)
2. Determine if it's a new project/module
3. If new project type (e.g., React Native added to Django backend):
   - Update workspace profile
   - Load additional skills (React Native skills)
   - Update persona preferences (cross-pollination if same persona)
4. IntegrationEngine creates necessary scaffolding

**Continuous Learning Loop**:
```
Detection → Categorization → Learning → Skill Update → Fireup Reconfig → Better Performance
```

---

### 3.9 Archive System (`archive/`)

#### **Date Archiver** (`date_archiver.py`)
**Schedule**:
- **Hourly**: Temporary backups (kept 24h)
- **Daily**: Full workspace snapshot (kept 30 days)
- **Weekly**: Weekly summary (kept 12 weeks)
- **Monthly**: Monthly archive (kept 24 months)
- **Yearly**: Yearly archive (kept 10 years)

**Compression**:
- Use gzip/brot2 for text (60-80% reduction)
- Use zip for mixed content
- Optional encryption (AES-256) for sensitive data

**Naming**:
```
archive_20250318_0200_daily.tar.gz
archive_202503_w12_weekly.tar.gz
archive_2025_03_monthly.tar.gz
```

#### **Category Archiver** (`category_archiver.py`)
**Categories**:
- By persona: `techcorp_team_20250318.tar.gz`
- By project: `ecommerce_backend_20250318.tar.gz`
- By task: `feature_stripe_integration_20250318.tar.gz`
- By milestone: `release_v1.2.0_20250318.tar.gz`

**Use Case**: "Show me all changes for TechCorp Inc last month" → extract from persona archives

---

## 4. Communication & Data Flow

### Event Bus (`utils/event_bus.py`)
**Implementation**: AsyncIO-based pub/sub

**Core API**:
```python
class EventBus:
    async def publish(event: Event)
    def subscribe(subscriber_id, event_types, callback)
    async def publish_async(event: Event)
    def get_stats() -> Dict
```

**Event Structure**:
```python
@dataclass
class Event:
    type: EventType           # Enum of all event types
    source: str              # Component that emitted (e.g., "observer.file_system")
    timestamp: datetime      # When event occurred
    data: Dict[str, Any]     # Payload (file_path, changes, etc.)
    correlation_id: Optional[str]  # Trace across components
    priority: int            # 1-5, higher = more urgent
```

**Example Flow**:
1. **File Created**:
   - Source: `observer.file_system`
   - Type: `FILE_CREATED`
   - Data: `{"path": "/app/models.py", "size": 1024, "workspace": "techcorp"}`
   - Subscribers: `learner.pattern_recognition`, `updater.file_modder`, `persona.comm_logger`

2. **Pattern Discovered**:
   - Source: `learner.pattern_recognition`
   - Type: `PATTERN_DISCOVERED`
   - Data: `{"pattern_id": "django_model_123", "files": ["models.py"], "confidence": 0.87}`
   - Subscribers: `persona.history_db`, `mcp.context_engine`

3. **Modification Completed**:
   - Source: `updater.file_modder`
   - Type: `MODIFICATION_COMPLETED`
   - Data: `{"change_id": "chg_456", "files": ["settings.py"], "success": true}`
   - Subscribers: `sync_manager`, `persona.deal_tracker`, `archive.archiver`

### Correlation IDs
For tracing a single operation across multiple events:
```
Correlation ID: "req_20250318_abc123"
→ File created event (corr: req_20250318_abc123)
→ Pattern learned (corr: req_20250318_abc123)
→ Modification proposed (corr: req_20250318_abc123)
→ Modification approved (corr: req_20250318_abc123)
→ Modification applied (corr: req_20250318_abc123)
→ Archive created (corr: req_20250318_abc123)
```

Allows complete audit trail of a single logical operation.

---

## 5. Self-Evolution Mechanism

### Evolution Triggers

#### Automatic Triggers
| Trigger | Condition | Action |
|---------|-----------|--------|
| Performance | 10% drop in key metric over 24h | Initiate investigation |
| Error Rate | >5% sustained error rate | Pause risky components |
| New Technology | Unknown framework detected | Research, learn, integrate |
| User Feedback | Negative sentiment clusters | Adjust behavior |
| Resource Cost | API spend > 2x baseline | Optimize calls |
| Schedule | Weekly deep analysis | Proactive improvements |

#### Manual Triggers
```bash
jarvis evolve --force                    # Force evolution now
jarvis learn --from <workspace>         # Learn from specific workspace
jarvis optimize --target perception     # Optimize specific component
jarvis meta --review                    # Review meta-learner's decisions
```

### Evolution Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│ 1. CAPTURE STATE                                            │
│    - Current component configs                              │
│    - Performance metrics (baseline)                         │
│    - Recent actions and outcomes                           │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. GENERATE HYPOTHESES                                      │
│    Meta-learner analyses:                                   │
│    - What component underperformed?                         │
│    - What changes could improve it?                         │
│    - Examples:                                              │
│      • "Pattern confidence too high → lower threshold"     │
│      • "Too many false positives → adjust filtering"       │
│      • "Slowness in file modder → batch changes"           │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. RISK ASSESSMENT                                          │
│    Safety Guard evaluates:                                  │
│    - Impact scope (files affected)                          │
│    - Reversibility                                          │
│    - Failure consequences                                   │
│    Risk Level: LOW / MEDIUM / HIGH / CRITICAL              │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. SANDBOX TESTING                                          │
│    For LOW & MEDIUM risk:                                   │
│    - Create isolated test workspace                        │
│    - Apply change                                          │
│    - Run synthetic workload                                │
│    - Measure against baseline                              │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 5. A/B TESTING (Optional)                                   │
│    For significant changes:                                 │
│    - Deploy to 10% of workspaces (canary)                  │
│    - Monitor for 24h                                       │
│    - Compare metrics with control group                    │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 6. METRICS EVALUATION                                       │
│    Success criteria:                                        │
│    - Target metric improved by X% (statistically sig)     │
│    - No regression in other metrics                        │
│    - Error rate did not increase                           │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 7. DEPLOYMENT                                               │
│    LOW risk: immediate rollout                             │
│    MEDIUM: gradual (10% → 50% → 100%)                      │
│    HIGH: require manual approval                           │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 8. UPDATE META-LEARNER                                      │
│    - Record effectiveness of this evolution                 │
│    - Adjust future hypothesis generation parameters        │
│    - Update trust models                                   │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 9. ARCHIVE OLD VERSION                                      │
│    - Keep previous config for rollback                     │
│    - Tag in git (if applicable)                            │
│    - Document change in changelog                          │
└──────────────────────────────────────────────────────────────┘
```

### Meta-Learner Example Implementation

```python
class MetaLearner:
    def __init__(self):
        self.performance_history = deque(maxlen=1000)
        self.evolution_history = []
        self.effectiveness_scores = {}  # {(component, change): score}
        
    async def analyze_and_evolve(self):
        """Main evolution loop"""
        metrics = self.collect_recent_metrics()
        
        # Detect anomalies
        anomalies = self.detect_anomalies(metrics)
        
        for anomaly in anomalies:
            # Generate hypotheses
            hypotheses = self.generate_hypotheses(anomaly)
            
            for hypothesis in hypotheses:
                # Check if we've tried similar before
                key = (hypothesis.component, hypothesis.change_type)
                if key in self.effectiveness_scores:
                    if self.effectiveness_scores[key] < 0.3:
                        logger.info(f"Skipping ineffective hypothesis: {hypothesis}")
                        continue
                
                # Test in sandbox
                success, new_metrics = await self.test_hypothesis(hypothesis)
                
                if success:
                    # Deploy to production
                    await self.deploy_change(hypothesis)
                    
                    # Record outcome
                    self.effectiveness_scores[key] = 0.8  # success
                    self.evolution_history.append({
                        "timestamp": datetime.utcnow(),
                        "hypothesis": hypothesis,
                        "metrics_before": metrics,
                        "metrics_after": new_metrics,
                        "deployed": True
                    })
                else:
                    self.effectiveness_scores[key] = 0.1  # failure
    
    def generate_hypotheses(self, anomaly: Anomaly) -> List[Hypothesis]:
        """Generate potential fixes for detected problem"""
        hypotheses = []
        
        if anomaly.component == "pattern_recognition" and anomaly.metric == "false_positive_rate":
            hypotheses.append(Hypothesis(
                component="pattern_recognition",
                change="adjust_confidence_threshold",
                params={"threshold_delta": -0.05},
                expected_effect="Reduce false positives by 20%"
            ))
            hypotheses.append(Hypothesis(
                component="pattern_recognition",
                change="add_blacklist_patterns",
                params={},
                expected_effect="Reduce noise from common patterns"
            ))
        
        # More hypothesis generation rules...
        return hypotheses
```

---

## 6. Persona & Deal Management

### Persona System

#### Concept
A **Persona** represents a distinct identity for a client, project, or team. Each persona has:
- Separate knowledge base
- Unique preferences and learned patterns
- Own workspace assignments
- Isolated history and performance metrics

#### Use Cases
1. **Multiple Clients**: TechCorp Inc vs Beta Inc - separate codebases, styles, preferences
2. **Internal vs External**: Different behavior for internal projects vs client work
3. **Personal vs Professional**: Separate "learning" vs "production" personas
4. **Sandbox vs Production**: Conservative in production, experimental in sandbox

#### Creating a Persona
```bash
jarvis persona create \
  --name "TechCorp Inc" \
  --description "E-commerce platform development" \
  --workspace "/path/to/techcorp" \
  --preferences '{"code_style": "black", "framework": "django"}'
```

Or via config:
```json
{
  "personas": [
    {
      "id": "techcorp_inc",
      "name": "TechCorp Inc Dev Team",
      "workspaces": ["/projects/techcorp-*"],
      "preferences": {
        "languages": ["python", "javascript"],
        "style_guide": "pep8",
        "testing": "pytest",
        "documentation": "sphinx"
      },
      "trust_score": 0.85,
      "stakeholders": ["dev-team@techcorp.com"]
    }
  ]
}
```

#### Automatic Persona Switching
```python
def detect_persona(path: Path) -> Optional[Persona]:
    """Detect which persona owns this workspace"""
    current = Path.cwd()
    
    # Check all personas
    for persona in persona_manager.list_personas():
        for workspace in persona.workspaces:
            workspace_path = Path(workspace)
            if current == workspace_path or current.is_relative_to(workspace_path):
                return persona
    
    # No match → use default persona
    return persona_manager.get_default_persona()
```

### Deal Tracking

#### Deal Structure
```python
@dataclass
class Deal:
    id: str
    title: str
    client: str
    description: str
    value: float  # Budget or contract value
    currency: str = "USD"
    start_date: datetime
    deadline: datetime
    status: DealStatus
    progress: float  # 0.0 to 1.0
    
    # Related entities
    tasks: List[Task]
    milestones: List[Milestone]
    team: List[Persona]  # Which personas working on this
    
    # Tracking
    time_spent: float  # hours
    costs_incurred: float
    communications: List[Communication]
```

#### Auto-Proposal from Conversations
When conversation contains:
- "We need to build a new checkout by April 15"
- "Budget is around $20k"
- "Client is TechCorp Inc"

→ Auto-create deal:
```json
{
  "title": "New Checkout System",
  "client": "TechCorp Inc",
  "description": "Build a new checkout system",
  "value": 20000,
  "deadline": "2026-04-15",
  "status": "proposal"
}
```

And send for confirmation:
```
Detected potential deal: "New Checkout System"
Client: TechCorp Inc
Deadline: April 15, 2026
Value: $20,000

Should I create this deal? (yes/no/ edit):
```

#### Progress Tracking
- **Manual**: User updates via `jarvis deal update <id> --progress 0.5`
- **Automatic**: From git commits containing deal ID, task completion
- **Inferred**: From time spent (tracked via observer), files modified

---

## 7. Fireup Dynamic Adaptation

### What is Fireup?
**Fireup** is the startup script that boots JARVIS with the right skills for the current workspace.

### Traditional vs Dynamic

**Traditional (Static)**:
```python
# fireup.py - hard-coded
SKILLS = [
    "django_skills",
    "react_skills",
    "testing_skills"
]
# Always loads these, even if not needed
```

**Dynamic (JARVIS)**:
```python
# fireup.py - generates itself!
SKILLS = auto_detected_skills  # Based on actual workspace contents

# If new folder "mobile_app" added:
# → fireup.py updates itself to include "react_native_skills"
# → next startup loads mobile skills automatically
```

### How Fireup Adapts

#### Phase 1: Initial Scan
```python
async def scan_workspace(workspace_path: Path) -> WorkspaceProfile:
    profile = WorkspaceProfile()
    
    # Detect project types
    if (workspace_path / "package.json").exists():
        profile.tech_stack.append("nodejs")
    if (workspace_path / "manage.py").exists():
        profile.tech_stack.append("django")
    
    # Count file types
    python_files = list(workspace_path.rglob("*.py"))
    if len(python_files) > 10:
        profile.languages.append("python")
    
    # Check for specific frameworks
    if any("tensorflow" in f.read_text() for f in python_files[:10]):
        profile.frameworks.append("tensorflow")
    
    return profile
```

#### Phase 2: Skill Selection
```python
def select_skills(profile: WorkspaceProfile, persona: Persona) -> List[str]:
    skill_registry = load_skill_registry()  # From mcp/skills/
    
    selected = []
    
    # Match tech stack
    for tech in profile.tech_stack:
        for skill in skill_registry:
            if tech in skill.applicable_tech:
                selected.append(skill.name)
    
    # Consider persona preferences
    for framework in persona.preferences.frameworks:
        for skill in skill_registry:
            if framework in skill.applicable_tech and skill.name not in selected:
                selected.append(skill.name)
    
    # Add generic skills always
    selected.extend(["code_generation", "testing", "documentation"])
    
    return list(set(selected))  # Deduplicate
```

#### Phase 3: Self-Modification
Fireup can update its own configuration:
```python
def update_fireup_config(profile: WorkspaceProfile, skills: List[str]):
    """Write updated config for next startup"""
    config = {
        "workspace_profile": profile.to_dict(),
        "loaded_skills": skills,
        "last_updated": datetime.utcnow().isoformat(),
        "version": "2.0"
    }
    
    with open("fireup_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    # Also update the fireup.py script itself if needed
    # (This is the self-modification capability!)
    if needs_skill_reload(profile):
        generate_new_fireup_script(skills)
```

### Real-Time Adaptation (Hot Reload)
When new folder/file added while JARVIS running:

1. **Observer detects** → Event: `NEW_WORKSPACE_DETECTED`
2. **Scanner categorizes** → Updates workspace profile
3. **Learner analyzes** → Determines if new skills needed
4. **Fireup notified** → `fireup.reload_skills_if_needed(new_profile)`
5. **Dynamic loading**: `importlib.import_module()` new skill
6. **No restart needed** - hot-swap skills!

---

## 8. MCP Autonomous Intelligence

### What is MCP?
**M**odel **C**ontext **P**rotocol - Enhanced intelligence layer that understands context and makes autonomous decisions.

### Key Enhancements Over Basic MCP

#### 1. Semantic Understanding (Not Just Keywords)
**Old Way**: Search for "payment" → finds string "payment"
**JARVIS Way**: Search for "how to handle failed payments" → finds:
- `payment_webhook_handler.py` (handles retries)
- `refund_policy.py` (refunds for failed payments)
- `error_backoff.py` (exponential backoff logic)

**How**: Sentence embeddings (all-MiniLM-L6-v2) create vector representations.

#### 2. Autonomous Planning
Given high-level task, breaks into steps:
```
Task: "Add authentication to API"

Plan:
1. Research: Check if any auth exists (search codebase)
2. Choose: Which auth method? JWT, OAuth, API keys?
3. Install: Add dependencies (djangorestframework-simplejwt)
4. Configure: settings.py AUTHENTICATION_CLASSES
5. Implement: Create UserSerializer, RegisterView, LoginView
6. Protect: Add permission classes to existing views
7. Test: Write auth tests (test_auth.py)
8. Document: Update README with auth instructions
```

#### 3. Skill Orchestration
Each step picks best skill:
```python
for step in plan:
    skills = skill_selector.select(step, context)
    
    for skill in skills:
        try:
            result = await skill.execute(step.context)
            if result.success:
                step.mark_complete()
                break
        except SkillError as e:
            logger.warning(f"Skill {skill.name} failed: {e}")
            continue  # Try next skill
    
    if not step.complete:
        raise PlanningError(f"All skills failed for step: {step}")
```

#### 4. Cross-Workspace Learning
Persona "techcorp" has done Stripe integration:
- Learned patterns: create customer, handle webhook, record transaction
- Success rate: 95%

When same persona works on new project needing payments:
- MCP retrieves Stripe integration pattern from knowledge graph
- Suggests similar approach
- Adapts to new project's structure

### MCP Runtime

```python
class MCPIntelligence:
    def __init__(self, persona: Persona):
        self.persona = persona
        self.context_engine = ContextEngine(persona)
        self.planner = AutonomousPlanner()
        self.skill_selector = SkillSelector()
        self.knowledge_graph = KnowledgeGraph(persona)
        self.execution_history = []
    
    async def execute_task(self, task_description: str, workspace: Path):
        """Full autonomous execution"""
        
        # 1. Build context
        context = await self.context_engine.build(
            task=task_description,
            workspace=workspace,
            persona=self.persona
        )
        
        # 2. Plan
        plan = await self.planner.plan(task_description, context)
        logger.info(f"Plan created with {len(plan.steps)} steps")
        
        # 3. Execute with monitoring
        for step in plan.steps:
            # Select skills for this step
            skills = await self.skill_selector.select(step, context)
            
            # Try skills in order
            step_complete = False
            for skill in skills:
                try:
                    result = await skill.execute(step, context)
                    
                    if result.success:
                        step_complete = True
                        context.update(result.artifacts)
                        self.execution_history.append({
                            "step": step,
                            "skill": skill.name,
                            "result": result,
                            "timestamp": datetime.utcnow()
                        })
                        break
                    else:
                        logger.warning(f"Skill {skill.name} failed: {result.error}")
                except Exception as e:
                    logger.error(f"Skill execution exception: {e}")
            
            if not step_complete:
                # All skills failed → need human intervention
                await self.request_human_help(step)
                return ExecutionResult(success=False, needs_human=True)
        
        # 4. Verify
        verification = await self.verify_completion(plan, context)
        
        # 5. Learn from this execution
        await self.learn_from_execution(plan, verification)
        
        return ExecutionResult(success=True, artifacts=verification.artifacts)
```

---

## 9. Safety & Approval System

### Multi-Layer Safety

#### Layer 1: Prevention
- **Syntax Checking**: Before modifying, parse to ensure valid syntax
- **Type Checking**: mypy/pyright for Python, TypeScript compiler for TS
- **Import Validation**: Ensure new imports exist and don't create circular deps
- **Security Scanning**: Detect secrets, vulnerabilities, unsafe patterns

#### Layer 2: Approval Workflow
```python
class ApprovalWorkflow:
    def __init__(self, safety_config: SafetyConfig):
        self.config = safety_config
    
    async def request_approval(self, action: Action, risk_level: RiskLevel, 
                             persona: Persona, impact: ImpactAnalysis) -> ApprovalResult:
        
        # Determine required approval level
        if risk_level == RiskLevel.LOW and self.config.auto_approve_low_risk:
            return ApprovalResult(approved=True, method="auto")
        
        if risk_level == RiskLevel.MEDIUM:
            if persona.trust_score > 0.8:
                # High trust → auto-approve medium
                return ApprovalResult(approved=True, method="auto_high_trust")
            else:
                # Create PR
                pr_url = await self.create_pull_request(action, impact)
                return ApprovalResult(approved=None, method="pr", pr_url=pr_url)
        
        if risk_level == RiskLevel.HIGH:
            if persona.trust_score > 0.9:
                # Trusted client → quick approval
                msg = await self.send_quick_approval_request(persona, action, impact)
                return ApprovalResult(approved=None, method="quick_approval", message=msg)
            else:
                # Full manual review
                msg = await self.send_detailed_approval_request(persona, action, impact)
                return ApprovalResult(approved=None, method="manual", message=msg)
        
        if risk_level == RiskLevel.CRITICAL:
            # Two-person approval required
            return ApprovalResult(approved=None, method="two_person")
```

#### Layer 3: Backup & Rollback
```python
@contextmanager
def backup_and_rollback(file_path: Path):
    """Context manager for safe file modification"""
    backup_path = create_backup(file_path)
    original_content = file_path.read_text()
    
    try:
        yield  # Perform modification
    except Exception as e:
        logger.error(f"Modification failed, rolling back: {e}")
        file_path.write_text(original_content)
        restore_from_backup(backup_path)
        raise
    finally:
        # Keep backup for 10 days, then auto-delete
        schedule_backup_deletion(backup_path, days=10)
```

#### Layer 4: Kill Switch
```python
class KillSwitch:
    def __init__(self, switch_file: str = ".jarvis.killswitch"):
        self.switch_file = Path(switch_file)
        self.check_interval = 10  # seconds
    
    async def monitor(self):
        """Continuously check for kill switch file"""
        while True:
            if self.switch_file.exists():
                logger.warning("Kill switch activated! Pausing all operations.")
                orchestate.pause_all()
                
                # Wait for removal
                while self.switch_file.exists():
                    await asyncio.sleep(5)
                
                logger.info("Kill switch removed. Resuming operations.")
                orchestrator.resume_all()
            
            await asyncio.sleep(self.check_interval)
```

#### Layer 5: Audit Trail
All actions logged to immutable store:
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    component TEXT,
    action TEXT,
    persona_id TEXT,
    file_path TEXT,
    change_hash TEXT,
    approval_status TEXT,
    approved_by TEXT,
    correlation_id TEXT,
    metadata JSON
);
```

---

## 10. Implementation Details

### Technology Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| Language | Python 3.9+ | Rich ecosystem, async support |
| Async | asyncio | Native Python async, no external dependencies |
| Event Bus | Custom (asyncio.Queue) | Lightweight, no Redis needed |
| Database | SQLite | Simple, serverless, good for single-machine |
| Vector Store | ChromaDB / FAISS | Semantic search for MCP |
| Embeddings | sentence-transformers | Local, no API cost |
| File Watching | watchdog | Cross-platform (inotify/FSEvents/ReadDirectoryChangesW) |
| Code Parsing | ast (Python), tree-sitter (multi-lang) | Structural analysis |
| Testing | pytest, pytest-asyncio | Async test support |
| API | FastAPI (optional) | Auto-generated docs, async |
| Deployment | systemd, Docker | Production options |

### Key Design Patterns Used

1. **Observer Pattern**: Observers watch for changes
2. **Publish-Subscribe**: Event bus decouples components
3. **Strategy Pattern**: Pluggable skills, updaters, learners
4. **Factory Pattern**: Component loading from config
5. **Singleton**: EventBus, Config (one instance)
6. **Context Manager**: Backup/restore, transactions
7. **Pipeline**: Observer → Learner → Updater
8. **Chain of Responsibility**: Skill selection, approval chain

### Error Handling Strategy

```python
async def safe_execute(component, func, *args, **kwargs):
    """Wrapper for safe component execution"""
    try:
        result = await func(*args, **kwargs)
        component.record_success()
        return result
    except TransientError as e:
        # Temporary failure, retry with backoff
        logger.warning(f"Transient error in {component}: {e}")
        await asyncio.sleep(backoff(component.retry_count))
        component.retry_count += 1
        if component.retry_count < 3:
            return await safe_execute(component, func, *args, **kwargs)
        else:
            raise
    except PermanentError as e:
        # Permanent failure, escalate
        logger.error(f"Permanent error in {component}: {e}")
        await safety_guard.handle_permanent_failure(component, e)
        raise
    except Exception as e:
        # Unknown error, log and escalate
        logger.exception(f"Unexpected error in {component}")
        await safety_guard.handle_unknown_error(component, e)
        raise
```

---

## 11. Deployment & Operations

### Quick Start
```bash
# 1. Install
git clone https://github.com/yourorg/jarvis.git
cd jarvis
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Initialize
jarvis init

# 3. Configure personas
jarvis persona create --name "My Project" --workspace /path/to/project

# 4. Start
jarvis start

# 5. Check status
jarvis status
```

### Systemd Service
Create `/etc/systemd/system/jarvis.service`:
```ini
[Unit]
Description=JARVIS Autonomous AI Employee
After=network.target

[Service]
Type=simple
User=jarvis
WorkingDirectory=/opt/jarvis
Environment="PATH=/opt/jarvis/.venv/bin"
ExecStart=/opt/jarvis/.venv/bin/jarvis start --foreground
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable jarvis
sudo systemctl start jarvis
sudo systemctl status jarvis
```

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 jarvis
USER jarvis

CMD ["jarvis", "start", "--foreground"]
```

```bash
docker build -t jarvis .
docker run -d \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/workspaces:/workspaces \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --name jarvis \
  jarvis
```

### Monitoring

#### Metrics Exposed
```bash
jarvis metrics
```

Output:
```
=== JARVIS Metrics ===
Uptime: 5d 12h 34m
Components:
  - orchestrator: healthy (last heartbeat: 2s ago)
  - file_system_observer: healthy (files watched: 1,247)
  - meta_learner: healthy (evolutions: 12)
  - safety_guard: healthy (actions approved: 342, rejected: 12)

Performance:
  - Events processed/sec: 15.3
  - Files modified today: 24
  - Patterns learned: 156
  - Skills used: 23
  - Avg task completion time: 2.3h
  - Cost today: $1.47 (API calls: 3,247)

Personas:
  - techcorp_inc (trust: 0.87): 12 active tasks
  - beta_inc (trust: 0.72): 5 active tasks
```

#### Logs
```bash
# Structured JSON logs
tail -f logs/jarvis.log | jq .

# Errors only
tail -f logs/errors/error_*.log

# Performance metrics
tail -f logs/performance/metrics_*.log
```

#### Health Check Endpoint (if API enabled)
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "uptime": 456789,
  "components": {
    "orchestrator": "healthy",
    "observers": "healthy",
    "learners": "healthy"
  },
  "metrics": {
    "memory_mb": 234,
    "cpu_percent": 12.3
  }
}
```

---

## 12. API Reference

### REST API (Optional)

#### Authentication
```bash
# Use API key or JWT
Authorization: Bearer <token>
```

#### Endpoints

**GET /** - Health check
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime": 123456
}
```

**GET /status** - Detailed status
```json
{
  "orchestrator": {"state": "running", "uptime": 123456},
  "components": [...],
  "metrics": {...}
}
```

**GET /personas** - List personas
```json
[
  {"id": "techcorp", "name": "TechCorp Inc", "workspaces": 2},
  {"id": "beta", "name": "Beta Inc", "workspaces": 1}
]
```

**POST /personas/{id}/switch** - Switch active persona
```bash
curl -X POST http://localhost:8000/personas/techcorp/switch
```

**GET /metrics** - Performance metrics
```json
{
  "tasks_completed": 1234,
  "files_modified": 567,
  "patterns_learned": 89,
  "api_calls_today": 12345,
  "cost_today": 2.34
}
```

**GET /archive** - List archives
```json
[
  {"date": "2025-03-18", "type": "daily", "size_mb": 45},
  {"date": "2025-03-11", "type": "weekly", "size_mb": 320}
]
```

**POST /archive/restore** - Restore from archive
```bash
curl -X POST http://localhost:8000/archive/restore \
  -H "Content-Type: application/json" \
  -d '{"archive_id": "2025-03-18_daily", "target_path": "/workspace"}'
```

**GET /approvals/pending** - List pending approvals
```json
[
  {
    "id": "req_123",
    "action": "modify_database",
    "risk_level": "high",
    "impact": ["db/schema.sql", "models/user.py"],
    "correlation_id": "corr_456"
  }
]
```

**POST /approvals/{id}/approve** - Approve action
```bash
curl -X POST http://localhost:8000/approvals/req_123/approve
```

**WebSocket** `/ws/events` - Real-time event stream
```javascript
const ws = new WebSocket("ws://localhost:8000/ws/events");
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Event: ${data.type} from ${data.source}`);
};
```

---

## 13. Testing Strategy

### Unit Tests
Test each component in isolation with mocks:

```python
# tests/unit/learners/test_pattern_recognition.py
def test_extract_function_pattern():
    code = """
def create_user(username, email):
    user = User(username=username, email=email)
    user.save()
    return user
"""
    learner = PatternRecognition()
    pattern = learner.extract_pattern(code)
    
    assert pattern.type == "function_definition"
    assert pattern.name == "create_user"
    assert len(pattern.parameters) == 2
```

### Integration Tests
Test component interactions:

```python
# tests/integration/test_full_cycle.py
@pytest.mark.asyncio
async def test_file_created_to_modification():
    # 1. Create test workspace
    workspace = create_test_workspace()
    
    # 2. Start JARVIS with test config
    jarvis = await start_test_jarvis(workspace)
    
    # 3. Simulate file creation
    test_file = workspace / "models.py"
    test_file.write_text("# TODO: add User model")
    
    # 4. Wait for processing
    await asyncio.sleep(2)
    
    # 5. Check that pattern was learned
    patterns = await jarvis.learner.get_patterns()
    assert any("model" in p.name for p in patterns)
    
    # 6. Check that modification was suggested/executed
    actions = await jarvis.history.get_recent_actions()
    assert any("TODO" in a.description for a in actions)
```

### Self-Evolution Tests
```python
# tests/integration/test_self_evolution.py
def test_meta_learner_can_improve_system():
    # Introduce a bug/inneficiency
    # Run meta-learning cycle
    # Verify that improvement was proposed and applied
    # Verify metrics improved
    pass
```

### Load Tests
Simulate 100 workspaces, 10,000 files, high event rate.

---

## 14. Troubleshooting Guide

### Common Issues

#### "JARVIS won't start"
**Symptoms**: `jarvis start` hangs or exits immediately

**Diagnosis**:
```bash
# Check config syntax
jarvis config validate

# Check logs
tail -n 50 logs/jarvis.log | jq .

# Test event bus
python -c "from utils.event_bus import EventBus; print('OK')"
```

**Solutions**:
- Ensure all directories exist: `mkdir -p data/{personas,patterns,skills,history,archives,cache} logs`
- Check file permissions: `chmod -R 755 data/ logs/`
- Validate Python dependencies: `pip install -e ".[dev]"`

#### "High error rate in file modifications"
**Symptoms**: Many `MODIFICATION_FAILED` events, rollbacks frequent

**Diagnosis**:
```bash
# Find failing files
grep "MODIFICATION_FAILED" logs/jarvis.log | jq '.file_path' | sort | uniq -c | sort -nr

# Check pattern quality
jarvis patterns list --min_confidence 0.5
```

**Solutions**:
- Update patterns manually or let meta-leaner adjust
- Increase confidence threshold: `jarvis config set learner.confidence_threshold 0.8`
- Exclude problematic directories: add to `.jarvisignore`

#### "Memory leak"
**Symptoms**: Memory usage grows steadily

**Diagnosis**:
```bash
# Monitor memory
ps aux | grep jarvis

# Check cache sizes
du -sh data/cache/
```

**Solutions**:
- Restart JARVIS (graceful shutdown preserves state)
- Reduce cache retention: `jarvis config set mcp.cache_embeddings false`
- Run garbage collection: `jarvis admin gc`

#### "MCP not selecting correct skills"
**Symptoms**: JARVIS uses wrong tools for task

**Diagnosis**:
```bash
# View skill selection history
jarvis skills history

# Check skill effectiveness scores
jarvis skills rankings
```

**Solutions**:
- Manually adjust skill weights: `jarvis skills weight <skill_name> +0.1`
- Provide more training examples: `jarvis learn --from /path/to/example_project`
- Reset skill rankings: `jarvis skills reset`

---

## Appendix: Quick Reference

### CLI Command Summary
```bash
# System
jarvis start/stop/restart/status
jarvis init              # First-time setup
jarvis config show/edit/validate
jarvis evolve            # Trigger self-evolution

# Workspaces
jarvis scan [path]       # Scan workspace
jarvis workspaces list   # Show all known workspaces
jarvis workspace add /path/to/project

# Personas
jarvis persona list
jarvis persona create --name "TechCorp" --workspace /techcorp
jarvis persona switch techcorp   # Manual switch
jarvis persona show <id>

# Deals
jarvis deal list
jarvis deal create --title "Project X" --deadline "2026-04-01"
jarvis deal update <id> --progress 0.75

# Monitoring
jarvis metrics           # Show metrics
jarvis logs [--tail]     # View logs
jarvis events [--follow] # Live event stream

# Maintenance
jarvis archive create --name "pre-deploy"
jarvis archive list
jarvis archive restore <id>
jarvis admin backup      # Manual backup
jarvis admin restore     # Restore from backup
jarvis admin gc          # Garbage collection
```

### Configuration Files
- `jarvis_config.json` - Main configuration
- `fireup_config.json` - Dynamically updated by scanner
- `data/personas/*.json` - Persona definitions
- `data/patterns/*.json` - Learned code patterns
- `data/skills/skill_registry.json` - Available skills metadata
- `.jarvisignore` - Files/dirs to ignore (like .gitignore)
- `.jarvis.killswitch` - Emergency stop (touch to pause)

### Directories
- `data/` - All persistent data (backed up)
- `logs/` - Structured logs (rotated)
- `.jarvis/` - Workspace-specific metadata (backups, caches)

### Event Types Reference
See `utils/event_bus.py` for complete list.

---

## Conclusion

JARVIS is designed as a **self-sustaining, self-improving AI employee** that:
- **Observes** everything in your workspaces
- **Learns** patterns, preferences, and best practices
- **Acts** autonomously with safety guards
- **Evolves** its own algorithms over time
- **Adapts** to different personas and projects
- **Reports** progress and metrics transparently

It's like having a senior developer, DevOps engineer, and project manager rolled into one, working 24/7 to keep your codebase clean, up-to-date, and following best practices.

The key innovation is the **feedback loop**: JARVIS watches itself, learns from successes and failures, and continuously improves—just like a human employee would, but with machine-scale memory and processing.

**Ready to deploy?** See `docs/deployment.md` for production setup.
