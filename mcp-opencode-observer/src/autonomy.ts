import { readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync, copyFileSync, unlinkSync } from 'fs';
import { join, dirname, basename } from 'path';
import yaml from 'js-yaml';
import { ConversationDB } from './db';

// ============== Configuration ==============

const WORKSPACE_ROOT = process.env.OPENCODE_WORKSPACE || process.cwd();
const RULES_PATH = join(WORKSPACE_ROOT, 'config', 'rules.yaml');

interface Rule {
  id: string;
  pattern?: string;
  event?: string;
  source?: string;
  confidence?: number;
  action: string;
  condition?: string;
  priority?: number;
}

interface RulesConfig {
  approval_mode: boolean;
  max_approvals_before_autonomous: number;
  triggers: Rule[];
  actions: Record<string, { description: string; exec: string }>;
  safety: {
    max_updates_per_minute: number;
    cooldown_after_error_seconds: number;
    allowed_paths: string[];
    forbidden_paths: string[];
  };
}

let rulesConfig: RulesConfig;
try {
  if (existsSync(RULES_PATH)) {
    rulesConfig = yaml.load(readFileSync(RULES_PATH, 'utf-8')) as RulesConfig;
    console.error('[Autonomy] Loaded rules from', RULES_PATH);
  } else {
    rulesConfig = getDefaultRules();
    // Write default rules for future editing
    try { writeFileSync(RULES_PATH, yaml.dump(rulesConfig)); } catch {}
  }
} catch (e) {
  console.error('[Autonomy] Failed to load rules.yaml, using defaults', e);
  rulesConfig = getDefaultRules();
}

function getDefaultRules(): RulesConfig {
  return {
    approval_mode: true,
    max_approvals_before_autonomous: 50,
    triggers: [
      {
        id: 'persona_yellow_ai',
        pattern: '(?i)yellow\\.ai|conversational ai|bot studio|agent assist',
        source: 'message',
        action: 'switch_persona account_executive',
        confidence: 0.8,
        priority: 10
      },
      {
        id: 'persona_technical',
        pattern: '(?i)demo|architecture|integration|api|technical|solution consultant|presales',
        source: 'message',
        action: 'switch_persona solution_consultant',
        confidence: 0.7,
        priority: 9
      },
      {
        id: 'detect_competitor',
        pattern: '(?i)(zendesk|salesforce|servicenow|hubspot|yellow\\.ai|intercom|zoho|ibm watson|google dialogflow|microsoft bot framework|uipath|automation anywhere)',
        source: 'message',
        action: 'log_competitor_mention',
        confidence: 0.9
      }
    ],
    actions: {},
    safety: { max_updates_per_minute: 10, cooldown_after_error_seconds: 300, allowed_paths: ['MEMORY/**'], forbidden_paths: [] }
  };
}

const MEMORY_DIR = join(WORKSPACE_ROOT, 'MEMORY');
const BACKUP_DIR = join(WORKSPACE_ROOT, 'data', 'backups');
const APPROVED_CHANGES_FILE = join(MEMORY_DIR, 'approved_changes.json');
let changeCount = 0;

// Load persisted change count
if (existsSync(APPROVED_CHANGES_FILE)) {
  try {
    const data = JSON.parse(readFileSync(APPROVED_CHANGES_FILE, 'utf-8'));
    changeCount = data.count || 0;
  } catch {}
}

// ============== Safety Utilities ==============

function ensureDirSync(dir: string): void {
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}

function backupFile(filePath: string, keepVersions = 10): string {
  if (!existsSync(filePath)) return '';
  const backupId = Date.now().toString();
  const backupDir = join(BACKUP_DIR, basename(filePath));
  ensureDirSync(backupDir);
  const backupPath = join(backupDir, `${backupId}.json`);
  copyFileSync(filePath, backupPath);
  
  const backups = readdirSync(backupDir).sort();
  if (backups.length > keepVersions) {
    for (const old of backups.slice(0, backups.length - keepVersions)) {
      try { unlinkSync(join(backupDir, old)); } catch {}
    }
  }
  return backupId;
}

function isPathAllowed(filePath: string): boolean {
  for (const pattern of rulesConfig.safety.forbidden_paths) {
    const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
    if (regex.test(filePath)) return false;
  }
  if (rulesConfig.safety.allowed_paths.length > 0) {
    for (const pattern of rulesConfig.safety.allowed_paths) {
      const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
      if (regex.test(filePath)) return true;
    }
    return false;
  }
  return true;
}

function writeJsonSafe(filePath: string, data: any): boolean {
  if (!isPathAllowed(filePath)) {
    console.error('[Autonomy] Path not allowed:', filePath);
    return false;
  }
  
  try {
    const backupId = backupFile(filePath);
    const dir = dirname(filePath);
    ensureDirSync(dir);
    writeFileSync(filePath, JSON.stringify(data, null, 2) + '\n', 'utf-8');
    logAudit('file_write', { file: filePath, backupId, keys: Object.keys(data) });
    return true;
  } catch (err) {
    console.error('[Autonomy] Write failed:', filePath, err);
    return false;
  }
}

function logAudit(action: string, details: any): void {
  const auditFile = join(MEMORY_DIR, 'audit_log.json');
  let audit = { entries: [] };
  if (existsSync(auditFile)) {
    try { audit = JSON.parse(readFileSync(auditFile, 'utf-8')); } catch {}
  }
  audit.entries.push({ timestamp: new Date().toISOString(), action, ...details });
  if (audit.entries.length > 1000) audit.entries = audit.entries.slice(-1000);
  try { writeFileSync(auditFile, JSON.stringify(audit, null, 2) + '\n', 'utf-8'); } catch {}
}

// ============== Update Functions ==============

export function getActivePersona(): string {
  try {
    const p = JSON.parse(readFileSync(join(MEMORY_DIR, 'active_persona.json'), 'utf-8'));
    return p.current_persona || 'solution_consultant';
  } catch {
    return 'solution_consultant';
  }
}

export function switchPersona(persona: string, reason: string, ruleId?: string): boolean {
  if (!['solution_consultant', 'account_executive'].includes(persona)) return false;
  
  const current = getActivePersona();
  if (current === persona) return true;
  
  if (rulesConfig.approval_mode && changeCount < rulesConfig.max_approvals_before_autonomous) {
    console.log(`[Autonomy] Approval needed: switch ${current} → ${persona} (${reason}) - conversation event`);
    changeCount++;
  }
  
  const filePath = join(MEMORY_DIR, 'active_persona.json');
  const newData = {
    current_persona: persona,
    last_switched: new Date().toISOString(),
    personas_available: ['solution_consultant', 'account_executive']
  };
  
  if (writeJsonSafe(filePath, newData)) {
    const logPath = join(MEMORY_DIR, 'persona_switch_log.json');
    let log = { switches: [], last_updated: '' };
    if (existsSync(logPath)) {
      try { log = JSON.parse(readFileSync(logPath, 'utf-8')); } catch {}
    }
    log.switches.push({ timestamp: new Date().toISOString(), from: current, to: persona, reason, ruleId });
    log.last_updated = new Date().toISOString();
    writeFileSync(logPath, JSON.stringify(log, null, 2) + '\n', 'utf-8');
    console.log(`[Autonomy] Persona switched: ${current} → ${persona}`);
    return true;
  }
  return false;
}

export function updatePatterns(persona: string, updates: Record<string, any>, source?: string): boolean {
  const patternFile = join(MEMORY_DIR, 'patterns', `${persona}_patterns.json`);
  const current = existsSync(patternFile) ? JSON.parse(readFileSync(patternFile, 'utf-8')) : {};
  
  const merged = deepMerge(current, updates);
  if (writeJsonSafe(patternFile, merged)) {
    console.log(`[Autonomy] Patterns updated for ${persona}:`, Object.keys(updates).join(', '));
    return true;
  }
  return false;
}

function deepMerge(target: any, source: any): any {
  const output = { ...target };
  if (isObject(target) && isObject(source)) {
    Object.keys(source).forEach(key => {
      if (isObject(source[key])) {
        if (!(key in target)) Object.assign(output, { [key]: source[key] });
        else output[key] = deepMerge(target[key], source[key]);
      } else {
        Object.assign(output, { [key]: source[key] });
      }
    });
  }
  return output;
}

function isObject(item: any): boolean {
  return item && typeof item === 'object' && !Array.isArray(item);
}

export function logCompetitor(competitor: string, messageId: number): void {
  const logPath = join(MEMORY_DIR, 'competitor_mentions.json');
  let log = { mentions: [] };
  if (existsSync(logPath)) {
    try { log = JSON.parse(readFileSync(logPath, 'utf-8')); } catch {}
  }
  log.mentions.push({
    competitor: competitor.toLowerCase(),
    message_id: messageId,
    timestamp: new Date().toISOString()
  });
  try { writeFileSync(logPath, JSON.stringify(log, null, 2) + '\n', 'utf-8'); } catch {}
}

export function getDateBasedPath(persona: string, type: 'sessions' | 'patterns' | 'skills_used'): string {
  const now = new Date();
  const year = now.getFullYear().toString();
  const month = now.toLocaleString('default', { month: 'long', year: 'numeric' });
  return join(MEMORY_DIR, year, month, persona, type);
}

export function archiveSession(session: any, persona: string): void {
  const dir = getDateBasedPath(persona, 'sessions');
  ensureDirSync(dir);
  const filename = `${Date.now()}.json`;
  const filePath = join(dir, filename);
  
  session.persona = persona;
  session.archived_at = new Date().toISOString();
  
  try {
    writeFileSync(filePath, JSON.stringify(session, null, 2) + '\n', 'utf-8');
    console.log(`[Autonomy] Session archived: ${filePath}`);
  } catch (err) {
    console.error('[Autonomy] Archive failed:', err);
  }
}

// ============== Rule Engine ==============

export function evaluateRules(message: string, persona: string, messageId: number): void {
  for (const rule of rulesConfig.triggers) {
    if (rule.source && rule.source !== 'message') continue;
    if (!rule.pattern) continue;
    
    const regex = new RegExp(rule.pattern, 'i');
    if (regex.test(message)) {
      executeRule(rule, message, persona, messageId);
    }
  }
}

function executeRule(rule: Rule, message: string, persona: string, messageId: number): void {
  try {
    const { action } = rule;
    
    // Extract target persona from action if it's a switch
    if (action.startsWith('switch_persona ')) {
      const target = action.split(' ')[1];
      if (['solution_consultant', 'account_executive'].includes(target)) {
        switchPersona(target, `rule: ${rule.id}`, rule.id);
      }
    }
    else if (action === 'log_competitor_mention') {
      // Extract competitor from the pattern match
      const match = message.match(new RegExp(rule.pattern, 'i'));
      if (match && match[0]) {
        logCompetitor(match[0], messageId);
      }
    }
    else if (action === 'archive_session') {
      archiveSession({ message_trigger: message }, persona);
    }
  } catch (err) {
    console.error('[Autonomy] Rule execution failed:', rule.id, err);
  }
}

// ============== Insight Extraction ==============

export function extractInsights(message: string): any {
  const lower = message.toLowerCase();
  const insight: any = {
    interests: [],
    dislikes: [],
    skills_referenced: [],
    competitors_mentioned: [],
    urgency: 'low',
    summary: message.slice(0, 50)
  };
  
  if (/yellow\.ai|conversational ai|bot studio|agent assist/.test(lower)) insight.persona_cue = 'account_executive';
  if (/demo|architecture|integration|technical|presales|solution consultant/.test(lower)) insight.persona_cue = 'solution_consultant';
  if (/love|like|excited|new.*ai|openai|claude|gpt|llm|anthropic/.test(lower)) insight.interests.push('ai_enthusiast');
  if (/(no )?bs|bullshit|zero tolerance|ruthless/.test(lower)) insight.dislikes.push('inefficiency');
  
  // Skills detection
  const skillMap: Record<string, string[]> = {
    'battlecards': ['battlecards', 'competitive', 'battle'],
    'demo_strategy': ['demo', 'demonstration'],
    'deal_meddpicc': ['meddpicc', 'deal qualification'],
    'value_architecture': ['value', 'roi', 'tco'],
    'risk_report': ['risk', 'assessment']
  };
  for (const [skill, keywords] of Object.entries(skillMap)) {
    if (keywords.some(k => lower.includes(k))) {
      insight.skills_referenced.push(skill);
    }
  }
  
        // Competitor detection (list from rules)
        const competitorRegex = /(zendesk|salesforce|servicenow|hubspot|yellow\\.ai|intercom|zoho|ibm watson|google dialogflow|microsoft bot framework|uipath|automation anywhere)/i;
        const matches = message.match(competitorRegex);
        if (matches) insight.competitors_mentioned = matches.map((m: string) => m.toLowerCase());
  
  return insight;
}

// ============== Main Polling Loop ==============

let lastSeen = Date.now();
let dbInstance: ConversationDB | null = null;

export function startAutonomy(db: any): void {
  dbInstance = db;
  
  // Initial poll immediately
  pollMessages().catch(console.error);
  
  // Then poll every 60 seconds
  const intervalId = setInterval(() => {
    pollMessages().catch(console.error);
  }, 60000);
  
  // Persist change count every minute
  const saveInterval = setInterval(() => {
    try {
      writeFileSync(APPROVED_CHANGES_FILE, JSON.stringify({ count: changeCount, updated: new Date().toISOString() }, null, 2));
    } catch {}
  }, 60000);
  
  console.error('[Autonomy] Started monitoring OpenCode and Claude conversations (polling every 60s, approval threshold:', rulesConfig.max_approvals_before_autonomous, ')');
}

async function pollMessages(): Promise<void> {
  if (!dbInstance) return;
  
  try {
    const newMessages: any[] = await dbInstance.getMessageFromTime(lastSeen, WORKSPACE_ROOT);
    if (newMessages.length > 0) {
      lastSeen = (newMessages[newMessages.length - 1].time_created) as number;
      
      for (const msg of newMessages) {
        const content = (msg.data && (msg.data.content || msg.data.text)) || '';
        if (!content) continue;
        
        const insight = extractInsights(content);
        const persona = getActivePersona();
        
        // Apply rules
        evaluateRules(content, persona, msg.id);
        
        // Persona switch from LLM cue
        if (insight.persona_cue && insight.persona_cue !== persona) {
          switchPersona(insight.persona_cue, `LLM cue: ${insight.persona_cue}`);
        }
        
        // Update patterns
        const updates: Record<string, any> = {};
        if (insight.interests?.length) updates.technical = { interests: insight.interests };
        if (insight.dislikes?.length) updates.personality = { dislikes: insight.dislikes };
        if (insight.skills_referenced?.length) updates.skills = { used: insight.skills_referenced };
        if (Object.keys(updates).length > 0) {
          updatePatterns(persona, updates);
        }
        
        // Log competitors
        for (const comp of (insight.competitors_mentioned || [])) {
          logCompetitor(comp, msg.id);
        }
        
        // Session archiving (heuristic)
        if (/session ended|closing|that's all|goodbye/i.test(content)) {
          archiveSession({ message: content, insight }, persona);
        }
      }
    }
  } catch (err) {
    console.error('[Autonomy] Poll error:', err.message);
  }
}

// Export for MCP tools
export function getStatus() {
  return {
    running: true,
    changeCount,
    approvalsRemaining: rulesConfig.approval_mode ? Math.max(0, rulesConfig.max_approvals_before_autonomous - changeCount) : 'unlimited',
    lastPoll: new Date(lastSeen).toISOString(),
    currentPersona: getActivePersona()
  };
}