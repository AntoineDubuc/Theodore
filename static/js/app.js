// Theodore Web UI - Modern JavaScript

class TheodoreUI {
    constructor() {
        this.initializeEventListeners();
        this.setupFormValidation();
        this.initializeAnimations();
    }

    initializeEventListeners() {
        // Main search form
        const searchForm = document.getElementById('searchForm');
        if (searchForm) {
            searchForm.addEventListener('submit', this.handleDiscovery.bind(this));
        }

        // Process company form
        const processForm = document.getElementById('processForm');
        if (processForm) {
            processForm.addEventListener('submit', this.handleProcessing.bind(this));
        }

        // Real-time search
        const companyInput = document.getElementById('companyName');
        if (companyInput) {
            let searchTimeout;
            companyInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.handleRealTimeSearch(e.target.value);
                }, 300);
            });
        }

        // Tab switching
        const tabs = document.querySelectorAll('.tab-button');
        tabs.forEach(tab => {
            tab.addEventListener('click', this.handleTabSwitch.bind(this));
        });
    }

    setupFormValidation() {
        const inputs = document.querySelectorAll('.form-input');
        inputs.forEach(input => {
            input.addEventListener('blur', this.validateInput.bind(this));
            input.addEventListener('input', this.clearValidationErrors.bind(this));
        });
    }

    initializeAnimations() {
        // Stagger animation for cards
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('fade-in-up');
        });

        // Parallax background effect
        this.setupParallax();
    }

    setupParallax() {
        let ticking = false;

        function updateParallax() {
            const scrolled = window.pageYOffset;
            const parallax = document.querySelector('body::before');
            
            if (parallax) {
                const yPos = -(scrolled * 0.5);
                parallax.style.transform = `translateY(${yPos}px)`;
            }
            
            ticking = false;
        }

        function requestTick() {
            if (!ticking) {
                requestAnimationFrame(updateParallax);
                ticking = true;
            }
        }

        window.addEventListener('scroll', requestTick);
    }

    async handleDiscovery(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const companyName = formData.get('company_name');
        const limit = formData.get('limit') || 5;

        if (!companyName.trim()) {
            this.showError('Please enter a company name');
            return;
        }

        const submitBtn = event.target.querySelector('button[type="submit"]');
        this.setButtonLoading(submitBtn, true);
        this.clearMessages();

        try {
            const response = await fetch('/api/discover', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    company_name: companyName,
                    limit: parseInt(limit)
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.displayResults(data);
                this.showSuccess(`Found ${data.total_found} similar companies for ${data.target_company}`);
            } else {
                this.showError(data.error || 'Discovery failed');
                if (data.suggestion) {
                    this.showInfo(data.suggestion);
                }
            }

        } catch (error) {
            this.showError('Network error occurred. Please try again.');
            console.error('Discovery error:', error);
        } finally {
            this.setButtonLoading(submitBtn, false);
        }
    }

    async handleProcessing(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const companyName = formData.get('company_name');
        const website = formData.get('website');

        if (!companyName.trim() || !website.trim()) {
            this.showError('Please enter both company name and website');
            return;
        }

        const submitBtn = event.target.querySelector('button[type="submit"]');
        this.setButtonLoading(submitBtn, true);
        this.clearMessages();

        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    company_name: companyName,
                    website: website
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showProcessingResult(data);
                this.showSuccess(`Successfully processed ${data.company_name}`);
            } else {
                this.showError(data.error || 'Processing failed');
            }

        } catch (error) {
            this.showError('Network error occurred. Please try again.');
            console.error('Processing error:', error);
        } finally {
            this.setButtonLoading(submitBtn, false);
        }
    }

    async handleRealTimeSearch(query) {
        if (!query.trim() || query.length < 2) {
            this.hideSearchSuggestions();
            return;
        }

        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (response.ok && data.results.length > 0) {
                this.showSearchSuggestions(data.results);
            } else {
                this.hideSearchSuggestions();
            }

        } catch (error) {
            console.error('Search error:', error);
            this.hideSearchSuggestions();
        }
    }

    handleTabSwitch(event) {
        const tabButton = event.target;
        const tabId = tabButton.dataset.tab;

        // Update active tab button
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        tabButton.classList.add('active');

        // Update active tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        const targetTab = document.getElementById(tabId);
        if (targetTab) {
            targetTab.classList.add('active');
        }
    }

    displayResults(data) {
        const resultsContainer = document.getElementById('results');
        const resultsSection = document.getElementById('resultsSection');

        if (!resultsContainer || !resultsSection) return;

        if (data.results.length === 0) {
            resultsContainer.innerHTML = this.createEmptyState();
        } else {
            resultsContainer.innerHTML = data.results.map(result => 
                this.createResultCard(result)
            ).join('');
        }

        resultsSection.classList.remove('hidden');
        
        // Animate result cards
        setTimeout(() => {
            const cards = resultsContainer.querySelectorAll('.result-card');
            cards.forEach((card, index) => {
                setTimeout(() => {
                    card.classList.add('fade-in-up');
                }, index * 100);
            });
        }, 100);
    }

    createResultCard(result) {
        const scoreClass = result.similarity_score >= 0.8 ? 'high' : 
                          result.similarity_score >= 0.6 ? 'medium' : 'low';

        return `
            <div class="result-card" data-score="${scoreClass}">
                <div class="result-header">
                    <div>
                        <div class="result-company">${this.escapeHtml(result.company_name)}</div>
                        <div class="result-type">${this.escapeHtml(result.relationship_type || 'Similar Company')}</div>
                    </div>
                    <div class="result-score">
                        <div class="score-value">${(result.similarity_score * 100).toFixed(0)}%</div>
                        <div class="score-label">Match</div>
                    </div>
                </div>
                ${result.reasoning && result.reasoning.length > 0 ? `
                    <div class="result-reasons">
                        ${result.reasoning.map(reason => 
                            `<span class="reason-tag">${this.escapeHtml(reason)}</span>`
                        ).join('')}
                    </div>
                ` : ''}
                <div class="result-meta">
                    <small class="text-muted">
                        Confidence: ${(result.confidence * 100).toFixed(0)}% • 
                        Method: ${this.escapeHtml(result.discovery_method)}
                    </small>
                </div>
            </div>
        `;
    }

    createEmptyState() {
        return `
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <div class="empty-title">No similar companies found</div>
                <div class="empty-description">
                    Try searching for a different company or check if the company exists in our database.
                </div>
            </div>
        `;
    }

    showProcessingResult(data) {
        const modal = this.createModal('Processing Result', `
            <div class="processing-result">
                <div class="result-item">
                    <strong>Company:</strong> ${this.escapeHtml(data.company_name)}
                </div>
                <div class="result-item">
                    <strong>Status:</strong> ${this.escapeHtml(data.status)}
                </div>
                ${data.industry ? `
                    <div class="result-item">
                        <strong>Industry:</strong> ${this.escapeHtml(data.industry)}
                    </div>
                ` : ''}
                ${data.business_model ? `
                    <div class="result-item">
                        <strong>Business Model:</strong> ${this.escapeHtml(data.business_model)}
                    </div>
                ` : ''}
                ${data.summary ? `
                    <div class="result-item">
                        <strong>Summary:</strong> ${this.escapeHtml(data.summary)}
                    </div>
                ` : ''}
            </div>
        `);
        
        document.body.appendChild(modal);
    }

    showSearchSuggestions(results) {
        const input = document.getElementById('companyName');
        const wrapper = input.closest('.input-wrapper');
        
        // Ensure wrapper has proper positioning
        wrapper.style.position = 'relative';
        wrapper.style.zIndex = '10000';
        
        let suggestions = document.getElementById('searchSuggestions');
        if (!suggestions) {
            suggestions = document.createElement('div');
            suggestions.id = 'searchSuggestions';
            suggestions.className = 'search-suggestions';
            wrapper.appendChild(suggestions);
        }

        suggestions.innerHTML = results.map(result => `
            <div class="suggestion-item" data-name="${this.escapeHtml(result.name)}">
                <div class="suggestion-name">${this.escapeHtml(result.name)}</div>
                <div class="suggestion-details">
                    ${result.industry ? `${result.industry} • ` : ''}
                    ${result.business_model || 'Unknown'}
                </div>
            </div>
        `).join('');

        // Add click handlers
        suggestions.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                input.value = item.dataset.name;
                this.hideSearchSuggestions();
            });
        });

        suggestions.classList.add('show');
    }

    hideSearchSuggestions() {
        const suggestions = document.getElementById('searchSuggestions');
        if (suggestions) {
            suggestions.classList.remove('show');
        }
    }

    validateInput(event) {
        const input = event.target;
        const wrapper = input.closest('.input-wrapper');
        
        if (input.hasAttribute('required') && !input.value.trim()) {
            wrapper.classList.add('error');
            this.showFieldError(input, 'This field is required');
        } else if (input.type === 'url' && input.value && !this.isValidUrl(input.value)) {
            wrapper.classList.add('error');
            this.showFieldError(input, 'Please enter a valid URL');
        } else {
            wrapper.classList.remove('error');
            this.hideFieldError(input);
        }
    }

    clearValidationErrors(event) {
        const input = event.target;
        const wrapper = input.closest('.input-wrapper');
        wrapper.classList.remove('error');
        this.hideFieldError(input);
    }

    showFieldError(input, message) {
        let errorEl = input.parentNode.querySelector('.field-error');
        if (!errorEl) {
            errorEl = document.createElement('div');
            errorEl.className = 'field-error';
            input.parentNode.appendChild(errorEl);
        }
        errorEl.textContent = message;
    }

    hideFieldError(input) {
        const errorEl = input.parentNode.querySelector('.field-error');
        if (errorEl) {
            errorEl.remove();
        }
    }

    setButtonLoading(button, isLoading) {
        if (isLoading) {
            button.classList.add('loading');
            button.disabled = true;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
        }
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showInfo(message) {
        this.showMessage(message, 'info');
    }

    showMessage(message, type) {
        const container = document.getElementById('messages');
        if (!container) return;

        const messageEl = document.createElement('div');
        messageEl.className = `${type}-message`;
        messageEl.textContent = message;

        container.appendChild(messageEl);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageEl.remove();
        }, 5000);
    }

    clearMessages() {
        const container = document.getElementById('messages');
        if (container) {
            container.innerHTML = '';
        }
    }

    createModal(title, content) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h3>${this.escapeHtml(title)}</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-content">
                    ${content}
                </div>
            </div>
        `;

        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        return modal;
    }

    isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    async runDemo(companyName = null) {
        const company = companyName || document.getElementById('companyName').value || 'Visterra';
        const limit = document.getElementById('similarLimit').value || 3;

        this.clearMessages();
        
        try {
            const response = await fetch('/api/demo', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    company_name: company,
                    limit: parseInt(limit)
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.displayResults(data);
                this.showSuccess(`Demo: Found ${data.total_found} similar companies for ${data.target_company}`);
                if (data.demo_mode) {
                    this.showInfo('This is demo data. Use "Discover Similar Companies" for real AI analysis.');
                }
            } else {
                this.showError(data.error || 'Demo failed');
            }

        } catch (error) {
            this.showError('Network error occurred. Please try again.');
            console.error('Demo error:', error);
        }
    }
}

// Global function for demo button
function runDemo() {
    const ui = window.theodoreUI || new TheodoreUI();
    ui.runDemo();
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.theodoreUI = new TheodoreUI();
});

// Add additional CSS animations
const style = document.createElement('style');
style.textContent = `
    .fade-in-up {
        opacity: 0;
        transform: translateY(20px);
        animation: fadeInUp 0.6s ease forwards;
    }

    @keyframes fadeInUp {
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .search-suggestions {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--bg-tertiary);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        margin-top: 8px;
        max-height: 200px;
        overflow-y: auto;
        z-index: 9999;
        opacity: 0;
        transform: translateY(-10px);
        transition: all 0.3s ease;
        pointer-events: none;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    .search-suggestions.show {
        opacity: 1;
        transform: translateY(0);
        pointer-events: all;
    }

    .input-wrapper:has(.search-suggestions.show) {
        z-index: 10000;
        position: relative;
    }

    .suggestion-item {
        padding: 12px 16px;
        cursor: pointer;
        transition: background 0.2s ease;
    }

    .suggestion-item:hover {
        background: var(--glass-bg);
    }

    .suggestion-name {
        font-weight: 500;
        color: var(--text-primary);
    }

    .suggestion-details {
        font-size: 0.875rem;
        color: var(--text-muted);
    }

    .field-error {
        color: #f5576c;
        font-size: 0.875rem;
        margin-top: 4px;
    }

    .input-wrapper.error {
        background: linear-gradient(135deg, #f5576c 0%, #fa709a 100%);
    }

    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 2000;
        backdrop-filter: blur(5px);
    }

    .modal {
        background: var(--bg-secondary);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        max-width: 500px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
    }

    .modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px;
        border-bottom: 1px solid var(--border-subtle);
    }

    .modal-close {
        background: none;
        border: none;
        color: var(--text-muted);
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        transition: all 0.2s ease;
    }

    .modal-close:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    .modal-content {
        padding: 20px;
    }

    .processing-result .result-item {
        margin-bottom: 12px;
        padding: 8px 0;
        border-bottom: 1px solid var(--border-subtle);
    }

    .processing-result .result-item:last-child {
        border-bottom: none;
    }
`;
document.head.appendChild(style);