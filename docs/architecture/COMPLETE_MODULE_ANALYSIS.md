# OPENCODE FIREUP SKILL - Complete Analysis

> **Note:** This document includes both legacy MCP concepts and newer JARVIS components. For the up-to-date system architecture and component list, see `CURRENT_ARCHITECTURE.md`. The modules described here are conceptual; the actual implementation includes additional components (AccountAutoInitializer, Tool Executor, meta-learning enhancements).

## What Is This?

**OPENCODE_FIREUP_SKILL.md** was an early experimentation file about creating a custom MCP skill for OpenCode. It contained a skill implementation for detecting open code instances.

**Is it important?** 
- **For JARVIS core**: NOT ESSENTIAL - the system works without it
- **As a reference example**: VERY USEFUL - shows how to create custom skills
- **For OpenCode integration**: POTENTIALLY USEFUL if integrating JARVIS with OpenCode editor

**Decision**: Keep it as an **example skill** in documentation, but it's not part of the core JARVIS runtime.

---

## Complete JARVIS System: End-to-End Module Analysis

### Philosophy
JARVIS = Autonomous AI Employee that:
1. **Observes** everything (files, git, chat)
2. **Learns** patterns, preferences, trends
3. **Plans** multi-step tasks intelligently
4. **Acts** safely with backup/rollback
5. **Improves** itself continuously

All through **event-driven architecture** where components don't call each other directly—they publish/subscribe to events.

---

## MODULE 1: EVENT BUS (utils/event_bus.py)

### What It Does
The **communication backbone** - all components talk through it.

### How It Works
```python
class EventBus:
    async def publish(event: Event):
        # Put event in async queue
        self._queue.put(event)
    
    def subscribe(subscriber_id, event_types, callback):
        # Register callback for specific event types
        for event_type in event_types:
            self._subscribers[event_type].append(callback)
    
    async def _process_events():
        # Background task that dispatches events to subscribers
        while running:
            event = await queue.get()
            for callback in subscribers[event.type]:
                await callback(event)
```

### Example Flow
```
FileSystemObserver: "New file created: models.py"
    → event_bus.publish(FILE_CREATED, {path: "models.py"})
    ↓ EventBus dispatches to all subscribers
PatternRecognition: receives FILE_CREATED → "This is a Django model!"
MCP: receives FILE_CREATED → "New model, might need API endpoint"
Persona: receives FILE_CREATED → "Log activity for TechCorp persona"
```

### Why It's Critical
- **Loose coupling**: Components don't know about each other
- **Extensible**: Add new component, just subscribe to events
- **Fault tolerant**: One component fails, others keep working
- **Observable**: All events can be logged and replayed
- **Async**: Non-blocking, high performance

---

## MODULE 2: LOGGER (utils/logger.py)

### What It Does
Structured JSON logging for all components.

### How It Works
```python
logger = get_logger(__name__)
logger.info("File modified", 
    file="models.py",
    persona="techcorp",
    correlation_id="req_123"
)
# Output: {"timestamp":"...", "level":"INFO", "logger":"...", 
#          "message":"File modified", "file":"models.py", ...}
```

### Features
- JSON format (machine-parseable)
- Multiple handlers: console (colored), file (rotating)
- Structured fields: component, correlation_id, persona
- Different log files: jarvis.log (all), errors/ (errors only), performance/ (metrics)

### Why It's Critical
- **Debugging**: See what happened, when, with context
- **Audit trail**: Every action logged with who/what/when
- **Monitoring**: Can feed logs to ELK/Datadog
- **Correlation**: Use correlation_id to trace single request across all components

---

## MODULE 3: CONFIG (utils/config.py)

### What It Does
Centralized configuration with environment overrides.

### How It Works
```python
# Load from file + environment
config = Config.load()

# Use anywhere
if config.safety.auto_approve_low_risk:
    # Auto-approve docs changes
    pass

# Can override with env vars
# JARVIS_SAFETY_AUTO_APPROVE_LOW_RISK=false jarvis start
```

### Features
- Load from JSON file
- Override with environment variables (for Docker/K8s)
- Nested config sections (safety, observer, learner, etc.)
- Validation and defaults
- Save back to file

### Why It's Critical
- **Single source of truth**: All settings in one place
- **Environment aware**: Dev vs prod vs staging
- **Runtime changes**: Can adjust thresholds without code change
- **Observability**: Logging of config changes

---

## MODULE 4: ORCHESTRATOR (core/orchestrator.py)

### What It Does
**Central coordinator** - manages lifecycle of all components.

### How It Works
```python
class Orchestrator:
    async def initialize():
        # 1. Start event bus
        await event_bus.start()
        
        # 2. Initialize components in dependency order
        await self._initialize_components()
        
        # 3. Start schedulers (periodic tasks)
        await self._start_schedulers()
        
        # 4. Initial workspace scan
        await self._trigger_initial_scan()
        
        self.state = RUNNING
    
    async def _start_schedulers():
        # Schedule periodic tasks
        self._tasks.append(
            asyncio.create_task(self._run_scheduled_task("workspace_scan", 300))
        )
        # Runs every 5 minutes
    
    def get_status(self):
        # Return health of all components
        return {"state": "running", "components": {...}}
```

### Schedules
- workspace_scan: every 5 minutes
- performance_analysis: every hour
- meta_learning: every 6 hours
- archive_snapshot: daily at 2 AM
- health_check: every minute

### Why It's Critical
- **Single source of truth** for system state
- **Lifecycle management**: starts/stops components in correct order
- **Scheduling**: Periodic tasks (scans, backups, learning cycles)
- **Health monitoring**: Watches component heartbeats, restarts if needed
- **Event routing**: Can add centralized routing logic

---

## MODULE 5: FIREUP (fireup/fireup.py) - THE KEY TRIGGER

### What It Does
**Dynamic startup and skill management** - the autonomous trigger.

### How It Works

#### Step 1: Scan Workspace
```python
async def initialize(workspace_path):
    profile = await scanner.scan(workspace_path)
    # profile = {
    #   tech_stack: ["django", "react", "postgresql"],
    #   frameworks: {"backend": "django"},
    #   common_patterns: ["django_model", "react_component"],
    #   file_counts: {"python": 45, "js": 23}
    # }
```

#### Step 2: Determine Skills
```python
def _determine_required_skills(profile, persona):
    required = set()
    
    # Always load core
    required.update(["file_modder", "code_generator"])
    
    # Tech-based
    for tech in profile.tech_stack:
        skills = registry.get_skills_for_tech([tech])
        required.update([s.name for s in skills if s.auto_load])
    
    # Persona preferences
    if persona.preferences.skills:
        required.update(persona.preferences.skills)
    
    # Pattern-based (if workspace shows Dockerfiles, load docker skills)
    for pattern in profile.common_patterns:
        skill = self._pattern_to_skill(pattern)
        if skill:
            required.add(skill)
    
    return sorted(required, key=lambda s: registry.get_skill(s).priority)
```

#### Step 3: Load Skills Dynamically
```python
async def _load_skills(skill_names):
    for skill_name in skill_names:
        await registry.load_skill(skill_name)
        self.loaded_skills.append(skill_name)
```

Dynamic loading uses `importlib`:
```python
module = importlib.import_module(f"mcp.skills.{skill_name}")
skill_class = getattr(module, f"{skill_name.title()}Skill")
instance = skill_class()
self.loaded_instances[skill_name] = instance
```

#### Step 4: Self-Modification (Write Own Config!)
```python
def _update_fireup_config(self):
    config = {
        "workspace": str(self.current_workspace),
        "persona": self.current_persona.id,
        "profile": self.current_profile.to_dict(),  # What it learned
        "loaded_skills": self.loaded_skills,        # What it decided
        "last_updated": datetime.utcnow().isoformat()
    }
    with open("fireup_config.json", "w") as f:
        json.dump(config, f, indent=2)
```

#### Step 5: Hot-Reload on Changes
```python
async def reload_for_workspace_change(event):
    # New folder/file added
    new_profile = await scanner.scan(self.current_workspace)
    
    if new_profile.tech_stack != old_profile.tech_stack:
        # Tech changed! Load new skills
        new_skills = determine_skills(new_profile)
        await load_skills(new_skills)  # Hot-reload!
        self._update_fireup_config()
```

#### Step 6: Generate Workspace-Specific Code
```python
def _generate_dynamic_skills_file():
    # Creates auto_generated.py with workspace-specific helpers
    content = f'''
    class WorkspaceSpecificSkills:
        workspace = "{self.current_workspace}"
        patterns = {json.dumps(self.current_profile.common_patterns)}
        
        @staticmethod
        def get_skill_for_pattern(pattern):
            skill_map = {{
                "django_model": "django_skills.DjangoSkills",
                ...
            }}
            return skill_map.get(pattern)
    '''
    with open("fireup/dynamic_skills/auto_generated.py", "w") as f:
        f.write(content)
```

### Why Fireup Is THE KEY

**Without Fireup**:
- Manual config: "jarvis needs these skills listed in config file"
- Manual updates: Add React Native? Edit config, restart JARVIS
- Static: Can't adapt to new project types

**With Fireup**:
- Auto-detection: Scans workspace, knows what's needed
- Self-configuration: Writes its own config based on analysis
- Hot-reload: New tech → new skills load automatically
- Adaptive: Different workspace = different skill set

**Example**:
```
You: cd /my-django-project
    → Fireup detects Django → loads django_skills

You: Add mobile_app/ folder with React Native
    → FileObserver sees it
    → Fireup rescans, detects React Native
    → Loads react_native_skills automatically
    → No restart, no config edit!

You: Create Stripe integration
    → MCP uses django_skills (already loaded)
    → Success

You: cd /my-flask-project
    → Fireup switches persona, detects Flask
    → Unloads django_skills, loads flask_skills
    → Now "create API" uses Flask, not Django
```

**Impact**: JARVIS truly autonomous - adapts to your project without configuration.

---

## MODULE 6: OBSERVERS (jarvis/observers/)

### What They Do
**Detect changes** in the world and publish events.

### Types

#### FileSystemObserver
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileSystemHandler(FileSystemEventHandler):
    def on_created(self, event):
        # New file or directory
        self.event_bus.publish(FILE_CREATED, {
            "path": event.src_path,
            "is_directory": event.is_directory,
            "timestamp": datetime.utcnow()
        })
    
    def on_modified(self, event):
        self.event_bus.publish(FILE_MODIFIED, {...})
    
    def on_deleted(self, event):
        self.event_bus.publish(FILE_DELETED, {...})
```

**Why critical**: JARVIS needs to see what you're doing to learn and help.

#### GitObserver
```python
import git

class GitObserver:
    def monitor_repo(self, repo_path):
        repo = git.Repo(repo_path)
        # Poll or use git hooks
        for commit in repo.iter_commits():
            self.event_bus.publish(GIT_COMMIT, {
                "hash": commit.hexsha,
                "message": commit.message,
                "author": commit.author.name,
                "files_changed": commit.stats.files
            })
```

**Why critical**: Tracks progress, learns from code reviews, sees task completion.

#### ConversationObserver
```python
class ConversationObserver:
    # Monitors CLI commands, chat interfaces, emails
    def on_user_message(self, message):
        # NLP: extract intent, entities, sentiment
        analysis = nlp.analyze(message)
        # "Add authentication by Friday" → 
        #   intent: "add_feature", entity: "authentication", deadline: "Friday"
        self.event_bus.publish(USER_FEEDBACK, analysis)
```

**Why critical**: Learns preferences, detects deals (deadlines, budgets), understands requirements.

---

## MODULE 7: LEARNERS (jarvis/learners/)

### What They Do
**Analyze events** and extract knowledge.

### Types

#### PatternRecognition
```python
class PatternRecognition:
    async def learn_from_file(self, filepath: Path):
        # Parse code into AST
        if filepath.suffix == ".py":
            tree = ast.parse(filepath.read_text())
            
            # Extract patterns
            patterns = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    pattern = {
                        "type": "class_definition",
                        "name": node.name,
                        "bases": [base.id for base in node.bases],
                        "decorators": [d.func.id for d in node.decorator_list],
                        "line_count": len(node.body)
                    }
                    patterns.append(pattern)
            
            # Cluster similar patterns
            clustered = self.cluster_patterns(patterns)
            
            # Store if frequent enough
            for pattern in clustered:
                if pattern.frequency >= config.pattern_min_frequency:
                    self.store_pattern(pattern)
                    self.event_bus.publish(PATTERN_DISCOVERED, pattern)
```

**Example**: Sees 5 Django models with `id = models.UUIDField(primary_key=True)` → learns "django_model_uuid" pattern → next time you create model, can suggest this pattern.

#### PreferenceExtractor
```python
class PreferenceExtractor:
    def learn_from_git_history(self, persona_id):
        # Use git blame to see who wrote what
        for file in persona_workspace.rglob("*.py"):
            blame = git.Repo().blame('HEAD', file)
            for author, lines in blame:
                if author == persona.primary_developer:
                    # Analyze their style
                    if uses_black_formatting(lines):
                        persona.preferences.formatter = "black"
                    if has_docstrings(lines):
                        persona.preferences.docstring_style = "google"
        
        self.event_bus.publish(PREFERENCE_UPDATED, {...})
```

**Learns**: Formatter (Black vs autopep8), testing framework, docstring style, naming conventions, framework preferences.

#### PerformanceAnalyzer
```python
class PerformanceAnalyzer:
    def analyze_task_completion(self, task):
        # Track metrics
        duration = task.completed_at - task.started_at
        error_count = len(task.errors)
        test_coverage = calculate_coverage(task.files_modified)
        
        # Compare to baseline
        avg_duration = self.get_baseline(task.type)
        if duration > avg_duration * 1.1:
            self.event_bus.publish(PERFORMANCE_ISSUE, {
                "task_type": task.type,
                "metric": "duration",
                "current": duration,
                "baseline": avg_duration,
                "deviation_pct": ((duration/avg_duration)-1)*100
            })
```

**Tracks**: Task completion time, error rates, test coverage, resource usage.

#### TrendDetector
```python
class TrendDetector:
    async def scan_dependencies(self):
        # Check for outdated packages
        for requirements_file in self.workspace.rglob("requirements.txt"):
            for line in requirements_file:
                package, version = parse_requirement(line)
                latest = await pypi.get_latest_version(package)
                if version < latest:
                    self.event_bus.publish(OUTDATED_DEPENDENCY, {
                        "package": package,
                        "current": version,
                        "latest": latest,
                        "file": str(requirements_file)
                    })
```

**Detects**: Outdated dependencies, new tech in workspace (if many .tsx files appear, detects TypeScript/React), security vulnerabilities.

---

## MODULE 8: MCP - AI BRAIN (jarvis/mcp/)

### What It Does
**Understands context and makes decisions** - the intelligence layer.

### Components

#### ContextEngine
```python
class ContextEngine:
    async def build_context(self, task: str, workspace: Path, persona: Persona):
        context = {
            "task": task,
            "workspace_type": workspace.profile.project_type,
            "persona": persona.to_dict(),
            "recent_files": self.get_recently_modified_files(),
            "learned_patterns": self.get_relevant_patterns(task),
            "similar_past_tasks": self.find_similar_tasks(task),
            "current_deals": persona.active_deals
        }
        
        # Add semantic search
        query_embedding = self.embedding_model.encode(task)
        relevant_code = self.vector_store.search(query_embedding, k=5)
        context["semantic_results"] = relevant_code
        
        return context
```

**How**: Uses embeddings to find semantically similar code, not just keyword matches.

**Example**: 
- Task: "Add payment handling"
- Keyword search: finds files with "payment" - might miss "checkout", "billing", "invoice"
- Semantic search: understands these are related → more comprehensive

#### AutonomousPlanner
```python
class AutonomousPlanner:
    async def plan(self, task: str, context: Context):
        # Decompose into steps
        plan = Plan()
        
        if "authentication" in task.lower():
            plan.add_steps([
                "Research existing auth implementation",
                "Choose auth method (JWT, OAuth, API keys)",
                "Install dependencies",
                "Configure settings",
                "Implement models/serializers",
                "Create views/endpoints",
                "Add URLs",
                "Write tests",
                "Update documentation"
            ])
        
        # Estimate complexity
        plan.estimate_complexity(len(plan.steps), context)
        
        # Identify dependencies between steps
        plan.add_dependency("Install dependencies", "Configure settings")
        
        return plan
```

**Why critical**: Breaks complex tasks into executable steps. Without this, JARVIS can only do single-step operations.

#### SkillSelector
```python
class SkillSelector:
    async def select_skills(self, plan_step: Step, context: Context):
        candidates = self.get_applicable_skills(plan_step, context)
        
        scored = []
        for skill in candidates:
            score = 0
            
            # 1. Semantic similarity to step description
            similarity = cosine_similarity(
                self.embedding_model.encode(plan_step.description),
                self.embedding_model.encode(skill.description)
            )
            score += similarity * 0.4
            
            # 2. Historical success rate for this persona
            success_rate = self.get_success_rate(persona.id, skill.name)
            score += success_rate * 0.3
            
            # 3. Relevance to context (files involved)
            overlap = len(set(skill.typical_files) & set(context.recent_files))
            score += overlap * 0.2
            
            # 4. Resource cost (prefer cheaper)
            cost = self.estimate_cost(skill)
            score -= cost * 0.1
            
            scored.append((skill, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [skill for skill, score in scored[:3]]
```

**Why critical**: Picks the right tool for each job. Different skills for Django vs Flask, testing vs production.

---

## MODULE 9: SKILLS (jarvis/mcp/skills/)

### What They Are
**Reusable capabilities** that MCP selects and executes.

### Structure
```python
from mcp.skills.base_skill import BaseSkill

class DjangoSkills(BaseSkill):
    name = "django_skills"
    description = "Django-specific operations"
    applicable_tech = ["django", "python"]
    priority = 1  # High priority for Django projects
    auto_load = True  # Load automatically when Django detected
    
    async def execute(self, context):
        # Do the actual work
        if context.task == "create_model":
            return await self.create_model(context)
        elif context.task == "create_view":
            return await self.create_view(context)
    
    async def create_model(self, context):
        template = self.load_template("django_model.py.j2")
        code = template.render(fields=context.fields)
        await self.file_modder.write(context.filepath, code)
        return SkillResult(success=True, files_modified=[context.filepath])
```

### Example Skills Needed
- `django_skills.py` - Models, views, serializers, settings
- `react_skills.py` - Components, hooks, state management
- `testing_skills.py` - Unit tests, integration tests, fixtures
- `docker_skills.py` - Dockerfile, docker-compose, multi-stage builds
- `deployment_skills.py` - CI/CD configs, infrastructure
- `refactoring_skills.py` - Extract method, rename, move file
- `documentation_skills.py` - Readme, API docs, docstrings

**How to add**: Create file in `mcp/skills/`, inherit BaseSkill, implement `execute()`. Fireup auto-discovers it!

---

## MODULE 10: UPDATERS (jarvis/updaters/)

### What They Do
**Safely modify files** after safety approval.

### FileModder (Most Critical)
```python
class FileModder:
    async def modify(self, filepath: Path, modifications: List[Modification]):
        # 0. Safety check already passed
        
        # 1. Create backup
        backup_path = self.backup_manager.create_backup(filepath)
        
        # 2. Read original
        original = filepath.read_text()
        
        # 3. Apply modifications (AST-based, not regex!)
        modified = original
        for mod in modifications:
            if mod.type == "insert":
                modified = self.insert_at_line(modified, mod.line, mod.code)
            elif mod.type == "replace":
                modified = self.replace_pattern(modified, mod.pattern, mod.replacement)
            elif mod.type == "delete":
                modified = self.delete_block(modified, mod.start_line, mod.end_line)
        
        # 4. Validate syntax (important!)
        if filepath.suffix == ".py":
            try:
                ast.parse(modified)  # Check syntax
            except SyntaxError as e:
                raise ModificationError(f"Invalid syntax: {e}")
        
        # 5. Write atomically (write to temp, fsync, rename)
        temp_path = filepath.with_suffix(filepath.suffix + ".tmp")
        temp_path.write_text(modified)
        os.fsync(temp_path.open().fileno())
        temp_path.replace(filepath)  # Atomic rename
        
        # 6. Log success
        self.event_bus.publish(MODIFICATION_COMPLETED, {
            "file": str(filepath),
            "backup": str(backup_path),
            "modifications": len(modifications)
        })
```

**Why AST-based matters**:
- Regex: `search_and_replace("DEBUG = True", "DEBUG = False")` → might match comment!
- AST: Parse Python code → only modify assignment statements → safe

### CodeGenerator
```python
class CodeGenerator:
    def __init__(self):
        self.templates = self.load_templates()
    
    async def generate(self, template_name: str, context: Dict):
        template = self.templates.get(template_name)
        if not template:
            raise TemplateNotFound(template_name)
        
        code = template.render(**context)
        
        # Maintain formatting (use Black if configured)
        if config.updater.preserve_comments:
            code = self.preserve_formatting(code)
        
        return code
```

**Templates**: Jinja2 files like `django_model.py.j2`:
```jinja2
class {{ model_name }}(models.Model):
    {% for field in fields %}
    {{ field.name }} = models.{{ field.type }}({% if field.params %}{{ field.params }}{% endif %})
    {% endfor %}
    
    def __str__(self):
        return f"{{ model_name }}: {self.id}"
```

### ConfigUpdater
```python
class ConfigUpdater:
    async def add_dependency(self, filepath: Path, package: str, version: str = None):
        content = filepath.read_text()
        
        if filepath.name == "requirements.txt":
            # Add line
            new_line = f"{package}=={version}" if version else package
            content += f"\n{new_line}\n"
        
        elif filepath.name == "package.json":
            # JSON modify
            data = json.loads(content)
            data["dependencies"][package] = version
            content = json.dumps(data, indent=2)
        
        await self.file_modder.modify(filepath, [
            Modification(type="append", content=content)
        ])
```

---

## MODULE 11: SAFETY GUARD (jarvis/safety/guard.py)

### What It Does
**Approves or rejects modifications** based on risk.

### Risk Assessment
```python
class SafetyGuard:
    def assess_risk(self, action: dict) -> RiskLevel:
        risk_score = 0
        
        # File type
        filepath = action["file"]
        if filepath.startswith("tests/"):
            risk_score += 1  # LOW
        elif filepath.startswith("docs/"):
            risk_score += 1  # LOW
        elif filepath.startswith(("settings.py", "config/")):
            risk_score += 3  # MEDIUM
        elif filepath.startswith(("models.py", "schema.sql")):
            risk_score += 4  # HIGH
        elif "core/" in filepath or "orchestrator" in filepath:
            risk_score += 5  # CRITICAL
        
        # Action type
        if action["type"] == "delete":
            risk_score += 2
        elif action["type"] == "modify":
            risk_score += 1
        elif action["type"] in ["create", "format"]:
            risk_score += 0
        
        # Scope
        files_affected = len(action.get("files", []))
        if files_affected > 5:
            risk_score += 2
        elif files_affected > 2:
            risk_score += 1
        
        # Map to levels
        if risk_score <= 2:
            return RiskLevel.LOW
        elif risk_score <= 5:
            return RiskLevel.MEDIUM
        elif risk_score <= 8:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    async def request_approval(self, action: dict, risk: RiskLevel, persona: Persona):
        if risk == RiskLevel.LOW and config.auto_approve_low_risk:
            return Approval Decision(approved=True, method="auto")
        
        elif risk == RiskLevel.MEDIUM:
            if persona.trust_score > 0.8:
                return Approval(approved=True, method="auto_high_trust")
            else:
                # Create PR
                pr_url = await self.create_pull_request(action)
                return Approval(approved=None, method="pr", pr_url=pr_url)
        
        elif risk == RiskLevel.HIGH:
            # Send notification
            await self.notify_persona_owner(persona, action)
            # Wait for response (with timeout)
            decision = await self.wait_for_approval(timeout=48*3600)
            return decision
        
        elif risk == RiskLevel.CRITICAL:
            # Two-person approval
            return Approval(approved=None, method="two_person")
```

---

## MODULE 12: PERSONA MANAGER (jarvis/persona/persona_manager.py)

### What It Does
Manages multiple "identities" for different clients/projects.

### Persona Structure
```python
@dataclass
class Persona:
    id: str
    name: str
    workspaces: List[Path]
    preferences: Dict
    trust_score: float  # 0.0 - 1.0
    deals: List[Deal]
    knowledge_graph: KnowledgeGraph
    performance_history: List[Metric]
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "workspaces": [str(w) for w in self.workspaces],
            "preferences": self.preferences,
            "trust_score": self.trust_score,
            ...
        }
```

### Auto-Switching
```python
class PersonaManager:
    def get_active_persona(self, current_path: Path) -> Persona:
        # Check if current path matches any workspace
        for persona in self.personas:
            for workspace in persona.workspaces:
                if current_path == workspace or current_path.is_relative_to(workspace):
                    if self.active_persona != persona:
                        self.switch_persona(persona)
                    return persona
        
        # Default
        return self.get_default_persona()
    
    def switch_persona(self, persona: Persona):
        self.active_persona = persona
        
        # Fire event so other components know
        self.event_bus.publish(PERSONA_SWITCHED, {
            "persona_id": persona.id,
            "timestamp": datetime.utcnow()
        })
        
        # Update trust score based on recent performance
        self.update_trust_score(persona)
```

**Automatic**: `cd /techcorp-project` → TechCorp persona active. `cd /beta-project` → Beta persona active.

### Trust Score Management
```python
def update_trust_score(self, persona: Persona):
    """Adjust trust based on recent performance"""
    recent_tasks = self.get_recent_tasks(persona.id, count=20)
    
    success_rate = sum(1 for t in recent_tasks if t.success) / len(recent_tasks)
    avg_duration = sum(t.duration for t in recent_tasks) / len(recent_tasks)
    user_feedback = self.get_recent_feedback(persona.id)
    
    # Calculate trust (0-1)
    trust = (
        success_rate * 0.4 +
        (1 - min(avg_duration / expected_duration, 1)) * 0.3 +
        user_feedback.avg_sentiment * 0.3
    )
    
    # Decay old scores gradually
    persona.trust_score = persona.trust_score * 0.9 + trust * 0.1
```

**Impact**: Higher trust → more auto-approvals → higher autonomy.

---

## MODULE 13: ARCHIVE (jarvis/archive/)

### What It Does
**Time-travel and rollback** - enables safe, bold autonomy.

### Date Archiver
```python
class DateArchiver:
    async def create_snapshot(self, label: str = None):
        # Compress entire workspace
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
        archive_name = f"archive_{timestamp}_{label}.tar.gz"
        archive_path = self.archive_dir / archive_name
        
        # Create tar.gz
        with tarfile.open(archive_path, "w:gz", compresslevel=6) as tar:
            tar.add(self.workspace, arcname=".")
        
        # Optional: encrypt
        if config.archive.encryption_enabled:
            self.encrypt_archive(archive_path)
        
        # Retain based on policy
        self.apply_retention_policy()
        
        self.event_bus.publish(ARCHIVE_CREATED, {
            "path": str(archive_path),
            "size": archive_path.stat().st_size,
            "timestamp": timestamp
        })
```

**Policies**:
- Hourly: Keep 24
- Daily: Keep 30
- Weekly: Keep 12
- Monthly: Keep 24
- Yearly: Keep 10

### Restore Manager
```python
class RestoreManager:
    async def restore_to_point(self, timestamp: str):
        # Find archive
        archive = self.find_archive(timestamp)
        
        # Extract to temp
        temp_dir = Path(tempfile.mkdtemp())
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(temp_dir)
        
        # Compare with current (dry-run option)
        if dry_run:
            return self.diff_directories(temp_dir, self.workspace)
        
        # Backup current state first
        current_backup = self.create_backup(self.workspace)
        
        # Replace
        self.workspace_files = archive.extracted_files
        
        # Log
        self.event_bus.publish(WORKSPACE_RESTORED, {
            "archive": str(archive),
            "restored_at": datetime.utcnow().isoformat(),
            "backup_taken": str(current_backup)
        })
```

**Why critical**: Enables JARVIS to act boldly because everything is reversible. "Oops, that change broke things" → restore to pre-change state instantly.

---

## MODULE 14: META-LEARNER (jarvis/learners/meta_learner.py)

### What It Does
**JARVIS learns how to learn better** - the self-improvement engine.

### How It Works
```python
class MetaLearner:
    async def analyze_and_evolve(self):
        # 1. Collect recent metrics
        metrics = self.collect_recent_metrics()
        
        # 2. Detect anomalies
        anomalies = self.detect_anomalies(metrics)
        
        for anomaly in anomalies:
            # 3. Generate hypotheses
            hypotheses = self.generate_hypotheses(anomaly)
            
            for hypothesis in hypotheses:
                # 4. Check if we've tried this before
                key = (hypothesis.component, hypothesis.change_type)
                if key in self.effectiveness_scores:
                    if self.effectiveness_scores[key] < 0.3:
                        continue  # Skip ineffective changes
                
                # 5. Test in sandbox
                success, new_metrics = await self.test_hypothesis(hypothesis)
                
                if success:
                    # 6. Deploy to production
                    await self.deploy_change(hypothesis)
                    
                    # 7. Record effectiveness
                    self.effectiveness_scores[key] = 0.8
                    self.evolution_history.append({
                        "timestamp": datetime.utcnow(),
                        "hypothesis": hypothesis,
                        "before": metrics,
                        "after": new_metrics,
                        "deployed": True
                    })
    
    def generate_hypotheses(self, anomaly: Anomaly) -> List[Hypothesis]:
        """Generate potential fixes"""
        hypotheses = []
        
        if anomaly.component == "pattern_recognition" and anomaly.metric == "false_positive_rate":
            hypotheses.append(Hypothesis(
                component="pattern_recognition",
                change="adjust_confidence_threshold",
                params={"threshold_delta": -0.05},
                expected_effect="Reduce false positives by 20%",
                risk="low"
            ))
            hypotheses.append(Hypothesis(
                component="pattern_recognition",
                change="add_blacklist_patterns",
                params={},
                expected_effect="Reduce noise",
                risk="low"
            ))
        
        elif anomaly.component == "file_modder" and anomaly.metric == "execution_time":
            hypotheses.append(Hypothesis(
                component="file_modder",
                change="enable_batching",
                params={"batch_size": 10},
                expected_effect="50% faster for multi-file ops",
                risk="medium"
            ))
        
        return hypotheses
    
    async def test_hypothesis(self, hypothesis: Hypothesis):
        # Create isolated test workspace
        test_workspace = self.create_sandbox()
        
        # Apply change
        await self.apply_change(test_workspace, hypothesis)
        
        # Run synthetic workload
        before = self.run_workload(test_workspace, iterations=100)
        after = self.run_workload(test_workspace, iterations=100)
        
        # Compare
        improvement = (before - after) / before
        
        # Statistical significance test
        if improvement > hypothesis.min_improvement and p_value < 0.05:
            return True, after
        else:
            return False, None
```

**Example Evolution**:
```
Observation: Pattern recognition finding too many false positives (15%)
Hypothesis: "Increase confidence threshold from 0.7 to 0.8"
Test: Last week's files → 100 patterns found, 15 false → after: 89 patterns, 4 false
Result: 6 false positives eliminated, 11 true positives lost → Net positive ✅
Deploy: Auto (LOW risk)
Effectiveness score: 0.87
```

**Autonomy Impact**: JARVIS gets faster, more accurate, more reliable over time without human tuning.

---

## MODULE 15: DEAL TRACKER (jarvis/persona/deal_tracker.py)

### What It Does
**Tracks client projects** with budgets, deadlines, milestones.

### Deal Structure
```python
@dataclass
class Deal:
    id: str
    title: str
    client: str
    persona_id: str
    description: str
    value: float
    currency: str
    start_date: datetime
    deadline: datetime
    status: Literal["negotiation", "active", "on_hold", "completed", "cancelled"]
    progress: float  # 0.0 - 1.0
    
    tasks: List[Task]
    milestones: List[Milestone]
    stakeholders: List[Contact]
    
    budget_spent: float
    time_spent: float
    
    @property
    def budget_remaining(self):
        return self.value - self.budget_spent
    
    @property
    def days_until_deadline(self):
        return (self.deadline - datetime.utcnow()).days
```

### Auto-Update Mechanisms
```python
class DealTracker:
    async def update_from_git_commit(self, commit: Commit):
        # Parse commit message for deal references
        # "feat(checkout): complete Stripe for TechCorp deal #123"
        match = re.search(r"deal\s+#(\d+)", commit.message, re.I)
        if match:
            deal_id = match.group(1)
            await self.increment_progress(deal_id, task_completed=True)
            
            # Estimate time from commit size?
            lines_changed = commit.stats.total["lines"]
            hours = self.estimate_hours_from_lines(lines_changed)
            await self.add_time_spent(deal_id, hours)
    
    async def update_from_task_completion(self, task: Task):
        # When JARVIS completes a task linked to a deal
        if task.deal_id:
            deal = self.get_deal(task.deal_id)
            deal.tasks_completed += 1
            deal.total_tasks
            deal.progress = deal.tasks_completed / deal.total_tasks
            deal.time_spent += task.duration_hours
    
    async def check_deadlines(self):
        # Run daily
        for deal in self.get_active_deals():
            days_left = deal.days_until_deadline
            if days_left < 7:
                # Send reminder to stakeholders
                await self.send_deadline_reminder(deal)
            if days_left < 3 and deal.progress < 0.9:
                # At risk!
                await self.escalate_at_risk_deal(deal)
```

**Business value**: JARVIS doesn't just code - it manages client relationships, tracks budgets, sends deadline reminders. Autonomous business management.

---

## MODULE 16: SCANNER (jarvis/scanner/)

### What It Does
**Analyzes workspace structure** to detect project type and tech stack.

### WorkspaceScanner
```python
class WorkspaceScanner:
    async def scan(self, path: Path) -> WorkspaceProfile:
        profile = WorkspaceProfile()
        
        # 1. Detect project type
        if (path / "package.json").exists():
            profile.project_type = ProjectType.NODE_JS
            data = json.loads((path / "package.json").read_text())
            profile.dependencies = list(data.get("dependencies", {}).keys())
            profile.dev_dependencies = list(data.get("devDependencies", {}).keys())
        
        if (path / "requirements.txt").exists():
            profile.project_type = ProjectType.PYTHON
            profile.dependencies = parse_requirements(path / "requirements.txt")
        
        if (path / "pom.xml").exists():
            profile.project_type = ProjectType.JAVA_MAVEN
            profile.dependencies = parse_maven_pom(path / "pom.xml")
        
        if (path / "Cargo.toml").exists():
            profile.project_type = ProjectType.RUST
            profile.dependencies = parse_cargo_toml(path / "Cargo.toml")
        
        # 2. Count file types
        profile.file_counts = self.count_files_by_extension(path)
        
        # 3. Detect frameworks
        if "django" in profile.dependencies or (path / "manage.py").exists():
            profile.frameworks.append("django")
        if "fastapi" in profile.dependencies:
            profile.frameworks.append("fastapi")
        if "react" in profile.dependencies or any(f.suffix == ".jsx" for f in path.rglob("*")):
            profile.frameworks.append("react")
        
        # 4. Find common patterns
        profile.common_patterns = self.detect_patterns(path)
        
        # 5. Identify important files
        profile.important_files = self.find_important_files(path)
        
        profile.scan_timestamp = datetime.utcnow()
        return profile
```

**Why critical**: Fireup uses this to decide which skills to load. If scanner says "Django + React", Fireup loads django_skills + react_skills.

---

## COMPLETE DATA FLOW EXAMPLE

### Scenario: "Add Stripe payment to TechCorp's Django checkout"

**0. Startup** (already happened)
```
Fireup: Scans /techcorp-backend
  → Detects: Django, React, PostgreSQL
  → Loads: django_skills, react_skills, postgres_skills, testing_skills
  → Active persona: TechCorp (trust 0.87)
  → Ready and waiting
```

**1. User Request**
```
CLI: jarvis execute "Add Stripe payment to checkout"
  → Publishes: TASK_REQUESTED event
```

**2. MCP Planning**
```
MCP receives TASK_REQUESTED
  ↓
ContextEngine.build():
  - Who: TechCorp persona (Django, prefers pytest, used Stripe 3x before)
  - What: "payment", "checkout" → semantic search finds stripe_webhook.py, payment_model.py
  - Where: checkout/views.py, payment/models.py
  → Rich context ready
  ↓
AutonomousPlanner.decompose("Add Stripe payment"):
  Steps:
    1. Add 'stripe' to requirements.txt
    2. Add STRIPE_API_KEY to settings.py
    3. Create payment/models.py (Customer, Payment, Refund)
    4. Create payment/views.py (CreatePayment, Webhook)
    5. Add /api/payment/ to urls.py
    6. Write tests (test_payment.py)
    7. Update README with Stripe setup
  → Plan with 7 steps, dependencies (step 2 before 4)
  ↓
SkillSelector.select_skills():
  Step 1: config_updater (score 0.92), pip_installer (0.85)
  Step 2: file_modder (0.88), django_settings (0.91) ← Winner
  Step 3: code_generator (0.90)
  Step 4: code_generator (0.88)
  Step 5: file_modder (0.89)
  Step 6: test_writer (0.93)
  Step 7: doc_generator (0.87)
  → Skills selected with confidence scores
```

**3. Safety Check**
```
For each modification:
  Action: "Add stripe to requirements.txt"
    → SafetyGuard.assess_risk()
      Risk: MEDIUM (new dependency)
      Trust: 0.87 → Auto-approve ✅
    → Approve immediately

  Action: "Modify settings.py"
    → Risk: MEDIUM (config change)
    → Auto-approve ✅
```

**4. Execution**
```
Step 1: config_updater.add_dependency("stripe")
  ConfigUpdater:
    - Reads requirements.txt
    - Adds "stripe==5.1.0"
    - Validates with pip dry-run
    - Writes atomically
    - Backup: requirements.txt.bak-20250318.jarvis
  → Event: MODIFICATION_COMPLETED
  ↓ (EventBus notifies)
  Archive: backs up changed file
  PerformanceAnalyzer: records 0.3s execution time
  ✓ Step 1 done (0.3s)

Step 2: django_settings_modifier.add_stripe_settings()
  FileModder:
    - Backup: settings.py
    - Insert at end of file:
      STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
      STRIPE_PUBLISHABLE_KEY = ...
    - Syntax check: python -m py_compile settings.py ✅
    - Atomic write
  → Event: MODIFICATION_COMPLETED
  ✓ Step 2 done (0.2s)

Step 3: code_generator.create_payment_models()
  CodeGenerator:
    - Loads template: payment_model.py.j2
    - Renders with fields: Customer, Payment, Refund
    - Generates 89 lines
    - Writes payment/models.py
  → Event: MODIFICATION_COMPLETED
  ✓ Step 3 done (2.1s)

[...Steps 4-7 similar...]
```

**5. Validation**
```
All steps complete → Run tests
  pytest tests/test_payment.py
  15 tests pass ✅
  Coverage: payment module 94% ✅

Git commit + PR:
  git add .
  git commit -m "feat(payment): add Stripe integration (JARVIS)"
  git push origin feature/stripe-payment
  → PR #47 created
  → CI runs, all checks pass ✅
  → Auto-merge (MEDIUM risk + CI green)
```

**6. Learning**
```
Observers see:
  - 8 files modified
  - 18 minutes total (avg 2.3h for similar task → 92% faster!)
  - All tests passing

Learners activate:

PatternRecognition:
  "stripe_integration_workflow" pattern detected
  Store in data/patterns/stripe_integration_001.json
  Publish PATTERN_DISCOVERED

PreferenceExtractor:
  "TechCorp uses Stripe webhooks with signature verification"
  Update persona.preferences.payment_webhook_validation = "stripe_signature"
  Publish PREFERENCE_UPDATED

PerformanceAnalyzer:
  "Stripe integration: 18m vs avg 2.3h → record exceptional performance"
  Update persona.performance.completed_tasks += 1
  Publish METRICS_COLLECTED

TrendDetector:
  "Using stripe==5.1.0, 5.2.0 available"
  Create TODO item in workspace: "Update Stripe to 5.2.0"

MetaLearner:
  "Task exceptionally fast, good skill selection"
  Increase weights for: config_updater (for Django), code_generator
  No system changes needed this time
```

**7. Deal Tracking** (if linked)
```
Deal: "E-commerce Platform Revamp" (TechCorp)
  → tasks_completed: 124 → 125
  → progress: 62% → 62.1%
  → time_spent: 421.0h → 421.3h
  → budget_spent: $42,100 → $42,108 (18m @ $280/hr rate)
  → Publish DEAL_UPDATED
```

**8. User Notification**
```
JARVIS CLI output:
✅ Stripe payment integration added!

   Files modified: 8
   Tests added: 15 (all passing ✓)
   PR: #47 (merged)
   Time: 18 minutes (saved ~2 hours!)
   Coverage: 94%
   
   Deal progress updated: E-commerce Platform (62.1% complete)
   
   Note: Stripe 5.2.0 available. Consider updating.
```

---

## EVERY FOLDER & FILE - PURPOSE & REASON

### Root Level
- **README.md** - GitHub homepage, explain project to visitors
- **START_HERE.md** - Getting started guide for new users
- **AUTONOMY_AND_INTERCONNECTION.md** - How all components connect (most important tech doc)
- **JARVIS_DESIGN.md** - Complete architectural reference (67KB)
- **JARVIS_COMPLETE_GUIDE.md** - API reference and operations
- **README_JARVIS_MASTER.md** - Master overview
- **FINAL_SUMMARY.txt** - Quick reference cheat sheet

### core/
- **orchestrator.py** - Central coordinator, component lifecycle, scheduling
- **__init__.py** - Package marker

**Exists because**: Core system coordination needed. Without orchestrator, no startup sequence, no component management.

### utils/
- **event_bus.py** - Async pub/sub communication backbone
- **logger.py** - Structured JSON logging
- **config.py** - Configuration with env overrides
- **__init__.py** - Package marker

**Exists because**: Shared utilities used by ALL components. Event bus is critical for loose coupling.

### fireup/
- **fireup.py** - **THE KEY TRIGGER** - dynamic startup, skill loading, self-modification (577 lines)
- **dynamic_skills/** - Auto-generated workspace-specific helper code
- **__init__.py** - Package marker

**Exists because**: This is what makes JARVIS autonomous - auto-detects tech, loads skills, updates itself. Without fireup, manual config required → not autonomous.

### jarvis/
Main package containing all operational components:

#### observers/
- **file_system.py** - Watchdog-based file monitoring
- **git.py** - Git commit/branch/PR monitoring
- **conversations.py** - Chat/email/issue comment logging
- **database.py** - DB schema change detection
- **__init__.py**

**Exists because**: JARVIS needs eyes on everything. Without observers, no awareness of changes.

#### learners/
- **pattern_recognition.py** - AST parsing, pattern clustering
- **preference_extractor.py** - Git history analysis, style learning
- **performance_analyzer.py** - Metrics tracking, anomaly detection
- **trend_detector.py** - Outdated deps, new tech detection
- **meta_learner.py** - Self-improvement, hypothesis testing
- **__init__.py**

**Exists because**: JARVIS must learn from observations. Without learners, just automation, not intelligence.

#### updaters/
- **file_modder.py** - AST-based safe file modification with backup
- **code_generator.py** - Jinja2 template-based code generation
- **config_updater.py** - Safe dependency/configuration updates
- **schema_migrator.py** - Database migration scripts
- **__init__.py**

**Exists because**: JARVIS needs to act safely. Without updaters, can't modify code.

#### mcp/
- **context_engine.py** - Semantic search, embeddings, context building
- **autonomous_planner.py** - Task decomposition, step planning
- **skill_selector.py** - Skill ranking and selection
- **skills/**
  - **base_skill.py** - Abstract base class for all skills
  - **django_skills.py** - Django operations (to be created)
  - **react_skills.py** - React operations (to be created)
  - **testing_skills.py** - Test generation (to be created)
  - **__init__.py**

**Exists because**: This is the AI brain. Without MCP, no intelligent planning or execution.

#### persona/
- **persona_manager.py** - Multi-persona switching, trust scoring
- **deal_tracker.py** - Client project and deadline tracking
- **history_db/** - SQLite models and queries
- **comm_logger.py** - Communication history
- **__init__.py**

**Exists because**: Need multi-client isolation and business context. Without persona, JARVIS can't work for multiple clients with different preferences.

#### scanner/
- **workspace_scanner.py** - Project type detection, tech stack analysis
- **folder_categorizer.py** - Categorize folders (src/, tests/, docs/)
- **file_detector.py** - File classification by extension/content
- **integration_engine.py** - Auto-integration logic for new projects
- **__init__.py**

**Exists because**: Fireup needs workspace intelligence. Without scanner, can't detect what skills to load.

#### safety/
- **guard.py** - Risk assessment, approval workflow
- **approval_workflow.py** - Approval logic (auto/PR/manual)
- **impact_analyzer.py** - Predict impact of changes
- **backup_manager.py** - Backup creation and retention
- **__init__.py**

**Exists because**: Safety enables autonomy. Without safety, all changes need manual review → no autonomy.

#### archive/
- **archiver.py** - Main archive interface
- **date_archiver.py** - Time-based snapshots (hourly/daily/weekly)
- **category_archiver.py** - Category-based archives (by persona, project)
- **restore_manager.py** - Point-in-time restore
- **__init__.py**

**Exists because**: Rollback capability essential for bold autonomous action. Without archive, can't recover from mistakes.

### cli/
- **main.py** - CLI entry point (argparse/click)
- **commands/** - Subcommands (status, evolve, persona, scan, etc.)
- **completions/** - Shell completion scripts
- **__init__.py**

**Exists because**: User interface. Without CLI, must use API only.

### api/
- **server.py** - FastAPI server
- **endpoints/** - REST endpoints (status, persona, tasks, metrics)
- **websocket/** - Real-time event streaming
- **__init__.py**

**Exists because**: Optional HTTP API for integration with other tools. Not strictly needed but useful.

### tests/
- **unit/** - Unit tests for each component
- **integration/** - End-to-end tests
- **fixtures/** - Test data (sample workspaces, mock events)
- **__init__.py**

**Exists because**: Quality assurance. Without tests, can't ensure reliability.

### docs/
- Additional documentation (manuals, tutorials)
- **api/** - Generated API docs

**Exists because**: Comprehensive documentation for users and developers.

### data/ (created at runtime)
- **personas/** - Persona JSON files
- **patterns/** - Learned code patterns
- **skills/** - Skill registry and metadata
- **history/** - SQLite database (jarvis.db)
- **archives/** - Compressed backups
- **cache/** - Temporary caches (embeddings, file indexes)

**Exists because**: Persistent storage. JARVIS needs to remember what it learned.

### logs/ (created at runtime)
- **jarvis.log** - Main structured log (JSON)
- **errors/** - Error-only logs
- **performance/** - Metrics logs
- **audit/** - Immutable audit trail

**Exists because**: Observability. Without logs, can't debug or monitor.

---

## WHY EVERYTHING IS NECESSARY - The Minimal Viable JARVIS

**Strict minimum**:
1. ✅ Event bus - **can't communicate without it**
2. ✅ Logger - **can't debug without it**
3. ✅ Config - **can't configure without it**
4. ✅ Orchestrator - **can't start components without it**
5. ✅ **Fireup** - **can't be autonomous without it** (triggers the adaptation)
6. ✅ Observers - **can't learn without seeing changes**
7. ✅ Learners - **can't improve without learning**
8. ✅ Updaters - **can't act without modification ability**
9. ✅ Safety - **can't be trusted without approval/rollback**
10. ✅ Archive - **can't be bold without rollback capability**
11. ✅ Persona - **can't manage multiple clients without isolation**
12. ✅ MCP - **can't plan tasks without intelligence**
13. ✅ Skills - **can't execute without tools**

**Remove any one** and JARVIS loses a core capability.

---

## FIREUP: THE HEART OF AUTONOMY

**Why fireup is the trigger**:
- **Without fireup**: Manual config → JARVIS doesn't know what skills to use
- **With fireup**: Scans workspace → auto-loads appropriate skills → updates its own config → hot-reloads when new tech added

**This is the key innovation**: True self-configuration. Most systems need manual setup. JARVIS uses fireup to **configure itself** based on workspace analysis.

**Analogy**:
- Normal AI assistant: "Please install plugin for Django"
- JARVIS: *Scans project, sees Django, loads Django skills, ready to help*

That's why fireup matters. It's the **autonomous trigger** that makes everything else possible.

---

## FINAL SUMMARY

**JARVIS achieves autonomy through**:
1. **Fireup** - Self-configuring startup (no manual setup)
2. **Observers** - Continuous awareness (never misses changes)
3. **Learners** - Pattern extraction (gets smarter)
4. **MCP** - Intelligent planning (multi-step reasoning)
5. **Updaters** - Safe execution (backup + rollback)
6. **Safety** - Risk-based approvals (enables bold action)
7. **Persona** - Multi-client isolation (works for many)
8. **Archive** - Time travel (reversible changes)
9. **MetaLearner** - Self-improvement (optimizes system)
10. **Event Bus** - Loose coupling (components work independently)

**Result**: AI employee that works 24/7, adapts to your projects, learns your style, manages clients, and gets better every week.

**Every folder/file has a clear purpose**. The architecture is **minimal but complete** - no bloat, everything serves a specific function in the autonomy loop.

---

**Ready to build?** Start with `fireup/fireup.py` (already working), then implement observers and learners to start the learning loop.

All specs in documentation. You have complete blueprint. 🚀

## MODULE 17: ACCOUNT AUTO-INITIALIZER (jarvis/observers/account_initializer.py)

### What It Does
Automatically creates smartness files when a new account folder is added under `MEMORY/accounts/`.

### How
Watches for `file.created` events on `MEMORY/accounts/`. When a new directory appears, it creates:
- `deals/` subfolder
- `notes.json`
- `activities.jsonl`
- `index.json`
- `summary.md`

Publishes `account.initialized` event for meta-learning.

## MODULE 18: TOOL EXECUTOR (jarvis/tools/executor.py)

### What It Does
Safely executes shell commands in the workspace when LLM decides to gather information.

### Allowed Commands
ls, grep, find, cat, head, tail, wc, pwd, du, df, file, stat.

### How
Bot includes tool usage instructions in system prompt. If LLM outputs `!ls -la`, executor runs it and returns output to LLM for final answer. Commands run with 30s timeout, confined to workspace.

Publishes `tool.executed` event for meta-learning.

---

**Note:** This document describes the legacy MCP-based architecture. For the current self‑evolving JARVIS system (v2.0+) see `docs/architecture/CURRENT_ARCHITECTURE.md`. The current system includes 15 components, account‑based organization, tool execution, meta‑learning, and dynamic prompt evolution.
