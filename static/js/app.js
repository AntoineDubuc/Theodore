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
            console.log('✅ Search form found, attaching event listener'); // Debug log
            searchForm.addEventListener('submit', this.handleDiscovery.bind(this));
            console.log('✅ Event listener attached to search form'); // Debug log
        } else {
            console.log('❌ Search form NOT found!'); // Debug log
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
        console.log('🚀 handleDiscovery called'); // Debug log
        console.log('📝 Event object:', event); // Debug log
        event.preventDefault();
        console.log('🛑 Default prevented'); // Debug log
        
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
        
        // Show discovery progress
        this.showDiscoveryProgress(companyName);

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
                
                // Handle both success and error response structures
                const results = data.results || data.companies || [];
                console.log('📊 Companies found:', results); // Debug log
                
                if (results.length > 0) {
                    // Log each company to console for debugging
                    results.forEach((company, index) => {
                        console.log(`${index + 1}. ${company.company_name} (${(company.similarity_score * 100).toFixed(0)}% match)`);
                    });
                    
                    // Ensure data has the results in the expected format
                    const normalizedData = {
                        ...data,
                        results: results,
                        total_found: data.total_found || results.length,
                        target_company: data.target_company || data.company_name || 'Unknown'
                    };
                    
                    this.hideDiscoveryProgress();
                    this.displayResults(normalizedData);
                    this.showSuccess(`Found ${normalizedData.total_found} similar companies for ${normalizedData.target_company}`);
                } else {
                    // Handle no results case
                    console.log('📭 No results found'); // Debug log
                    this.hideDiscoveryProgress();
                    this.displayResults({ results: [], total_found: 0, target_company: data.target_company || 'Unknown' });
                    
                    if (data.error) {
                        this.showError(data.error);
                        if (data.suggestion) {
                            this.showInfo(data.suggestion);
                        }
                    } else {
                        this.showError('No similar companies found');
                    }
                }
            } else {
                console.log('❌ Discovery failed:', data); // Debug log
                this.hideDiscoveryProgress();
                this.showError(data.error || 'Discovery failed');
                if (data.suggestion) {
                    this.showInfo(data.suggestion);
                }
            }

        } catch (error) {
            this.hideDiscoveryProgress();
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
        
        const researchStatusBadge = this.getResearchStatusBadge(result.research_status);
        const researchControls = this.getResearchControls(result);
        const progressId = `progress-${result.company_name.replace(/\s+/g, '-')}`;

        return `
            <div class="result-card" data-score="${scoreClass}" data-company-name="${this.escapeHtml(result.company_name)}" data-website="${this.escapeHtml(result.website || '')}">
                <div class="result-header">
                    <div>
                        <div class="result-company-wrapper">
                            <div class="result-company">${this.escapeHtml(result.company_name)}</div>
                            ${researchStatusBadge}
                        </div>
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
                ${result.business_context ? `
                    <div class="business-context">
                        <strong>Business Context:</strong> ${this.escapeHtml(result.business_context)}
                    </div>
                ` : ''}
                <div class="result-meta">
                    <small class="text-muted">
                        Confidence: ${(result.confidence * 100).toFixed(0)}% • 
                        Method: ${this.escapeHtml(result.discovery_method)}
                        ${result.in_database ? ' • In Database' : ' • Not in Database'}
                    </small>
                </div>
                <div class="research-controls">
                    ${researchControls}
                </div>
                <div class="research-progress" id="${progressId}" style="display: none;">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 0%"></div>
                    </div>
                    <div class="progress-text">Initializing...</div>
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

    getResearchStatusBadge(status) {
        const statusConfig = {
            'unknown': { label: 'Unknown', icon: '❓', class: 'status-unknown' },
            'not_researched': { label: 'Basic Data', icon: '📝', class: 'status-basic' },
            'researching': { label: 'Researching', icon: '🔄', class: 'status-researching' },
            'completed': { label: 'Researched', icon: '✅', class: 'status-completed' },
            'failed': { label: 'Failed', icon: '❌', class: 'status-failed' },
            'queued': { label: 'Queued', icon: '⏳', class: 'status-queued' }
        };

        const config = statusConfig[status] || statusConfig['unknown'];
        return `<span class="research-status-badge ${config.class}">${config.icon} ${config.label}</span>`;
    }

    getResearchControls(result) {
        const companyId = result.company_name.replace(/\s+/g, '-');
        
        // Escape values for safe HTML attributes
        const escapedName = this.escapeHtml(result.company_name);
        const escapedWebsite = this.escapeHtml(result.website || '');
        
        // Add Open Website button for all statuses (if website available)
        const websiteButton = escapedWebsite ? `
            <button class="btn-mini btn-website" onclick="window.open('${escapedWebsite}', '_blank')" title="Open ${escapedName} website">
                🌐 Website
            </button>
        ` : '';

        if (result.research_status === 'completed') {
            // Check if this is a researched company (not in database) or database company
            if (result.is_researched) {
                // Researched company - show research-specific controls
                return `
                    <button class="btn-mini btn-secondary" onclick="window.theodoreUI.viewResearchDetails('${escapedName}')">
                        👁️ View Research
                    </button>
                    <button class="btn-mini btn-accent" onclick="window.theodoreUI.saveToDatabase('${escapedName}', '${escapedWebsite}')">
                        💾 Save to Database
                    </button>
                    <button class="btn-mini btn-primary" onclick="window.theodoreUI.reResearchCompany('${escapedName}', '${escapedWebsite}')">
                        🔄 Re-research
                    </button>
                    ${websiteButton}
                `;
            } else {
                // Database company - show database-specific controls
                return `
                    <button class="btn-mini btn-secondary" onclick="window.theodoreUI.viewCompanyDetails('${result.database_id}', '${escapedName}')">
                        👁️ View Details
                    </button>
                    <button class="btn-mini btn-primary" onclick="window.theodoreUI.reResearchCompany('${escapedName}', '${escapedWebsite}')">
                        🔄 Re-research
                    </button>
                    ${websiteButton}
                `;
            }
        } else if (result.research_status === 'researching' || result.research_status === 'queued') {
            return `
                <button class="btn-mini btn-secondary" disabled>
                    ⏳ Researching...
                </button>
                ${websiteButton}
            `;
        } else {
            return `
                <button class="btn-mini btn-primary" onclick="window.theodoreUI.startResearch('${escapedName}', '${escapedWebsite}')">
                    🔬 Research Now
                </button>
                ${result.research_status === 'unknown' ? `
                    <button class="btn-mini btn-secondary" onclick="window.theodoreUI.previewResearch('${escapedName}', '${escapedWebsite}')">
                        👁️ Preview
                    </button>
                ` : ''}
                ${websiteButton}
            `;
        }
    }

    async startResearch(companyName, website) {
        console.log(`🔬 Starting research for: ${companyName}`);
        console.log(`🌐 Website: ${website}`);
        console.log(`📝 Research payload being sent:`, {
            company: {
                name: companyName,
                website: website
            }
        });
        
        // Update button to show loading state
        this.updateResearchButton(companyName, 'researching');
        
        try {
            const response = await fetch('/api/research', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    company: {
                        name: companyName,
                        website: website
                    }
                })
            });

            const data = await response.json();
            console.log(`📊 Research API response:`, data);

            if (response.ok && data.success) {
                console.log(`✅ Research successful for ${companyName}`);
                console.log(`📋 Company data received:`, data.company);
                this.showSuccess(`Research completed for ${companyName}`);
                
                // Update the result card with enhanced data
                this.updateResultCardWithResearch(companyName, data.company);
                
            } else {
                this.showError(data.error || 'Failed to complete research');
                // Reset button on error
                this.updateResearchButton(companyName, 'unknown');
            }
        } catch (error) {
            console.error('Research error:', error);
            this.showError('Network error during research');
            // Reset button on error  
            this.updateResearchButton(companyName, 'unknown');
        }
    }

    updateResultCardWithResearch(companyName, researchedCompany) {
        console.log(`🎯 Updating result card for: ${companyName}`);
        console.log(`📋 Full researched company data:`, researchedCompany);
        
        // Find the result card for this company
        const resultCard = document.querySelector(`[data-company-name="${this.escapeHtml(companyName)}"]`);
        if (!resultCard) {
            console.warn(`❌ Result card not found for ${companyName}`);
            return;
        }
        
        console.log(`✅ Found result card for ${companyName}`);

        // Update the card with enhanced research data
        if (researchedCompany.is_researched && researchedCompany.research_status === 'success') {
            console.log(`📊 Research successful, extracting data fields:`);
            console.log(`📋 Industry: "${researchedCompany.industry}"`);
            console.log(`📋 Business Model: "${researchedCompany.business_model}"`);
            console.log(`📋 Description: "${researchedCompany.company_description}"`);
            console.log(`📋 Target Market: "${researchedCompany.target_market}"`);
            console.log(`📋 Key Services:`, researchedCompany.key_services);
            console.log(`📋 Location: "${researchedCompany.location}"`);
            console.log(`📋 Pages Crawled:`, researchedCompany.pages_crawled);
            console.log(`📋 Pages Crawled Type:`, typeof researchedCompany.pages_crawled);
            console.log(`📋 Pages Crawled Length:`, researchedCompany.pages_crawled ? researchedCompany.pages_crawled.length : 'undefined');
            console.log(`📋 Processing Time:`, researchedCompany.processing_time);
            console.log(`📋 Processing Time Type:`, typeof researchedCompany.processing_time);
            console.log(`📋 Research Timestamp:`, researchedCompany.research_timestamp);
            
            // Add research data sections
            const businessContextDiv = resultCard.querySelector('.business-context');
            const resultMetaDiv = resultCard.querySelector('.result-meta');

            // Add or update business context with research data
            const researchHTML = `
                <div class="research-data">
                    <div class="research-section">
                        <strong>Industry:</strong> ${this.escapeHtml(researchedCompany.industry || 'Unknown')}
                    </div>
                    <div class="research-section">
                        <strong>Business Model:</strong> ${this.escapeHtml(researchedCompany.business_model || 'Unknown')}
                    </div>
                    ${researchedCompany.company_description ? `
                        <div class="research-section">
                            <strong>Description:</strong> ${this.escapeHtml(researchedCompany.company_description.substring(0, 200))}${researchedCompany.company_description.length > 200 ? '...' : ''}
                        </div>
                    ` : ''}
                    ${researchedCompany.target_market && researchedCompany.target_market !== 'Unknown' ? `
                        <div class="research-section">
                            <strong>Target Market:</strong> ${this.escapeHtml(researchedCompany.target_market)}
                        </div>
                    ` : ''}
                    ${researchedCompany.key_services && researchedCompany.key_services.length > 0 ? `
                        <div class="research-section">
                            <strong>Key Services:</strong> ${researchedCompany.key_services.map(s => this.escapeHtml(s)).join(', ')}
                        </div>
                    ` : ''}
                    ${researchedCompany.location && researchedCompany.location !== 'Unknown' ? `
                        <div class="research-section">
                            <strong>Location:</strong> ${this.escapeHtml(researchedCompany.location)}
                        </div>
                    ` : ''}
                    <div class="research-section research-meta-info">
                        <strong>Research Info:</strong> 
                        ${researchedCompany.pages_crawled && researchedCompany.pages_crawled.length > 0 ? `${researchedCompany.pages_crawled.length} pages crawled` : 'Pages data unavailable'}
                        ${researchedCompany.processing_time && researchedCompany.processing_time > 0 ? ` • ${researchedCompany.processing_time.toFixed(1)}s processing time` : ''}
                        ${researchedCompany.research_timestamp ? ` • ${new Date(researchedCompany.research_timestamp).toLocaleString()}` : ''}
                    </div>
                </div>
            `;
            
            console.log(`🏗️ Generated research HTML:`, researchHTML);

            // Insert research data after business context or before meta
            if (businessContextDiv) {
                console.log(`📍 Inserting research data after business context`);
                businessContextDiv.insertAdjacentHTML('afterend', researchHTML);
            } else if (resultMetaDiv) {
                console.log(`📍 Inserting research data before meta div`);
                resultMetaDiv.insertAdjacentHTML('beforebegin', researchHTML);
            }

            // Update research status badge
            const statusBadge = resultCard.querySelector('.research-status-badge');
            if (statusBadge) {
                statusBadge.innerHTML = '✅ Researched';
                statusBadge.className = 'research-status-badge status-completed';
            }

            // Update research controls
            const controlsDiv = resultCard.querySelector('.research-controls');
            if (controlsDiv) {
                const newControls = this.getResearchControls({
                    ...researchedCompany,
                    research_status: 'completed'
                });
                controlsDiv.innerHTML = newControls;
            }

            // Update meta information to show research method
            if (resultMetaDiv) {
                const metaText = resultMetaDiv.querySelector('small');
                if (metaText) {
                    metaText.innerHTML = metaText.innerHTML.replace(
                        /Method: [^•]+/, 
                        `Method: ${this.escapeHtml(researchedCompany.discovery_method || 'LLM + On-Demand Research')}`
                    );
                }
            }

            // Add animation to highlight the update
            resultCard.classList.add('research-updated');
            setTimeout(() => {
                resultCard.classList.remove('research-updated');
            }, 2000);

        } else {
            // Research failed, update status
            this.updateResearchButton(companyName, 'failed');
        }
    }

    async startBulkResearch(companies) {
        console.log(`🔬 Starting bulk research for ${companies.length} companies`);
        
        try {
            const response = await fetch('/api/research/bulk', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    companies: companies
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showSuccess(`Bulk research started for ${data.total_started} companies`);
                
                // Show progress for each company
                data.job_ids.forEach((jobId, index) => {
                    this.showResearchProgress(companies[index].name, jobId);
                });
                
            } else {
                this.showError(data.error || 'Failed to start bulk research');
            }
        } catch (error) {
            console.error('Bulk research start error:', error);
            this.showError('Network error starting bulk research');
        }
    }

    showResearchProgress(companyName, jobId) {
        const progressId = `progress-${companyName.replace(/\s+/g, '-')}`;
        const progressContainer = document.getElementById(progressId);
        
        if (progressContainer) {
            progressContainer.style.display = 'block';
            
            // Start polling for progress
            this.pollResearchProgress(jobId, progressContainer);
        }
    }

    async pollResearchProgress(jobId, progressContainer) {
        try {
            const response = await fetch(`/api/research/progress/${jobId}`);
            const data = await response.json();

            if (response.ok && data.progress) {
                const progress = data.progress;
                
                // Update progress bar
                const progressFill = progressContainer.querySelector('.progress-fill');
                const progressText = progressContainer.querySelector('.progress-text');
                
                if (progressFill) {
                    progressFill.style.width = `${progress.progress_percent}%`;
                }
                
                if (progressText) {
                    progressText.textContent = progress.current_phase || 'Processing...';
                }

                // Continue polling if not complete
                if (progress.status === 'researching' || progress.status === 'queued') {
                    setTimeout(() => {
                        this.pollResearchProgress(jobId, progressContainer);
                    }, 2000); // Poll every 2 seconds
                } else {
                    // Research complete
                    if (progress.status === 'completed') {
                        this.showSuccess(`Research completed for ${progress.company_name}`);
                        progressText.textContent = 'Research completed!';
                        
                        // Hide progress after delay
                        setTimeout(() => {
                            progressContainer.style.display = 'none';
                        }, 3000);
                        
                        // Update research status
                        this.updateResearchButton(progress.company_name, 'completed');
                        
                    } else if (progress.status === 'failed') {
                        this.showError(`Research failed for ${progress.company_name}: ${progress.error_message || 'Unknown error'}`);
                        progressText.textContent = 'Research failed';
                        
                        // Update research status
                        this.updateResearchButton(progress.company_name, 'failed');
                    }
                }
            }
        } catch (error) {
            console.error('Progress polling error:', error);
        }
    }

    updateResearchButton(companyName, status) {
        // Find the result card for this company
        const resultCard = document.querySelector(`[data-company-name="${companyName}"]`);
        if (resultCard) {
            const controls = resultCard.querySelector('.research-controls');
            const statusBadge = resultCard.querySelector('.research-status-badge');
            
            // Update status badge
            if (statusBadge) {
                const newBadge = this.getResearchStatusBadge(status);
                statusBadge.outerHTML = newBadge;
            }
            
            // Update controls based on new status
            if (controls) {
                const website = resultCard.dataset.website || '';
                const newControls = this.getResearchControls({
                    company_name: companyName,
                    website: website,
                    research_status: status
                });
                controls.innerHTML = newControls;
            }
        }
    }

    async viewCompanyDetails(companyId, companyName = null) {
        try {
            // If companyId is null/undefined, try to find by name
            if (!companyId || companyId === 'null' || companyId === 'undefined') {
                if (companyName) {
                    // Search for company by name in database
                    console.log(`Searching for company by name: ${companyName}`);
                    return await this.viewCompanyDetailsByName(companyName);
                } else {
                    this.showError('Cannot load company details - no ID or name provided');
                    return;
                }
            }
            
            const response = await fetch(`/api/company/${companyId}`);
            const data = await response.json();
            
            if (response.ok && data.company) {
                this.showCompanyDetailsModal(data.company);
            } else {
                this.showError('Failed to load company details');
            }
        } catch (error) {
            console.error('View company details error:', error);
            this.showError('Network error loading company details');
        }
    }
    
    async viewCompanyDetailsByName(companyName) {
        try {
            // Get all companies and find by name
            const response = await fetch('/api/companies');
            const data = await response.json();
            
            if (response.ok && data.companies) {
                const company = data.companies.find(c => 
                    c.name.toLowerCase() === companyName.toLowerCase()
                );
                
                if (company) {
                    // Now fetch full details using the found ID
                    await this.viewCompanyDetails(company.id);
                } else {
                    this.showError(`Company "${companyName}" not found in database. Research may still be in progress.`);
                }
            } else {
                this.showError('Failed to search for company');
            }
        } catch (error) {
            console.error('View company by name error:', error);
            this.showError('Network error searching for company');
        }
    }

    showCompanyDetailsModal(company) {
        const modalContent = `
            <div class="company-details">
                <h3>${this.escapeHtml(company.name)}</h3>
                <div class="detail-section">
                    <h4>Basic Information</h4>
                    <p><strong>Website:</strong> <a href="${company.website}" target="_blank">${this.escapeHtml(company.website)}</a></p>
                    <p><strong>Industry:</strong> ${this.escapeHtml(company.industry || 'Unknown')}</p>
                    <p><strong>Business Model:</strong> ${this.escapeHtml(company.business_model || 'Unknown')}</p>
                </div>
                ${company.sales_intelligence ? `
                    <div class="detail-section">
                        <h4>Sales Intelligence</h4>
                        <div class="sales-intelligence-content">
                            ${this.escapeHtml(company.sales_intelligence).replace(/\n/g, '<br>')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        const modal = this.createModal('Company Details', modalContent);
        document.body.appendChild(modal);
    }

    async previewResearch(companyName, website) {
        const previewContent = `
            <div class="research-preview">
                <h4>Research Preview for ${this.escapeHtml(companyName)}</h4>
                <p><strong>Website:</strong> <a href="${website}" target="_blank">${this.escapeHtml(website)}</a></p>
                
                <div class="preview-phases">
                    <h5>Research Process (4 Phases):</h5>
                    <ul>
                        <li>🔍 <strong>Link Discovery:</strong> Find all company pages (robots.txt, sitemaps, recursive crawling)</li>
                        <li>🤖 <strong>AI Page Selection:</strong> LLM selects most promising pages for sales intelligence</li>
                        <li>⚡ <strong>Parallel Extraction:</strong> Extract content from 5-10 selected pages simultaneously</li>
                        <li>📝 <strong>Sales Intelligence:</strong> Generate 2-3 focused paragraphs for sales teams</li>
                    </ul>
                </div>
                
                <div class="preview-outcome">
                    <h5>Expected Outcome:</h5>
                    <p>Comprehensive sales intelligence including business model, target market, key services, technology stack, and competitive positioning.</p>
                </div>
                
                <div class="preview-actions">
                    <button class="btn btn-primary" onclick="window.theodoreUI.startResearch('${this.escapeHtml(companyName)}', '${this.escapeHtml(website)}'); this.closest('.modal-overlay').remove();">
                        🔬 Start Research Now
                    </button>
                </div>
            </div>
        `;
        
        const modal = this.createModal('Research Preview', previewContent);
        document.body.appendChild(modal);
    }

    async reResearchCompany(companyName, website) {
        if (confirm(`Re-research ${companyName}? This will update the existing data.`)) {
            await this.startResearch(companyName, website);
        }
    }
    
    viewResearchDetails(companyName) {
        console.log(`👁️ Viewing research details for: ${companyName}`);
        
        // Find the result card to get research data
        const resultCard = document.querySelector(`[data-company-name="${this.escapeHtml(companyName)}"]`);
        console.log(`🎯 Found result card:`, resultCard);
        
        if (!resultCard) {
            console.error(`❌ Cannot find result card for ${companyName}`);
            this.showError(`Cannot find research data for ${companyName}`);
            return;
        }
        
        // Extract research data from the card (look for .research-data sections)
        const researchData = resultCard.querySelector('.research-data');
        console.log(`📊 Found research data element:`, researchData);
        console.log(`📝 Research data innerHTML:`, researchData ? researchData.innerHTML : 'null');
        
        if (!researchData) {
            console.error(`❌ No research data element found for ${companyName}`);
            this.showError(`No research data available for ${companyName}`);
            return;
        }
        
        // Build modal content from the research data
        console.log(`🔍 Extracting research fields...`);
        const industry = this.extractResearchField(researchData, 'Industry') || 'Unknown';
        console.log(`📋 Extracted Industry: "${industry}"`);
        const businessModel = this.extractResearchField(researchData, 'Business Model') || 'Unknown';
        console.log(`📋 Extracted Business Model: "${businessModel}"`);
        const description = this.extractResearchField(researchData, 'Description') || 'No description available';
        console.log(`📋 Extracted Description: "${description}"`);
        const targetMarket = this.extractResearchField(researchData, 'Target Market') || 'Unknown';
        console.log(`📋 Extracted Target Market: "${targetMarket}"`);
        const keyServices = this.extractResearchField(researchData, 'Key Services') || 'None listed';
        console.log(`📋 Extracted Key Services: "${keyServices}"`);
        const location = this.extractResearchField(researchData, 'Location') || 'Unknown';
        console.log(`📋 Extracted Location: "${location}"`);
        const researchInfo = this.extractResearchField(researchData, 'Research Info') || 'Research metadata unavailable';
        console.log(`📋 Extracted Research Info: "${researchInfo}"`);
        
        const modalContent = `
            <div class="research-details">
                <h3>${this.escapeHtml(companyName)} - Research Details</h3>
                
                <div class="detail-section">
                    <h4>Basic Information</h4>
                    <div class="detail-item">
                        <strong>Industry:</strong> ${this.escapeHtml(industry)}
                    </div>
                    <div class="detail-item">
                        <strong>Business Model:</strong> ${this.escapeHtml(businessModel)}
                    </div>
                    <div class="detail-item">
                        <strong>Location:</strong> ${this.escapeHtml(location)}
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>Business Details</h4>
                    <div class="detail-item">
                        <strong>Target Market:</strong> ${this.escapeHtml(targetMarket)}
                    </div>
                    <div class="detail-item">
                        <strong>Key Services:</strong> ${this.escapeHtml(keyServices)}
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>Company Description</h4>
                    <div class="detail-item description-text">
                        ${this.escapeHtml(description)}
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>Research Metadata</h4>
                    <div class="detail-item">
                        <strong>Research Details:</strong> ${this.escapeHtml(researchInfo)}
                    </div>
                </div>
                
                <div class="research-meta">
                    <small class="text-muted">
                        Research completed via on-demand web scraping and AI analysis
                    </small>
                </div>
            </div>
        `;
        
        const modal = this.createModal('Research Details', modalContent);
        
        // Add scroll debugging
        setTimeout(() => {
            const modalElement = modal.querySelector('.modal');
            const contentElement = modal.querySelector('.modal-content');
            console.log('📏 Modal height:', modalElement.offsetHeight);
            console.log('📏 Content height:', contentElement.scrollHeight);
            console.log('📏 Modal scrollable:', modalElement.scrollHeight > modalElement.offsetHeight);
            console.log('📏 Content scrollable:', contentElement.scrollHeight > contentElement.offsetHeight);
        }, 100);
        
        document.body.appendChild(modal);
    }
    
    extractResearchField(researchElement, fieldName) {
        console.log(`🔍 Looking for field: "${fieldName}"`);
        // Look for a research section with the given field name
        const sections = researchElement.querySelectorAll('.research-section');
        console.log(`📊 Found ${sections.length} research sections`);
        
        for (const section of sections) {
            const strongElement = section.querySelector('strong');
            if (strongElement) {
                console.log(`📝 Section strong text: "${strongElement.textContent}"`);
                if (strongElement.textContent.includes(fieldName)) {
                    // Extract text after the strong element
                    const text = section.textContent.replace(strongElement.textContent, '').trim();
                    console.log(`✅ Found "${fieldName}": "${text}"`);
                    return text;
                }
            }
        }
        console.log(`❌ Field "${fieldName}" not found`);
        return null;
    }
    
    async saveToDatabase(companyName, website) {
        console.log(`Saving ${companyName} to database...`);
        
        if (!confirm(`Save ${companyName} to the database? This will store the research data permanently.`)) {
            return;
        }
        
        try {
            const response = await fetch('/api/save-researched-company', {
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
            
            if (response.ok && data.success) {
                this.showSuccess(`${companyName} saved to database successfully`);
                
                // Update the result card to show it's now in database
                const resultCard = document.querySelector(`[data-company-name="${this.escapeHtml(companyName)}"]`);
                if (resultCard) {
                    // Update controls to show database options instead of research options
                    const controlsDiv = resultCard.querySelector('.research-controls');
                    if (controlsDiv) {
                        const newControls = this.getResearchControls({
                            company_name: companyName,
                            website: website,
                            research_status: 'completed',
                            is_researched: false, // Now in database
                            database_id: data.company_id || 'new'
                        });
                        controlsDiv.innerHTML = newControls;
                    }
                    
                    // Update meta information
                    const metaDiv = resultCard.querySelector('.result-meta small');
                    if (metaDiv) {
                        metaDiv.innerHTML = metaDiv.innerHTML + ' • Saved to Database';
                    }
                }
                
            } else {
                this.showError(data.error || 'Failed to save company to database');
            }
        } catch (error) {
            console.error('Save to database error:', error);
            this.showError('Network error saving to database');
        }
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
                                ${company.website ? `
                                    <button class="btn-mini btn-website" onclick="window.open('${this.escapeHtml(company.website)}', '_blank')" title="Open ${this.escapeHtml(company.name)} website">
                                        🌐 Website
                                    </button>
                                ` : ''}
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
    
    showDiscoveryProgress(companyName) {
        // Hide results section first
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.classList.add('hidden');
        }
        
        // Create or show discovery progress container
        let progressContainer = document.getElementById('discoveryProgress');
        if (!progressContainer) {
            progressContainer = document.createElement('div');
            progressContainer.id = 'discoveryProgress';
            progressContainer.className = 'discovery-progress-container';
            
            const searchCard = document.querySelector('.search-card');
            searchCard.parentNode.insertBefore(progressContainer, searchCard.nextSibling);
        }
        
        // Discovery phases with realistic timing
        const phases = [
            { id: 'phase-init', name: 'Initializing Discovery', icon: '🔍', duration: 500 },
            { id: 'phase-database', name: 'Checking Database', icon: '🗄️', duration: 800 },
            { id: 'phase-llm', name: 'AI Research & Analysis', icon: '🧠', duration: 12000 },
            { id: 'phase-enhance', name: 'Enhancing Results', icon: '⚡', duration: 2000 },
            { id: 'phase-complete', name: 'Discovery Complete', icon: '✅', duration: 500 }
        ];
        
        progressContainer.innerHTML = `
            <div class="discovery-header">
                <h3><span class="discovery-icon">🚀</span> Discovering companies similar to "${companyName}"</h3>
                <div class="discovery-spinner"></div>
            </div>
            <div class="discovery-phases">
                ${phases.map(phase => `
                    <div class="discovery-phase" id="${phase.id}">
                        <div class="phase-icon">${phase.icon}</div>
                        <div class="phase-content">
                            <div class="phase-name">${phase.name}</div>
                            <div class="phase-status">Waiting...</div>
                            <div class="phase-progress">
                                <div class="phase-progress-bar">
                                    <div class="phase-progress-fill" style="width: 0%"></div>
                                </div>
                            </div>
                        </div>
                        <div class="phase-check">⏳</div>
                    </div>
                `).join('')}
            </div>
            <div class="discovery-stats">
                <div class="stat-item">
                    <span class="stat-label">Companies Found</span>
                    <span class="stat-value" id="companiesFound">0</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Sources Used</span>
                    <span class="stat-value" id="sourcesUsed">AI Research</span>
                </div>
            </div>
        `;
        
        progressContainer.style.display = 'block';
        progressContainer.classList.add('fade-in-up');
        
        // Start animated progress
        this.animateDiscoveryProgress(phases);
    }
    
    animateDiscoveryProgress(phases) {
        let currentPhase = 0;
        
        const runPhase = (phaseIndex) => {
            if (phaseIndex >= phases.length) return;
            
            const phase = phases[phaseIndex];
            const phaseElement = document.getElementById(phase.id);
            
            if (!phaseElement) return;
            
            // Mark previous phase as completed
            if (phaseIndex > 0) {
                const prevPhase = document.getElementById(phases[phaseIndex - 1].id);
                if (prevPhase) {
                    prevPhase.classList.remove('running');
                    prevPhase.classList.add('completed');
                    prevPhase.querySelector('.phase-status').textContent = 'Completed';
                    prevPhase.querySelector('.phase-check').textContent = '✅';
                    prevPhase.querySelector('.phase-progress-fill').style.width = '100%';
                }
            }
            
            // Start current phase
            phaseElement.classList.add('running');
            phaseElement.querySelector('.phase-status').textContent = 'Running...';
            phaseElement.querySelector('.phase-check').textContent = '🔄';
            
            // Animate progress bar
            const progressFill = phaseElement.querySelector('.phase-progress-fill');
            let progress = 0;
            const interval = 50;
            const increment = 100 / (phase.duration / interval);
            
            const progressInterval = setInterval(() => {
                progress += increment;
                if (progress >= 100) {
                    progress = 100;
                    clearInterval(progressInterval);
                    
                    // Add some dynamic text updates
                    if (phase.id === 'phase-llm') {
                        const companiesFound = Math.min(10, Math.floor(Math.random() * 8) + 3);
                        document.getElementById('companiesFound').textContent = companiesFound;
                        phaseElement.querySelector('.phase-status').textContent = `Found ${companiesFound} similar companies`;
                    }
                    
                    // Move to next phase after a short delay
                    setTimeout(() => {
                        runPhase(phaseIndex + 1);
                    }, 300);
                }
                
                progressFill.style.width = `${progress}%`;
            }, interval);
        };
        
        // Start with first phase
        runPhase(0);
    }
    
    hideDiscoveryProgress() {
        const progressContainer = document.getElementById('discoveryProgress');
        if (progressContainer) {
            progressContainer.style.display = 'none';
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
    console.log('🏁 DOM loaded, initializing Theodore UI...');
    try {
        window.theodoreUI = new TheodoreUI();
        console.log('✅ Theodore UI initialized successfully');
        console.log('🔍 Available functions:', Object.getOwnPropertyNames(window.theodoreUI.__proto__));
    } catch (error) {
        console.error('❌ Failed to initialize Theodore UI:', error);
    }
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
        max-width: 600px;
        width: 90%;
        max-height: 85vh;
        overflow-y: auto;
        overflow-x: hidden;
    }

    .modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px;
        border-bottom: 1px solid var(--border-subtle);
        background: var(--bg-secondary);
        position: sticky;
        top: 0;
        z-index: 1;
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
    
    .research-details {
        min-height: 1000px; /* Force scroll for testing */
        background: linear-gradient(45deg, transparent 0%, rgba(255,0,0,0.1) 50%, transparent 100%);
        border: 2px dashed rgba(255,255,255,0.2); /* Visual indicator for testing */
    }
    
    .research-details .detail-section {
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid var(--border-subtle);
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    .research-details .detail-section:last-child {
        border-bottom: none;
    }
    
    .research-details .detail-section h4 {
        margin: 0 0 10px 0;
        color: var(--text-primary);
        font-size: 1.1rem;
    }
    
    .research-details .detail-item {
        margin-bottom: 8px;
        line-height: 1.5;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    .research-details .detail-item strong {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    .research-details .description-text {
        background: var(--bg-tertiary);
        padding: 12px;
        border-radius: 8px;
        border-left: 3px solid var(--accent-color);
        font-style: italic;
        line-height: 1.6;
        word-wrap: break-word;
        overflow-wrap: break-word;
        max-width: 100%;
    }
    
    .research-details .research-meta {
        margin-top: 20px;
        padding-top: 15px;
        border-top: 1px solid var(--border-subtle);
        text-align: center;
    }
    
    .research-meta-info {
        background: var(--bg-tertiary);
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 0.9rem;
        color: var(--text-muted);
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