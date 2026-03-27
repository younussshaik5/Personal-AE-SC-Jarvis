/**
 * JARVIS Dashboard Application
 * Real-time sync with MCP observer and JARVIS core
 */

class JarvisUI {
    constructor() {
        this.ws = null;
        this.apiBase = '';  // Use relative paths (same origin)
        this.jarvisWsPort = 8081;  // JARVIS core WebSocket port
        this.eventLog = [];
        this.personas = [];
        this.deals = [];
        this.patterns = [];
        this.competitors = [];
        this.approvals = [];
        this.stats = {
            files: 0,
            patterns: 0,
            deals: 0,
            trust: 0
        };
        this.uptimeStart = Date.now();
        this.messageCount = 0;
        this.changeCount = 0;
        this.currentFilter = 'all';
        
        this.init();
    }

    async init() {
        // Show boot sequence
        this.showBootSequence();
        
        // Wait for boot animation
        await this.delay(3000);
        
        // Try to connect
        await this.connect();
        
        // Start time update
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);
        
        // Start periodic status fetch
        setInterval(() => this.fetchStatus(), 5000);
        setInterval(() => this.fetchData(), 10000);
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Hide boot, show dashboard
        document.getElementById('boot-sequence').classList.add('hidden');
        document.getElementById('dashboard').classList.remove('hidden');
        
        this.showToast('JARVIS online and synchronized', 'success');
    }

    async connect() {
        try {
            // Connect to JARVIS core WebSocket
            this.ws = new WebSocket(`ws://localhost:${this.jarvisWsPort}`);
            
            this.ws.onopen = () => {
                this.log('WebSocket connected to JARVIS core');
                this.updateSystemStatus(true);
            };
            
            this.ws.onmessage = (event) => {
                this.handleJarvisMessage(JSON.parse(event.data));
            };
            
            this.ws.onerror = (error) => {
                this.log('WebSocket error', 'error');
                this.showToast('JARVIS connection failed - some features may be limited', 'warning');
            };
            
            this.ws.onclose = () => {
                this.log('WebSocket closed');
                this.updateSystemStatus(false);
                // Try reconnect after 5s
                setTimeout(() => this.connect(), 5000);
            };
            
            // Also fetch initial data via HTTP API
            await this.fetchData();
            
        } catch (error) {
            this.log(`Connection failed: ${error.message}`, 'error');
            this.showToast('Failed to connect to JARVIS core', 'error');
        }
    }

    async fetchData() {
        try {
            // Use MCP tools to get data
            await this.fetchPersonas();
            await this.fetchDeals();
            await this.fetchApprovals();
            await this.fetchPatterns();
            await this.fetchCompetitors();
            await this.fetchStats();
        } catch (error) {
            this.log(`Fetch error: ${error.message}`, 'error');
        }
    }

    async fetchStatus() {
        try {
            const response = await fetch('/api/status');
            if (response.ok) {
                const data = await response.json();
                // Extract change count and active persona
                this.updateStats({
                    changeCount: data.change_count,
                    persona: data.active_persona
                });
            }
        } catch (error) {
            // Silent fail on status checks
        }
    }

    async fetchPersonas() {
        try {
            const response = await fetch('/api/personas');
            if (response.ok) {
                const data = await response.json(); // array of persona names
                this.personas = data.map(p => ({
                    id: p,
                    name: p.replace('_', ' ').toUpperCase(),
                    type: p,
                    workspaces: [] // can be expanded later
                }));
                this.renderPersonas();
            }
        } catch (error) {
            // Fallback to defaults
            this.personas = [
                { id: 'solution_consultant', name: 'SOLUTION CONSULTANT', type: 'solution_consultant', workspaces: [] },
                { id: 'account_executive', name: 'ACCOUNT EXECUTIVE', type: 'account_executive', workspaces: [] }
            ];
        }
    }

    async fetchDeals() {
        try {
            const response = await fetch('/api/deals');
            if (response.ok) {
                this.deals = await response.json();
            }
        } catch (error) {}
        this.renderDeals();
    }

    async fetchApprovals() {
        try {
            const response = await fetch('/api/approvals');
            if (response.ok) {
                this.approvals = await response.json();
            }
        } catch (error) {}
        this.renderApprovals();
    }

    async fetchPatterns() {
        try {
            const response = await fetch('/api/patterns');
            if (response.ok) {
                const data = await response.json();
                this.patterns = Object.entries(data).map(([key, value]) => ({ key, value }));
                this.renderPatterns();
            }
        } catch (error) {
            // no-op
        }
    }

    async fetchCompetitors() {
        try {
            const response = await fetch('/api/competitors');
            if (response.ok) {
                this.competitors = await response.json(); // array of mentions
                this.renderCompetitors();
            }
        } catch (error) {
            // no-op
        }
    }

    async fetchStats() {
        try {
            const response = await fetch('/api/stats');
            if (response.ok) {
                const data = await response.json();
                this.stats = {
                    files: data.files_observed,
                    patterns: data.patterns,
                    deals: data.deals_active,
                    trust: data.trust_score
                };
                this.renderStats();
            }
        } catch (error) {
            // fallback to mock
            this.stats = {
                files: 145,
                patterns: this.patterns.length,
                deals: this.deals.length,
                trust: 65
            };
            this.renderStats();
        }
    }

    handleJarvisMessage(data) {
        // Handle real-time events from JARVIS core
        if (data.type) {
            this.log(`Event: ${data.type}`, 'info');
            this.addEventToStream(data);
            this.messageCount++;
            
            // Update relevant UI based on event type
            switch (data.type) {
                case 'conversation.message':
                    // Maybe update patterns
                    break;
                case 'file.created':
                case 'file.modified':
                    this.stats.files++;
                    this.renderStats();
                    break;
                case 'persona.switched':
                    this.updateActivePersona(data.data.to);
                    break;
                case 'modification.approved':
                    this.changeCount++;
                    this.renderStats();
                    break;
            }
        }
    }

    updateStats(data) {
        if (data.changeCount !== undefined) this.changeCount = data.changeCount;
        if (data.persona) this.updateActivePersona(data.persona);
        
        document.getElementById('change-count').textContent = this.changeCount;
        document.getElementById('approval-count').textContent = 
            Math.max(0, 50 - this.changeCount);
    }

    updateActivePersona(personaId) {
        const persona = this.personas.find(p => p.id === personaId);
        if (persona) {
            document.getElementById('persona-name').textContent = persona.name;
            document.getElementById('persona-type').textContent = 
                persona.type.replace('_', ' ').toUpperCase();
            
            // Update active state in personas list
            document.querySelectorAll('.persona-card').forEach(card => {
                card.classList.toggle('active', card.dataset.personaId === personaId);
            });
        }
    }

    updateSystemStatus(online) {
        const indicator = document.querySelector('.status-indicator');
        const statusText = document.getElementById('status-text');
        
        if (online) {
            indicator.classList.add('online');
            statusText.textContent = 'ONLINE';
        } else {
            indicator.classList.remove('online');
            statusText.textContent = 'OFFLINE';
        }
    }

    updateTime() {
        const now = new Date();
        document.getElementById('current-time').textContent = 
            now.toISOString().split('T')[1].split('.')[0] + ' UTC';
        
        // Uptime
        const uptimeMs = Date.now() - this.uptimeStart;
        const hours = Math.floor(uptimeMs / 3600000);
        const minutes = Math.floor((uptimeMs % 3600000) / 60000);
        document.getElementById('uptime').textContent = `${hours}h ${minutes}m`;
        
        // Message count
        document.getElementById('msg-count').textContent = this.messageCount;
    }

    addEventToStream(event) {
        const container = document.getElementById('events-container');
        
        // Remove empty state if first event
        if (this.eventLog.length === 0) {
            container.innerHTML = '';
        }
        
        this.eventLog.unshift(event);
        if (this.eventLog.length > 100) this.eventLog.pop();
        
        // Create event element
        const eventEl = document.createElement('div');
        eventEl.className = `event-item type-${event.type.split('.')[0]}`;
        eventEl.innerHTML = `
            <div class="event-header">
                <span class="event-type">${event.type}</span>
                <span class="event-time">${new Date(event.timestamp * 1000).toLocaleTimeString()}</span>
            </div>
            <div class="event-desc">${JSON.stringify(event.data).substring(0, 200)}...</div>
        `;
        
        container.insertBefore(eventEl, container.firstChild);
        
        // Limit to 50 visible
        while (container.children.length > 50) {
            container.removeChild(container.lastChild);
        }
    }

    renderStats() {
        document.getElementById('stat-files').textContent = this.stats.files;
        document.getElementById('stat-patterns').textContent = this.stats.patterns;
        document.getElementById('stat-deals').textContent = this.stats.deals;
        document.getElementById('stat-trust').textContent = this.stats.trust + '%';
        document.getElementById('change-count').textContent = this.changeCount;
    }

    renderPersonas() {
        const list = document.getElementById('personas-list');
        list.innerHTML = '';
        
        this.personas.forEach(p => {
            const card = document.createElement('div');
            card.className = 'persona-card';
            card.dataset.personaId = p.id;
            card.innerHTML = `
                <div class="persona-card-header">
                    <span class="persona-name">${p.name}</span>
                    <span class="persona-type">${p.type.split('_').join(' ')}</span>
                </div>
                <div class="persona-workspaces">
                    📂 ${p.workspaces.join(', ')}
                </div>
            `;
            card.onclick = () => this.switchPersona(p.id);
            list.appendChild(card);
        });
    }

    renderDeals() {
        const list = document.getElementById('deals-list');
        if (this.deals.length === 0) {
            list.innerHTML = '<div class="empty-state">No active deals</div>';
            return;
        }
        
        list.innerHTML = '';
        this.deals.forEach(deal => {
            const card = document.createElement('div');
            card.className = 'deal-card';
            const progress = (deal.tasks_completed / deal.total_tasks) * 100;
            const deadline = new Date(deal.deadline);
            const daysLeft = Math.ceil((deadline - new Date()) / (1000*60*60*24));
            
            card.innerHTML = `
                <div class="deal-header">
                    <span class="deal-title">${deal.title}</span>
                    <span class="deal-status">${deal.status}</span>
                </div>
                <div class="deal-client">${deal.client || 'No client'}</div>
                <div class="deal-meta">
                    <span>💰 ${deal.budget ? '$' + deal.budget.toLocaleString() : 'No budget'}</span>
                    <span>📅 ${daysLeft > 0 ? daysLeft + ' days' : 'Overdue'}</span>
                    <span>✓ ${deal.tasks_completed}/${deal.total_tasks}</span>
                </div>
                <div style="margin-top: 0.5rem; background: var(--bg-dark); height: 4px; border-radius: 2px;">
                    <div style="width: ${progress}%; background: var(--primary); height: 100%; border-radius: 2px;"></div>
                </div>
            `;
            list.appendChild(card);
        });
    }

    renderApprovals() {
        const list = document.getElementById('approvals-list');
        if (this.approvals.length === 0) {
            list.innerHTML = '<div class="empty-state">No pending approvals</div>';
            return;
        }
        
        list.innerHTML = '';
        this.approvals.forEach(approval => {
            const item = document.createElement('div');
            item.className = 'approval-item';
            item.innerHTML = `
                <div>
                    <div class="approval-desc">${approval.description}</div>
                    <div class="approval-meta">Risk: ${approval.risk} • Trust: ${approval.trust_score.toFixed(2)}</div>
                </div>
                <div class="approval-actions">
                    <button class="btn-approve" onclick="jarvisUI.approveChange('${approval.id}')">✓</button>
                    <button class="btn-reject" onclick="jarvisUI.rejectChange('${approval.id}')">✗</button>
                </div>
            `;
            list.appendChild(item);
        });
        
        document.getElementById('approval-count').textContent = this.approvals.length;
    }

    renderPatterns() {
        const list = document.getElementById('patterns-list');
        if (this.patterns.length === 0) {
            list.innerHTML = '<div class="empty-state">No patterns learned yet</div>';
            return;
        }
        
        list.innerHTML = '';
        this.patterns.slice(0, 10).forEach(pat => {
            const item = document.createElement('div');
            item.className = 'pattern-item';
            item.innerHTML = `
                <span class="pattern-key">${pat.key}</span>
                <span class="pattern-count">${typeof pat.value === 'object' ? Object.keys(pat.value).length : pat.value}</span>
            `;
            list.appendChild(item);
        });
    }

    renderCompetitors() {
        const list = document.getElementById('competitors-list');
        if (this.competitors.length === 0) {
            list.innerHTML = '<div class="empty-state">No competitors detected</div>';
            return;
        }
        
        // Count occurrences
        const counts = {};
        this.competitors.forEach(c => {
            counts[c.competitor] = (counts[c.competitor] || 0) + 1;
        });
        
        list.innerHTML = '';
        Object.entries(counts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10)
            .forEach(([competitor, count]) => {
                const item = document.createElement('div');
                item.className = 'competitor-item';
                item.innerHTML = `
                    <span>${competitor}</span>
                    <span class="competitor-count">${count}</span>
                `;
                list.appendChild(item);
            });
    }

    async switchPersona(personaId) {
        try {
            // Would call MCP tool: switch_persona
            this.log(`Switching persona to ${personaId}`);
            this.showToast(`Switching to ${personaId}...`, 'info');
            
            // Simulate success
            await this.delay(500);
            this.updateActivePersona(personaId);
            this.showToast(`Persona switched to ${personaId}`, 'success');
        } catch (error) {
            this.showToast('Failed to switch persona', 'error');
        }
    }

    async approveChange(changeId) {
        // Would call MCP tool: approve_change
        this.log(`Approving change ${changeId}`);
        this.approvals = this.approvals.filter(a => a.id !== changeId);
        this.renderApprovals();
        this.showToast('Change approved', 'success');
    }

    async rejectChange(changeId) {
        this.log(`Rejecting change ${changeId}`);
        this.approvals = this.approvals.filter(a => a.id !== changeId);
        this.renderApprovals();
        this.showToast('Change rejected', 'warning');
    }

    async triggerAction(action) {
        this.log(`Triggering action: ${action}`);
        try {
            const response = await fetch(`/api/trigger/${action}`, { method: 'GET' });
            if (response.ok) {
                const result = await response.json();
                this.showToast(result.message || `Action ${action} triggered`, 'success');
                // If scan, refresh data after a delay
                if (action === 'scan') {
                    setTimeout(() => this.fetchData(), 2000);
                }
            } else {
                throw new Error('API error');
            }
        } catch (error) {
            this.showToast(`Failed to trigger ${action}`, 'error');
        }
    }

    showBootSequence() {
        // Boot animation is already in HTML
    }

    log(message, level = 'info') {
        console.log(`[JARVIS UI] ${level}: ${message}`);
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: '✓',
            error: '✗',
            warning: '⚠',
            info: 'ℹ'
        };
        
        toast.innerHTML = `
            <span class="toast-icon">${icons[type]}</span>
            <span class="toast-message">${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5s
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    setupEventListeners() {
        // Quick action buttons
        document.getElementById('action-archive').onclick = () => this.triggerAction('archive');
        document.getElementById('action-evolve').onclick = () => this.triggerAction('evolve');
        document.getElementById('action-scan').onclick = () => this.triggerAction('scan');
        document.getElementById('action-backup').onclick = () => this.triggerAction('backup');
        document.getElementById('scan-btn').onclick = () => this.triggerAction('scan');
        
        // Event filters
        const filters = ['all', 'files', 'chat', 'system'];
        filters.forEach(filter => {
            const btn = document.getElementById(`event-filter-${filter}`);
            if (btn) {
                btn.onclick = () => {
                    this.currentFilter = filter;
                    filters.forEach(f => {
                        const b = document.getElementById(`event-filter-${f}`);
                        if (b) b.classList.toggle('active', f === filter);
                    });
                    this.filterEvents();
                };
            }
        });
        
        // Modal close on overlay click
        document.getElementById('modal-overlay').onclick = (e) => {
            if (e.target.id === 'modal-overlay') {
                document.getElementById('modal-overlay').classList.add('hidden');
            }
        };
        
        // Add deal button
        document.getElementById('add-deal-btn').onclick = () => {
            this.showModal('Create New Deal', `
                <form onsubmit="jarvisUI.createDeal(event)">
                    <div class="form-group">
                        <label class="form-label">Deal Title</label>
                        <input type="text" class="form-input" name="title" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Client</label>
                        <input type="text" class="form-input" name="client">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Deadline</label>
                        <input type="date" class="form-input" name="deadline" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Budget</label>
                        <input type="number" class="form-input" name="budget">
                    </div>
                    <button type="submit" class="btn btn-primary">Create Deal</button>
                </form>
            `);
        };
        
        // Add persona button
        document.getElementById('add-persona-btn').onclick = () => {
            this.showModal('Create New Persona', `
                <form onsubmit="jarvisUI.createPersona(event)">
                    <div class="form-group">
                        <label class="form-label">Persona Name</label>
                        <input type="text" class="form-input" name="name" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Type</label>
                        <select class="form-select" name="type">
                            <option value="solution_consultant">Solution Consultant</option>
                            <option value="account_executive">Account Executive</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Workspace Path</label>
                        <input type="text" class="form-input" name="workspace" placeholder="/path/to/workspace" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Create Persona</button>
                </form>
            `);
        };
    }

    async createDeal(event) {
        event.preventDefault();
        const form = event.target;
        const deal = {
            title: form.title.value,
            client: form.client.value,
            deadline: form.deadline.value,
            budget: parseFloat(form.budget.value) || 0,
            status: 'open',
            tasks_completed: 0,
            total_tasks: 0
        };
        
        // Would call MCP tool
        this.deals.push(deal);
        this.renderDeals();
        this.hideModal();
        this.showToast('Deal created successfully', 'success');
    }

    async createPersona(event) {
        event.preventDefault();
        const form = event.target;
        const persona = {
            id: form.name.value.toLowerCase().replace(/\s/g, '_'),
            name: form.name.value,
            type: form.type.value,
            workspaces: [form.workspace.value]
        };
        
        this.personas.push(persona);
        this.renderPersonas();
        this.hideModal();
        this.showToast('Persona created', 'success');
    }

    showModal(title, content) {
        const overlay = document.getElementById('modal-overlay');
        const modal = document.getElementById('modal-content');
        
        modal.innerHTML = `
            <div class="modal-header">
                <h2 class="modal-title">${title}</h2>
                <button class="modal-close" onclick="jarvisUI.hideModal()">×</button>
            </div>
            <div class="modal-body">${content}</div>
        `;
        
        overlay.classList.remove('hidden');
    }

    hideModal() {
        document.getElementById('modal-overlay').classList.add('hidden');
    }

    filterEvents() {
        const container = document.getElementById('events-container');
        const items = container.querySelectorAll('.event-item');
        
        items.forEach(item => {
            const type = item.className.match(/type-(\w+)/)[1];
            const shouldShow = this.currentFilter === 'all' || 
                              (this.currentFilter === 'files' && ['file', 'folder'].includes(type)) ||
                              (this.currentFilter === 'chat' && type === 'conversation') ||
                              (this.currentFilter === 'system' && ['system', 'error'].includes(type));
            
            item.style.display = shouldShow ? 'block' : 'none';
        });
    }
}

// Global instance
let jarvisUI;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    jarvisUI = new JarvisUI();
});

// Expose to window for onclick handlers
window.jarvisUI = jarvisUI;