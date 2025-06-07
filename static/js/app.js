// Theodore Web UI - Modern JavaScript

class TheodoreUI {
    constructor() {
        this.initializeEventListeners();
        this.setupFormValidation();
        this.initializeAnimations();
        this.initializeDatabaseBrowser();
    }

    initializeEventListeners() {
        // Main search form
        const searchForm = document.getElementById('searchForm');
        if (searchForm) {
            console.log('Search form found, attaching event listener'); // Debug log
            searchForm.addEventListener('submit', this.handleDiscovery.bind(this));
        } else {
            console.log('Search form NOT found!'); // Debug log
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
            let searchController = null; // To cancel previous requests
            
            companyInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                
                // Cancel previous request if still pending
                if (searchController) {
                    searchController.abort();
                }
                
                searchTimeout = setTimeout(() => {
                    searchController = new AbortController();
                    this.handleRealTimeSearch(e.target.value, searchController);
                }, 300);
            });
            
            // TEMPORARILY DISABLED - Hide suggestions when input loses focus (with small delay to allow clicks)
            // companyInput.addEventListener('blur', () => {
            //     setTimeout(() => {
            //         this.hideSearchSuggestions('input_blur');
            //     }, 150);
            // });
            
            // TEMPORARILY DISABLED ALL CLICK OUTSIDE LOGIC FOR DEBUGGING
            // // Hide suggestions when clicking outside (use a named function to avoid duplicates)
            // this.clickOutsideHandler = (e) => {
            //     const inputWrapper = companyInput.closest('.input-wrapper');
            //     const suggestionsElement = document.getElementById('searchSuggestions');
            //     
            //     // Don't hide if clicking on input, wrapper, or suggestions
            //     if (inputWrapper && inputWrapper.contains(e.target)) {
            //         return; // Clicked inside input area
            //     }
            //     
            //     if (suggestionsElement && suggestionsElement.contains(e.target)) {
            //         return; // Clicked on suggestions
            //     }
            //     
            //     // Clicked outside, hide suggestions
            //     this.hideSearchSuggestions('click_outside');
            // };
            // 
            // // Remove any existing listener and add new one
            // document.removeEventListener('click', this.clickOutsideHandler);
            // document.addEventListener('click', this.clickOutsideHandler);
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
        console.log('handleDiscovery called'); // Debug log
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const companyName = formData.get('company_name');
        const limit = formData.get('limit') || 5;
        
        console.log('Discovery request:', { companyName, limit }); // Debug log

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
                console.log('🎉 Discovery successful! Results:', data); // Debug log
                console.log('📊 Companies found:', data.results); // Debug log
                
                // Log each company to console for debugging
                data.results.forEach((company, index) => {
                    console.log(`${index + 1}. ${company.company_name} (${(company.similarity_score * 100).toFixed(0)}% match)`);
                });
                
                this.displayResults(data);
                this.showSuccess(`Found ${data.total_found} similar companies for ${data.target_company}`);
            } else {
                console.log('❌ Discovery failed:', data); // Debug log
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

        // Start processing with progress display
        this.startProcessing(companyName.trim(), website.trim());
    }

    async startProcessing(companyName, website) {
        // Show progress container and hide results
        document.getElementById('processResults').style.display = 'none';
        document.getElementById('progressContainer').style.display = 'block';
        
        // Update progress title
        document.getElementById('progressTitle').textContent = `Processing ${companyName}...`;
        
        // Reset all phases to pending
        this.resetProgressPhases();
        
        // Disable form
        const processButton = document.getElementById('processButton');
        processButton.disabled = true;
        processButton.innerHTML = '<span>⏳</span> Processing...';
        
        this.clearMessages();
        
        try {
            const response = await fetch('/api/process-company', {
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

            if (data.success) {
                this.showProcessingResults(data);
                this.showSuccess(`Successfully processed ${companyName}! Generated ${data.sales_intelligence.length} character sales intelligence.`);
            } else {
                this.showProcessingError(data.error || 'Processing failed');
                this.showError(`Failed to process ${companyName}: ${data.error}`);
            }

        } catch (error) {
            console.error('Processing error:', error);
            this.showProcessingError(`Network error: ${error.message}`);
            this.showError(`Failed to process ${companyName}: ${error.message}`);
        } finally {
            // Re-enable form
            processButton.disabled = false;
            processButton.innerHTML = '<span>🧠</span> Generate Sales Intelligence';
            
            // Hide progress spinner
            const spinner = document.querySelector('.progress-spinner');
            if (spinner) {
                spinner.style.display = 'none';
            }
        }
    }

    resetProgressPhases() {
        const phases = [
            { id: 'phase-link-discovery', name: 'Link Discovery' },
            { id: 'phase-page-selection', name: 'LLM Page Selection' },
            { id: 'phase-content-extraction', name: 'Content Extraction' },
            { id: 'phase-intelligence-generation', name: 'Sales Intelligence Generation' }
        ];
        
        phases.forEach(phase => {
            const element = document.getElementById(phase.id);
            if (element) {
                element.className = 'phase-item';
                const statusEl = element.querySelector('.phase-status');
                const detailsEl = element.querySelector('.phase-details');
                const checkEl = element.querySelector('.phase-check');
                
                if (statusEl) statusEl.textContent = 'Pending';
                if (detailsEl) detailsEl.textContent = '';
                if (checkEl) checkEl.textContent = '⏳';
            }
        });
        
        // Clear log
        const logEl = document.getElementById('progressLog');
        if (logEl) {
            logEl.innerHTML = '';
        }
        
        // Show progress spinner
        const spinner = document.querySelector('.progress-spinner');
        if (spinner) {
            spinner.style.display = 'block';
        }
    }

    showProcessingResults(result) {
        // Hide progress and show results
        document.getElementById('progressContainer').style.display = 'none';
        document.getElementById('processResults').style.display = 'block';
        
        // Update summary stats
        const pagesEl = document.getElementById('resultPages');
        const timeEl = document.getElementById('resultTime');
        const lengthEl = document.getElementById('resultLength');
        
        if (pagesEl) pagesEl.textContent = result.pages_processed || 0;
        if (timeEl) timeEl.textContent = `${(result.processing_time || 0).toFixed(1)}s`;
        if (lengthEl) lengthEl.textContent = `${result.sales_intelligence.length} chars`;
        
        // Display sales intelligence
        const intelligenceEl = document.getElementById('salesIntelligence');
        if (intelligenceEl) {
            intelligenceEl.textContent = result.sales_intelligence;
        }
        
        // Mark all phases as completed for visual effect
        ['Link Discovery', 'LLM Page Selection', 'Content Extraction', 'Sales Intelligence Generation'].forEach(phase => {
            this.updatePhaseProgress(phase, 'completed');
        });
        
        // Add final log entry
        this.addToProgressLog('Processing', 'completed', `Generated sales intelligence in ${(result.processing_time || 0).toFixed(1)}s`);
    }

    showProcessingError(error) {
        // Keep progress visible but mark current phase as failed
        const runningPhase = document.querySelector('.phase-item.running');
        if (runningPhase) {
            runningPhase.className = 'phase-item failed';
            const statusEl = runningPhase.querySelector('.phase-status');
            const checkEl = runningPhase.querySelector('.phase-check');
            
            if (statusEl) statusEl.textContent = 'Failed';
            if (checkEl) checkEl.textContent = '❌';
        }
        
        // Add error to log
        this.addToProgressLog('Error', 'failed', error);
    }

    updatePhaseProgress(phaseName, status, details = '') {
        const phaseMap = {
            'Link Discovery': 'phase-link-discovery',
            'LLM Page Selection': 'phase-page-selection', 
            'Content Extraction': 'phase-content-extraction',
            'Sales Intelligence Generation': 'phase-intelligence-generation'
        };
        
        const phaseId = phaseMap[phaseName];
        if (!phaseId) return;
        
        const element = document.getElementById(phaseId);
        if (!element) return;
        
        element.className = `phase-item ${status}`;
        
        const statusEl = element.querySelector('.phase-status');
        const detailsEl = element.querySelector('.phase-details');
        const checkEl = element.querySelector('.phase-check');
        
        if (statusEl) statusEl.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        if (detailsEl) detailsEl.textContent = details;
        
        // Update check icon
        const checkIcon = status === 'completed' ? '✅' : 
                         status === 'failed' ? '❌' : 
                         status === 'running' ? '🔄' : '⏳';
        if (checkEl) checkEl.textContent = checkIcon;
        
        // Add to log
        this.addToProgressLog(phaseName, status, details);
    }
    
    addToProgressLog(phaseName, status, details) {
        const logContainer = document.getElementById('progressLog');
        if (!logContainer) return;
        
        const timestamp = new Date().toLocaleTimeString();
        
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `
            <span class="log-timestamp">[${timestamp}]</span>
            <strong>${phaseName}</strong>: ${status} ${details ? `- ${details}` : ''}
        `;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    async handleRealTimeSearch(query, controller = null) {
        console.log(`[${new Date().toLocaleTimeString()}] handleRealTimeSearch called with:`, query); // Debug log
        
        // Store current query to prevent showing stale results
        this.currentSearchQuery = query.trim().toLowerCase();
        
        if (!query.trim() || query.length < 2) {
            console.log('Query too short, hiding suggestions'); // Debug log
            this.hideSearchSuggestions('query_too_short');
            return;
        }

        try {
            const fetchOptions = {
                method: 'GET'
            };
            
            if (controller) {
                fetchOptions.signal = controller.signal;
            }
            
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`, fetchOptions);
            const data = await response.json();

            // Only show results if the query hasn't changed while we were waiting
            const currentInput = document.getElementById('companyName').value.trim().toLowerCase();
            if (currentInput !== this.currentSearchQuery) {
                return; // Query changed, ignore these results
            }

            if (response.ok && data.results.length > 0) {
                console.log('Search API returned:', data.results); // Debug log
                console.log('Current query:', this.currentSearchQuery); // Debug log
                
                // Filter results to only show matches that contain the search query
                const filteredResults = data.results.filter(result => 
                    result.name.toLowerCase().includes(this.currentSearchQuery)
                );
                
                console.log('Filtered results:', filteredResults); // Debug log
                
                if (filteredResults.length > 0) {
                    this.showSearchSuggestions(filteredResults);
                } else {
                    this.hideSearchSuggestions('no_filtered_results');
                }
            } else {
                this.hideSearchSuggestions('no_api_results');
            }

        } catch (error) {
            if (error.name === 'AbortError') {
                // Request was cancelled, this is expected
                return;
            }
            console.error('Search error:', error);
            this.hideSearchSuggestions('search_error');
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

        // If switching to database tab, load the database
        if (tabId === 'databaseTab') {
            this.loadDatabaseBrowser();
        }
    }

    displayResults(data) {
        console.log('📋 displayResults called with:', data); // Debug log
        
        const resultsContainer = document.getElementById('results');
        const resultsSection = document.getElementById('resultsSection');
        const resultsCountElement = document.getElementById('resultsCount');

        console.log('📍 Results container found:', !!resultsContainer); // Debug log
        console.log('📍 Results section found:', !!resultsSection); // Debug log
        console.log('📍 Results count element found:', !!resultsCountElement); // Debug log

        if (!resultsContainer || !resultsSection) {
            console.log('❌ Missing results container or section!'); // Debug log
            return;
        }

        // Update the results count
        const resultCount = data.results.length;
        if (resultsCountElement) {
            resultsCountElement.textContent = `${resultCount} found`;
            console.log('🔢 Updated results count to:', resultCount); // Debug log
        }

        if (data.results.length === 0) {
            console.log('📭 No results, showing empty state'); // Debug log
            resultsContainer.innerHTML = this.createEmptyState();
        } else {
            console.log('🏗️ Creating HTML for', data.results.length, 'results'); // Debug log
            const resultCards = data.results.map(result => {
                const cardHTML = this.createResultCard(result);
                console.log('📄 Generated card HTML length:', cardHTML.length); // Debug log
                return cardHTML;
            });
            
            const finalHTML = resultCards.join('');
            console.log('🎯 Final HTML to insert (length:', finalHTML.length, '):', finalHTML.substring(0, 200) + '...'); // Debug log
            
            resultsContainer.innerHTML = finalHTML;
            
            // Check if HTML was actually set
            setTimeout(() => {
                console.log('✅ Results container after insert:', resultsContainer.innerHTML.length, 'characters'); // Debug log
                console.log('🔍 Child elements count:', resultsContainer.children.length); // Debug log
            }, 100);
        }

        console.log('👁️ Showing results section'); // Debug log
        resultsSection.classList.remove('hidden');
        
        // Ensure results section is properly visible
        resultsSection.style.display = 'block';
        
        // Animate result cards
        setTimeout(() => {
            const cards = resultsContainer.querySelectorAll('.result-card');
            console.log('🎯 Animating', cards.length, 'result cards'); // Debug log
            cards.forEach((card, index) => {
                setTimeout(() => {
                    card.classList.add('fade-in-up');
                }, index * 100);
            });
        }, 100);
    }

    createResultCard(result) {
        console.log('🃏 Creating result card for:', result); // Debug log
        
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
        console.log('showSearchSuggestions called with:', results); // Debug log
        
        // Record when suggestions were shown to prevent immediate hiding
        this.suggestionsShownAt = Date.now();
        
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

        const suggestionHTML = results.map(result => `
            <div class="suggestion-item" data-name="${this.escapeHtml(result.name)}">
                <div class="suggestion-name">${this.escapeHtml(result.name)}</div>
                <div class="suggestion-details">
                    ${result.industry ? `${result.industry} • ` : ''}
                    ${result.business_model || 'Unknown'}
                </div>
            </div>
        `).join('');
        
        console.log('Setting suggestion HTML:', suggestionHTML); // Debug log
        suggestions.innerHTML = suggestionHTML;

        // Add click handlers with proper safeguards
        suggestions.onclick = null; // Clear any existing handlers
        
        // Use mousedown instead of click to avoid conflicts, and add delay
        setTimeout(() => {
            suggestions.addEventListener('mousedown', (e) => {
                console.log('Mousedown on suggestions:', e.target, 'isTrusted:', e.isTrusted); // Debug log
                const suggestionItem = e.target.closest('.suggestion-item');
                if (suggestionItem && e.isTrusted) { // Only handle real user interactions
                    console.log('Real suggestion selected:', suggestionItem.dataset.name); // Debug log
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Fill in the input field
                    input.value = suggestionItem.dataset.name;
                    
                    // Hide suggestions after a small delay to ensure the value is set
                    setTimeout(() => {
                        this.hideSearchSuggestions('suggestion_selected');
                    }, 50);
                }
            });
        }, 200); // Wait 200ms before attaching handlers to avoid phantom events

        suggestions.classList.add('show');
    }

    hideSearchSuggestions(reason = 'unknown') {
        // Prevent hiding if suggestions were just shown (within 200ms)
        if (this.suggestionsShownAt && (Date.now() - this.suggestionsShownAt) < 200) {
            console.log('Ignoring hide request - suggestions just shown, reason:', reason);
            return;
        }
        
        console.log('hideSearchSuggestions called, reason:', reason); // Debug log
        console.trace(); // Show stack trace to see what called this
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

    // Database Browser Methods
    initializeDatabaseBrowser() {
        // No initialization needed, will load when tab is clicked
    }

    async loadDatabaseBrowser() {
        console.log('Loading database browser...');
        
        const tableContainer = document.getElementById('companiesTable');
        const totalElement = document.getElementById('totalCompanies');
        
        // Show loading state
        tableContainer.innerHTML = '<div class="loading">Loading companies...</div>';
        if (totalElement) {
            totalElement.textContent = 'Loading...';
        }
        
        try {
            // Try the new companies endpoint first
            let response = await fetch('/api/companies');
            let data = await response.json();

            if (response.ok && data.success) {
                console.log('Using new companies API:', data);
                this.updateDatabaseStats({ total_companies: data.total });
                this.updateCompaniesTable(data.companies);
            } else {
                // Fallback to old database endpoint
                console.log('Trying fallback database endpoint...');
                response = await fetch('/api/database');
                data = await response.json();
                
                if (response.ok) {
                    console.log('Using fallback database API:', data);
                    this.updateDatabaseStats(data);
                    this.updateCompaniesTable(data.companies || []);
                } else {
                    this.showDatabaseError(data.error || 'Failed to load database');
                }
            }
        } catch (error) {
            console.error('Database browser error:', error);
            this.showDatabaseError('Network error loading database');
        }
    }

    updateDatabaseStats(data) {
        const totalElement = document.getElementById('totalCompanies');
        if (totalElement) {
            totalElement.textContent = data.total_companies || 0;
        }
    }

    updateCompaniesTable(companies) {
        const tableContainer = document.getElementById('companiesTable');
        
        if (!companies || companies.length === 0) {
            tableContainer.innerHTML = `
                <div class="loading">
                    <p>📑 No companies in database</p>
                    <p style="margin-top: 12px; font-size: 0.9rem; color: var(--text-muted);">
                        Use "Add Sample Companies" to populate the database with test data.
                    </p>
                </div>
            `;
            return;
        }

        const tableHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Company</th>
                        <th>Website</th>
                        <th>Industry</th>
                        <th>Business Model</th>
                        <th>Sales Intelligence</th>
                        <th>Last Updated</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${companies.map(company => `
                        <tr>
                            <td>
                                <div class="company-name">${this.escapeHtml(company.name || 'Unknown')}</div>
                                <div class="company-id">${this.escapeHtml((company.id || '').substring(0, 8))}...</div>
                            </td>
                            <td>
                                <div class="company-website">
                                    ${company.website ? `<a href="${company.website}" target="_blank">${this.escapeHtml(company.website.replace('https://', '').replace('http://', ''))}</a>` : 'N/A'}
                                </div>
                            </td>
                            <td>${this.escapeHtml(company.industry || 'Unknown')}</td>
                            <td>${this.escapeHtml(company.business_model || 'Unknown')}</td>
                            <td>
                                <div class="sales-intelligence-preview">
                                    ${company.has_sales_intelligence ? 
                                        `<span class="intelligence-indicator">✅ Available</span>
                                         <button class="btn-mini" onclick="viewSalesIntelligence('${company.id}')">View</button>` : 
                                        '<span class="intelligence-indicator">❌ Not Available</span>'
                                    }
                                </div>
                            </td>
                            <td>
                                <div class="update-time">${company.last_updated ? new Date(company.last_updated).toLocaleDateString() : 'Unknown'}</div>
                            </td>
                            <td>
                                <button class="btn-mini btn-primary" onclick="testSimilarity('${this.escapeHtml(company.name)}')">
                                    🔍 Test Similarity
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        tableContainer.innerHTML = tableHTML;
    }

    showDatabaseError(message) {
        const tableContainer = document.getElementById('companiesTable');
        tableContainer.innerHTML = `
            <div class="loading">
                <p style="color: #ff6b6b;">❌ Error: ${this.escapeHtml(message)}</p>
            </div>
        `;
    }

    async refreshDatabase() {
        console.log('Refreshing database...');
        await this.loadDatabaseBrowser();
        this.showSuccess('Database refreshed');
    }

    async addSampleCompanies() {
        console.log('Adding sample companies...');
        
        const addButton = document.querySelector('button[onclick="addSampleCompanies()"]');
        if (addButton) {
            this.setButtonLoading(addButton, true);
        }
        
        try {
            const response = await fetch('/api/database/add-sample', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess('Sample companies added successfully');
                
                // Show results if available
                if (data.results) {
                    console.log('Sample company results:', data.results);
                    data.results.forEach(result => {
                        console.log(' -', result);
                    });
                }
                
                // Refresh the database view
                setTimeout(() => {
                    this.loadDatabaseBrowser();
                }, 1000);
            } else {
                this.showError(data.error || 'Failed to add sample companies');
            }
        } catch (error) {
            console.error('Add sample companies error:', error);
            this.showError('Network error adding sample companies');
        } finally {
            if (addButton) {
                this.setButtonLoading(addButton, false);
            }
        }
    }

    async clearDatabase() {
        // Confirm before clearing
        if (!confirm('Are you sure you want to clear all companies from the database? This action cannot be undone.')) {
            return;
        }
        
        console.log('Clearing database...');
        
        const clearButton = document.querySelector('button[onclick="clearDatabase()"]');
        if (clearButton) {
            this.setButtonLoading(clearButton, true);
        }
        
        try {
            const response = await fetch('/api/database/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess('Database cleared successfully');
                
                // Refresh the database view
                setTimeout(() => {
                    this.loadDatabaseBrowser();
                }, 500);
            } else {
                this.showError(data.error || 'Failed to clear database');
            }
        } catch (error) {
            console.error('Clear database error:', error);
            this.showError('Network error clearing database');
        } finally {
            if (clearButton) {
                this.setButtonLoading(clearButton, false);
            }
        }
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

// Global functions
function runDemo() {
    const ui = window.theodoreUI || new TheodoreUI();
    ui.runDemo();
}

function refreshDatabase() {
    const ui = window.theodoreUI || new TheodoreUI();
    ui.refreshDatabase();
}

function addSampleCompanies() {
    const ui = window.theodoreUI || new TheodoreUI();
    ui.addSampleCompanies();
}

function clearDatabase() {
    const ui = window.theodoreUI || new TheodoreUI();
    ui.clearDatabase();
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

// Global utility functions for the HTML
function resetProcessForm() {
    document.getElementById('processForm').reset();
    document.getElementById('progressContainer').style.display = 'none';
    document.getElementById('processResults').style.display = 'none';
}

function switchToDiscoveryTab() {
    // Switch to discovery tab
    document.querySelector('.tab-button[data-tab="discoveryTab"]').click();
    
    // Fill in the last processed company name if available
    const processedCompany = document.getElementById('progressTitle').textContent.replace('Processing ', '').replace('...', '');
    if (processedCompany && processedCompany !== 'Processing Company') {
        document.getElementById('companyName').value = processedCompany;
    }
}

// Additional utility functions for database browser
async function viewSalesIntelligence(companyId) {
    try {
        const response = await fetch(`/api/company/${companyId}`);
        const data = await response.json();
        
        if (data.success && data.company.sales_intelligence) {
            // Create modal to display sales intelligence
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>${data.company.name} - Sales Intelligence</h3>
                        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="intelligence-content">
                            ${data.company.sales_intelligence.replace(/\n/g, '<br>')}
                        </div>
                        <div class="modal-stats" style="margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border-subtle);">
                            <div class="stat-row">
                                <strong>Pages Processed:</strong> ${data.company.pages_crawled ? data.company.pages_crawled.length : 0}
                            </div>
                            <div class="stat-row">
                                <strong>Processing Time:</strong> ${data.company.processing_time ? data.company.processing_time.toFixed(1) + 's' : 'Unknown'}
                            </div>
                            <div class="stat-row">
                                <strong>Last Updated:</strong> ${data.company.last_updated ? new Date(data.company.last_updated).toLocaleString() : 'Unknown'}
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        } else {
            alert('Sales intelligence not available for this company.');
        }
    } catch (error) {
        console.error('Error fetching sales intelligence:', error);
        alert('Failed to load sales intelligence.');
    }
}

function testSimilarity(companyName) {
    // Switch to discovery tab and fill in company name
    document.querySelector('.tab-button[data-tab="discoveryTab"]').click();
    document.getElementById('companyName').value = companyName;
    
    // Show a brief message
    if (window.theodoreUI) {
        window.theodoreUI.showMessage(`Testing similarity for "${companyName}" - enter your search in the Discovery tab`, 'info');
    }
}