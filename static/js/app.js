// Theodore Web UI - Modern JavaScript

class TheodoreUI {
    constructor() {
        // Browser compatibility detection
        this.isVivaldi = navigator.userAgent.includes('Vivaldi');
        this.isRestrictiveBrowser = this.isVivaldi; // Add other restrictive browsers here
        
        if (this.isRestrictiveBrowser) {
            console.log('Restrictive browser detected, enabling compatibility mode');
        }
        
        this.initializeEventListeners();
        this.setupFormValidation();
        this.initializeAnimations();
        this.initializeDatabaseBrowser();
        this.initializeDatabaseSearch();
        this.activeResearchJobs = new Map(); // Track active research jobs
        this.pollingIntervals = new Map(); // Track polling intervals
        this.currentPollingInterval = null; // Track main progress polling
        this.researchDataCache = new Map(); // Store research results data
        this.databaseSearchState = {}; // Store current search state
    }

    initializeEventListeners() {
        // Main search form
        const searchForm = document.getElementById('searchForm');
        if (searchForm) {
            searchForm.addEventListener('submit', this.handleDiscovery.bind(this));
        } else {
        }

        // Process company form
        const processForm = document.getElementById('processForm');
        if (processForm) {
            processForm.addEventListener('submit', this.handleProcessing.bind(this));
        } else {
        }

        // Search on Enter key press only
        const companyInput = document.getElementById('companyName');
        if (companyInput) {
            let searchController = null; // To cancel previous requests
            
            // Trigger search on Enter key
            companyInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault(); // Prevent form submission if inside a form
                    
                    // Cancel previous request if still pending
                    if (searchController) {
                        searchController.abort();
                    }
                    
                    searchController = new AbortController();
                    this.handleRealTimeSearch(e.target.value, searchController);
                }
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

        // Filter change listeners
        const businessModelFilter = document.getElementById('businessModelFilter');
        const categoryFilter = document.getElementById('categoryFilter');
        
        if (businessModelFilter) {
            businessModelFilter.addEventListener('change', this.updateFilterStatus.bind(this));
        }
        if (categoryFilter) {
            categoryFilter.addEventListener('change', this.updateFilterStatus.bind(this));
        }
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
        
        // Show discovery progress
        this.showDiscoveryProgress(companyName);

        // Get active filters
        const activeFilters = this.getActiveFilters();

        try {
            const response = await fetch('/api/discover', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    company_name: companyName,
                    limit: parseInt(limit),
                    ...activeFilters
                })
            });

            const data = await response.json();

            if (response.ok) {
                
                // Handle both success and error response structures
                const results = data.results || data.companies || [];
                
                if (results.length > 0) {
                    // Log each company to console for debugging
                    results.forEach((company, index) => {
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
        

        if (!companyName.trim()) {
            this.showError('Please enter a company name');
            return;
        }
        
        // Apply frontend URL normalization and domain discovery
        let normalizedWebsite = website ? website.trim() : '';
        
        // Add https:// if missing
        if (normalizedWebsite && !normalizedWebsite.startsWith('http://') && !normalizedWebsite.startsWith('https://')) {
            normalizedWebsite = `https://${normalizedWebsite}`;
        }

        // Show helpful message if no website provided
        if (!normalizedWebsite) {
            this.showInfo(`🔍 No website provided for ${companyName.trim()}. Theodore will attempt to discover the company website automatically and generate a fallback URL if needed.`);
        }

        // Start processing with progress display
        this.startProcessing(companyName.trim(), normalizedWebsite);
    }

    async startProcessing(companyName, website) {
        
        // Show progress container and hide results
        const resultsEl = document.getElementById('processResults');
        const progressEl = document.getElementById('progressContainer');
        
        
        if (resultsEl) {
            resultsEl.style.display = 'none';
        }
        
        if (progressEl) {
            progressEl.style.display = 'block';
        } else {
        }
        
        // Update progress title
        document.getElementById('progressTitle').textContent = `Processing ${companyName}...`;
        
        // Reset all phases to pending
        this.resetProgressPhases();
        
        // Disable form
        const processButton = document.getElementById('processButton');
        processButton.disabled = true;
        processButton.innerHTML = '<span>⏳</span> Processing...';
        
        this.clearMessages();
        
        // Start progress polling immediately with error handling
        const progressContainer = document.getElementById('progressContainer');
        if (!this.isRestrictiveBrowser) {
            try {
                this.pollCurrentJobProgress(progressContainer, companyName);
            } catch (pollError) {
                console.log('Progress polling blocked by browser security:', pollError);
            }
        } else {
            console.log('Skipping progress polling in restrictive browser mode');
        }
        
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
                
                // Clear the form after successful processing
                setTimeout(() => {
                    document.getElementById('processForm').reset();
                }, 3000); // Clear after 3 seconds to allow user to see success message
            } else {
                this.showProcessingError(data.error || 'Processing failed');
                this.showError(`Failed to process ${companyName}: ${data.error}`);
            }

        } catch (error) {
            console.error('Processing error:', error);
            this.showProcessingError(`Network error: ${error.message}`);
            this.showError(`Failed to process ${companyName}: ${error.message}`);
        } finally {
            // Stop progress polling
            this.stopProgressPolling(companyName);
            
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
        
        // Store company ID for details button
        window.lastProcessedCompanyId = result.company_id;
        
        // Update summary stats
        const pagesEl = document.getElementById('resultPages');
        const timeEl = document.getElementById('resultTime');
        const lengthEl = document.getElementById('resultLength');
        
        if (pagesEl) pagesEl.textContent = result.pages_processed || 0;
        if (timeEl) timeEl.textContent = `${(result.processing_time || 0).toFixed(1)}s`;
        if (lengthEl) lengthEl.textContent = `${result.sales_intelligence.length} chars`;
        
        // Update token usage and cost stats
        if (result.token_usage) {
            const tokensEl = document.getElementById('resultTokens');
            const costEl = document.getElementById('resultCost');
            const llmCallsEl = document.getElementById('resultLLMCalls');
            
            if (tokensEl) {
                const totalTokens = (result.token_usage.total_input_tokens || 0) + (result.token_usage.total_output_tokens || 0);
                tokensEl.textContent = `${totalTokens.toLocaleString()} tokens`;
            }
            if (costEl) {
                const cost = result.token_usage.total_cost_usd || 0;
                costEl.textContent = `$${cost.toFixed(4)}`;
            }
            if (llmCallsEl) {
                llmCallsEl.textContent = `${result.token_usage.llm_calls_count || 0} calls`;
            }
        }
        
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
        
        if (!phaseId) {
            return;
        }
        
        const element = document.getElementById(phaseId);
        
        if (!element) {
            return;
        }
        
        element.className = `phase-item ${status}`;
        
        const statusEl = element.querySelector('.phase-status');
        const detailsEl = element.querySelector('.phase-details');
        const checkEl = element.querySelector('.phase-check');
        
        // Show user-friendly status
        if (statusEl) {
            const statusMap = {
                'running': 'In Progress',
                'completed': 'Completed',
                'failed': 'Failed',
                'pending': 'Pending'
            };
            statusEl.textContent = statusMap[status] || status.charAt(0).toUpperCase() + status.slice(1);
        }
        
        // Show user-friendly details
        if (detailsEl) {
            let detailsText = '';
            if (details) {
                if (typeof details === 'string') {
                    detailsText = details;
                } else if (typeof details === 'object') {
                    // Convert object to meaningful text for phase details
                    if (phaseName === 'Link Discovery' && details.target_url) {
                        try {
                            detailsText = `Analyzing ${new URL(details.target_url).hostname}`;
                        } catch {
                            detailsText = `Analyzing ${details.target_url}`;
                        }
                    } else if (phaseName === 'Content Extraction' && details.current_page) {
                        try {
                            detailsText = `Extracting: ${new URL(details.current_page).pathname}`;
                        } catch {
                            detailsText = `Extracting: ${details.current_page}`;
                        }
                    } else if (details.status_message) {
                        detailsText = details.status_message;
                    }
                }
            }
            detailsEl.textContent = detailsText;
        }
        
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
        
        // Convert details to user-friendly text
        let detailsText = '';
        if (details) {
            if (typeof details === 'string') {
                detailsText = details;
            } else if (typeof details === 'object') {
                // Convert object to meaningful text based on phase
                if (phaseName === 'Link Discovery' && details.target_url) {
                    detailsText = `Analyzing ${details.target_url}`;
                } else if (phaseName === 'LLM Page Selection' && details.pages_selected) {
                    detailsText = `Selected ${details.pages_selected} promising pages`;
                } else if (phaseName === 'Content Extraction' && details.current_page) {
                    detailsText = `Extracting from ${details.current_page}`;
                } else if (details.status_message) {
                    detailsText = details.status_message;
                } else {
                    // Fallback: convert object to readable format
                    const meaningfulKeys = ['status', 'target_url', 'current_page', 'pages_completed', 'total_pages'];
                    const values = meaningfulKeys
                        .filter(key => details[key] !== undefined && details[key] !== null)
                        .map(key => `${key}: ${details[key]}`);
                    detailsText = values.length > 0 ? values.join(', ') : '';
                }
            }
        }
        
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `
            <span class="log-timestamp">[${timestamp}]</span>
            <strong>${phaseName}</strong>: ${status}${detailsText ? ` - ${detailsText}` : ''}
        `;
        
        logContainer.appendChild(logEntry);
        
        // Auto-scroll to bottom with Vivaldi compatibility
        try {
            logContainer.scrollTop = logContainer.scrollHeight;
        } catch (e) {
            console.log('Auto-scroll blocked by browser security policy');
        }
    }
    
    stopProgressPolling(companyName) {
        // Clear any polling intervals for this company
        const intervalId = this.pollingIntervals.get(companyName);
        if (intervalId) {
            clearTimeout(intervalId);
            this.pollingIntervals.delete(companyName);
        }
    }

    async handleRealTimeSearch(query, controller = null) {
        
        // Store current query to prevent showing stale results
        this.currentSearchQuery = query.trim().toLowerCase();
        
        if (!query.trim() || query.length < 2) {
            try {
                this.hideSearchSuggestions('query_too_short');
            } catch (e) {
                console.log('Browser blocked hideSearchSuggestions');
            }
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
                
                // Filter results to only show matches that contain the search query
                const filteredResults = data.results.filter(result => 
                    result.name.toLowerCase().includes(this.currentSearchQuery)
                );
                
                
                if (filteredResults.length > 0) {
                    this.showSearchSuggestions(filteredResults);
                } else {
                    try {
                        this.hideSearchSuggestions('no_filtered_results');
                    } catch (e) {
                        console.log('Browser blocked hideSearchSuggestions');
                    }
                }
            } else {
                try {
                    this.hideSearchSuggestions('no_api_results');
                } catch (e) {
                    console.log('Browser blocked hideSearchSuggestions');
                }
            }

        } catch (error) {
            if (error.name === 'AbortError') {
                // Request was cancelled, this is expected
                return;
            }
            console.error('Search error:', error);
            try {
                this.hideSearchSuggestions('search_error');
            } catch (e) {
                console.log('Browser blocked hideSearchSuggestions');
            }
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
        
        // If switching to batch tab, initialize batch processing
        if (tabId === 'batchTab') {
            this.initializeBatchProcessing();
        }
        
        // If switching to classification tab, load classification analytics
        if (tabId === 'classificationTab') {
            this.loadClassificationAnalytics();
        }
        
        // REMOVED: Don't hide results when switching tabs - let users keep their work visible
        // Results will persist until user manually processes another company
    }

    displayResults(data) {
        
        const resultsContainer = document.getElementById('results');
        const resultsSection = document.getElementById('resultsSection');
        const resultsCountElement = document.getElementById('resultsCount');


        if (!resultsContainer || !resultsSection) {
            return;
        }

        // Update the results count
        const resultCount = data.results.length;
        if (resultsCountElement) {
            resultsCountElement.textContent = `${resultCount} found`;
        }

        if (data.results.length === 0) {
            resultsContainer.innerHTML = this.createEmptyState();
        } else {
            const resultCards = data.results.map(result => {
                const cardHTML = this.createResultCard(result);
                return cardHTML;
            });
            
            const finalHTML = resultCards.join('');
            
            resultsContainer.innerHTML = finalHTML;
            
            // Check if HTML was actually set
            setTimeout(() => {
            }, 100);
        }

        resultsSection.classList.remove('hidden');
        
        // Ensure results section is properly visible
        resultsSection.style.display = 'block';
        
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
        
        const researchStatusBadge = this.getResearchStatusBadge(result.research_status);
        const researchControls = this.getResearchControls(result);
        const progressId = `progress-${result.company_name.replace(/\s+/g, '-')}`;
        const classificationBadge = this.createClassificationBadge(result);

        return `
            <div class="result-card" data-score="${scoreClass}" data-company-name="${this.escapeHtml(result.company_name)}" data-website="${this.escapeHtml(result.website || '')}">
                <div class="result-header">
                    <div>
                        <div class="result-company-wrapper">
                            <div class="result-company">${this.escapeHtml(result.company_name)}</div>
                            ${researchStatusBadge}
                        </div>
                        <div class="result-type">${this.escapeHtml(result.relationship_type || 'Similar Company')}</div>
                        ${classificationBadge}
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
                    <div class="progress-details" style="display: none; font-size: 0.8em; margin-top: 5px; opacity: 0.8; white-space: pre-line;"></div>
                </div>
            </div>
        `;
    }

    createClassificationBadge(result) {
        // Check if classification data exists
        if (!result.saas_classification && !result.is_saas) {
            return ''; // No classification data available
        }

        const isSaas = result.is_saas;
        const category = result.saas_classification || 'Unclassified';
        const confidence = result.classification_confidence;

        return `
            <div class="classification-badge">
                <span class="saas-indicator ${isSaas ? 'saas' : 'non-saas'}">
                    ${isSaas ? 'SaaS' : 'Non-SaaS'}
                </span>
                <span class="category-tag">${this.escapeHtml(category)}</span>
                ${confidence ? `<span class="confidence-score">${(confidence * 100).toFixed(0)}%</span>` : ''}
            </div>
        `;
    }

    createTableClassificationBadge(company) {
        // Check if classification data exists
        if (!company.saas_classification) {
            return '<span class="no-classification">Not classified</span>';
        }

        const isSaas = company.is_saas;
        const category = company.saas_classification;
        const confidence = company.classification_confidence;

        return `
            <div class="table-classification">
                <div class="classification-type">
                    <span class="saas-indicator-small ${isSaas ? 'saas' : 'non-saas'}">
                        ${isSaas ? 'SaaS' : 'Non-SaaS'}
                    </span>
                </div>
                <div class="classification-category">${this.escapeHtml(category)}</div>
                ${confidence ? `<div class="classification-confidence">${(confidence * 100).toFixed(0)}% confidence</div>` : ''}
            </div>
        `;
    }

    renderClassificationSection(company) {
        // Check if classification data exists
        if (!company.saas_classification && !company.is_saas) {
            return `
                <div class="detail-section">
                    <h4>🏷️ Business Model Classification</h4>
                    <div class="classification-missing">
                        <p style="color: var(--text-muted); font-style: italic;">
                            ⏳ Not yet classified. Run classification to analyze this company's business model.
                        </p>
                    </div>
                </div>
            `;
        }

        const isSaas = company.is_saas;
        const category = company.saas_classification || 'Unclassified';
        const confidence = company.classification_confidence;
        const justification = company.classification_justification;
        const timestamp = company.classification_timestamp;

        return `
            <div class="detail-section">
                <h4>🏷️ Business Model Classification</h4>
                <div class="classification-details">
                    <div class="classification-row">
                        <span class="label">Type:</span>
                        <span class="saas-badge ${isSaas ? 'saas' : 'non-saas'}">
                            ${isSaas ? 'SaaS' : 'Non-SaaS'}
                        </span>
                    </div>
                    <div class="classification-row">
                        <span class="label">Category:</span>
                        <span class="category">${this.escapeHtml(category)}</span>
                    </div>
                    ${confidence ? `
                        <div class="classification-row">
                            <span class="label">Confidence:</span>
                            <span class="confidence">${(confidence * 100).toFixed(1)}%</span>
                        </div>
                    ` : ''}
                    ${justification ? `
                        <div class="classification-row">
                            <span class="label">Justification:</span>
                            <span class="justification">${this.escapeHtml(justification)}</span>
                        </div>
                    ` : ''}
                    ${timestamp ? `
                        <div class="classification-row">
                            <span class="label">Classified:</span>
                            <span class="timestamp">${new Date(timestamp).toLocaleDateString()}</span>
                        </div>
                    ` : ''}
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
        
        suggestions.innerHTML = suggestionHTML;

        // Add click handlers with proper safeguards
        suggestions.onclick = null; // Clear any existing handlers
        
        // Use mousedown instead of click to avoid conflicts, and add delay
        setTimeout(() => {
            suggestions.addEventListener('mousedown', (e) => {
                const suggestionItem = e.target.closest('.suggestion-item');
                if (suggestionItem && e.isTrusted) { // Only handle real user interactions
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Fill in the input field
                    input.value = suggestionItem.dataset.name;
                    
                    // Hide suggestions after a small delay to ensure the value is set
                    setTimeout(() => {
                        try {
                            this.hideSearchSuggestions('suggestion_selected');
                        } catch (e) {
                            console.log('Browser blocked hideSearchSuggestions');
                        }
                    }, 50);
                }
            });
        }, 200); // Wait 200ms before attaching handlers to avoid phantom events

        suggestions.classList.add('show');
    }

    hideSearchSuggestions(reason = 'unknown') {
        try {
            // Prevent hiding if suggestions were just shown (within 200ms)
            if (this.suggestionsShownAt && (Date.now() - this.suggestionsShownAt) < 200) {
                return;
            }
            
            // Skip console.trace() in restrictive browsers like Vivaldi
            const suggestions = document.getElementById('searchSuggestions');
            if (suggestions) {
                suggestions.classList.remove('show');
            }
        } catch (e) {
            // Silently handle browser restrictions (Vivaldi, etc.)
            console.log('Search suggestions hiding blocked by browser security');
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

        // Add ESC key support
        const handleEscKey = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', handleEscKey);
            }
        };
        document.addEventListener('keydown', handleEscKey);

        // Clean up event listener when modal is removed
        const originalRemove = modal.remove.bind(modal);
        modal.remove = () => {
            document.removeEventListener('keydown', handleEscKey);
            originalRemove();
        };

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

    escapeJs(text) {
        // Escape text for use in JavaScript strings
        return text.replace(/\\/g, '\\\\')
                  .replace(/'/g, "\\'")
                  .replace(/"/g, '\\"')
                  .replace(/\n/g, '\\n')
                  .replace(/\r/g, '\\r')
                  .replace(/\t/g, '\\t');
    }

    // Filter Management Functions
    toggleFilters() {
        const content = document.getElementById('filtersContent');
        const toggleText = document.getElementById('filtersToggleText');
        const toggleIcon = document.getElementById('filtersToggleIcon');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            toggleText.textContent = 'Hide Filters';
            toggleIcon.textContent = '▲';
        } else {
            content.style.display = 'none';
            toggleText.textContent = 'Show Filters';
            toggleIcon.textContent = '▼';
        }
    }

    clearFilters() {
        const businessModelFilter = document.getElementById('businessModelFilter');
        const categoryFilter = document.getElementById('categoryFilter');
        
        if (businessModelFilter) businessModelFilter.value = '';
        if (categoryFilter) categoryFilter.value = '';
        
        this.updateFilterStatus();
    }

    updateFilterStatus() {
        const businessModelFilter = document.getElementById('businessModelFilter');
        const categoryFilter = document.getElementById('categoryFilter');
        const filterStatus = document.getElementById('filterStatus');
        
        const activeFilters = [];
        
        if (businessModelFilter && businessModelFilter.value) {
            const displayValue = businessModelFilter.value === 'saas' ? 'SaaS' : 'Non-SaaS';
            activeFilters.push(`Type: ${displayValue}`);
        }
        
        if (categoryFilter && categoryFilter.value) {
            activeFilters.push(`Category: ${categoryFilter.value}`);
        }
        
        if (activeFilters.length > 0) {
            filterStatus.textContent = `Active: ${activeFilters.join(', ')}`;
            filterStatus.style.color = 'var(--text-primary)';
        } else {
            filterStatus.textContent = 'No filters active';
            filterStatus.style.color = 'var(--text-muted)';
        }
    }

    getActiveFilters() {
        const businessModelFilter = document.getElementById('businessModelFilter');
        const categoryFilter = document.getElementById('categoryFilter');
        
        const filters = {};
        
        if (businessModelFilter && businessModelFilter.value) {
            filters.business_model = businessModelFilter.value;
        }
        
        if (categoryFilter && categoryFilter.value) {
            filters.category = categoryFilter.value;
        }
        
        return filters;
    }

    renderJobListingsDetails(jobDetails) {
        if (!jobDetails || typeof jobDetails !== 'object') {
            return '';
        }

        let detailsHtml = '';

        // Career page URL as clickable link
        if (jobDetails.career_page_url) {
            detailsHtml += `
                <div class="job-detail-item">
                    <strong>📄 Career Page:</strong> 
                    <a href="${this.escapeHtml(jobDetails.career_page_url)}" target="_blank" class="career-link">
                        ${this.escapeHtml(jobDetails.career_page_url)}
                    </a>
                </div>
            `;
        }

        // Best job sites as comma-separated links/text
        if (jobDetails.best_job_sites && Array.isArray(jobDetails.best_job_sites)) {
            detailsHtml += `
                <div class="job-detail-item">
                    <strong>🔍 Best Job Sites:</strong> ${jobDetails.best_job_sites.map(site => this.escapeHtml(site)).join(', ')}
                </div>
            `;
        }

        // Typical roles as badges
        if (jobDetails.typical_roles && Array.isArray(jobDetails.typical_roles)) {
            const roleBadges = jobDetails.typical_roles.map(role => 
                `<span class="role-badge">${this.escapeHtml(role)}</span>`
            ).join(' ');
            detailsHtml += `
                <div class="job-detail-item">
                    <strong>💼 Typical Roles:</strong> 
                    <div class="role-badges">${roleBadges}</div>
                </div>
            `;
        }

        // Search tips
        if (jobDetails.search_tips) {
            detailsHtml += `
                <div class="job-detail-item">
                    <strong>💡 Search Tips:</strong> ${this.escapeHtml(jobDetails.search_tips)}
                </div>
            `;
        }

        // Company info
        if (jobDetails.company_info) {
            detailsHtml += `
                <div class="job-detail-item">
                    <strong>🏢 Company Info:</strong> ${this.escapeHtml(jobDetails.company_info)}
                </div>
            `;
        }

        // Hiring status with appropriate icon
        if (jobDetails.hiring_status) {
            const statusIcon = jobDetails.hiring_status.toLowerCase().includes('active') ? '✅' : 
                              jobDetails.hiring_status.toLowerCase().includes('likely') ? '🔄' : '❓';
            detailsHtml += `
                <div class="job-detail-item">
                    <strong>${statusIcon} Hiring Status:</strong> ${this.escapeHtml(jobDetails.hiring_status)}
                </div>
            `;
        }

        return detailsHtml ? `<div class="job-listings-details">${detailsHtml}</div>` : '';
    }

    extractJobListingsDetailsFromHTML(researchDataElement) {
        // Look for existing job-listings-section in the research data
        const jobListingsSection = researchDataElement.querySelector('.job-listings-section');
        if (!jobListingsSection) {
            return '';
        }

        // Look for existing job-listings-details
        const existingDetails = jobListingsSection.querySelector('.job-listings-details');
        if (existingDetails) {
            // Return the existing enhanced details
            return existingDetails.outerHTML;
        }

        // If no enhanced details found, return empty (basic display only)
        return '';
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
        
        // Escape values for safe HTML attributes and JavaScript
        const escapedName = this.escapeHtml(result.company_name);
        const escapedWebsite = this.escapeHtml(result.website || '');
        const jsEscapedName = this.escapeJs(result.company_name);
        const jsEscapedWebsite = this.escapeJs(result.website || '');
        
        // Add Open Website button for all statuses (if website available)
        const websiteButton = escapedWebsite ? `
            <button class="btn-mini btn-website" onclick="window.open('${jsEscapedWebsite}', '_blank')" title="Open ${escapedName} website">
                🌐 Website
            </button>
        ` : '';

        if (result.research_status === 'completed') {
            // Check if this is a researched company (not in database) or database company
            if (result.is_researched) {
                // Researched company - show research-specific controls
                return `
                    <button class="btn-mini btn-secondary" onclick="window.theodoreUI.viewResearchDetails('${jsEscapedName}')">
                        👁️ View Research
                    </button>
                    <button class="btn-mini btn-accent" onclick="window.theodoreUI.saveToDatabase('${jsEscapedName}', '${jsEscapedWebsite}')">
                        💾 Save to Database
                    </button>
                    <button class="btn-mini btn-primary" onclick="window.theodoreUI.reResearchCompany('${jsEscapedName}', '${jsEscapedWebsite}')">
                        🔄 Re-research
                    </button>
                    ${websiteButton}
                `;
            } else {
                // Database company - show database-specific controls
                return `
                    <button class="btn-mini btn-secondary" onclick="window.theodoreUI.viewCompanyDetails('${result.database_id}', '${jsEscapedName}')">
                        👁️ View Details
                    </button>
                    <button class="btn-mini btn-primary" onclick="window.theodoreUI.reResearchCompany('${jsEscapedName}', '${jsEscapedWebsite}')">
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
                <button class="btn-mini btn-danger" onclick="window.theodoreUI.cancelResearch('${jsEscapedName}')">
                    🛑 Cancel
                </button>
                ${websiteButton}
            `;
        } else {
            return `
                <button class="btn-mini btn-primary" onclick="window.theodoreUI.startResearch('${jsEscapedName}', '${jsEscapedWebsite}')">
                    🔬 Research Now
                </button>
                ${result.research_status === 'unknown' ? `
                    <button class="btn-mini btn-secondary" onclick="window.theodoreUI.previewResearch('${jsEscapedName}', '${jsEscapedWebsite}')">
                        👁️ Preview
                    </button>
                ` : ''}
                ${websiteButton}
            `;
        }
    }

    async startResearch(companyName, website) {
        
        // Validate inputs
        if (!companyName || !website) {
            console.error(`🟦 JS: ❌ VALIDATION ERROR - Missing required data`);
            console.error(`🟦 JS: companyName: '${companyName}'`);
            console.error(`🟦 JS: website: '${website}'`);
            this.showError('Missing company name or website');
            return;
        }
        
        // Update UI immediately
        this.updateResearchButton(companyName, 'researching');
        
        // Track this research job
        const jobData = {
            status: 'starting',
            startTime: Date.now(),
            companyName: companyName,
            website: website
        };
        this.activeResearchJobs.set(companyName, jobData);
        
        try {
            console.log(`🟦 JS: 📊 Starting research for ${companyName}`);
            
            const progressContainer = this.showResearchProgressContainer(companyName);
            
            // Start polling immediately, no delay
            this.pollCurrentJobProgress(progressContainer, companyName);
            
            const requestStartTime = Date.now();
            
            // Create abort controller for timeout
            const abortController = new AbortController();
            const timeoutDuration = 120000; // 2 minutes timeout (same as Add Company)
            
            console.log(`🟦 JS: ✅ Created AbortController, signal aborted: ${abortController.signal.aborted}`);
            
            const timeoutId = setTimeout(() => {
                console.log(`🟦 JS: ⏱️ Aborting request after ${timeoutDuration/1000} seconds`);
                abortController.abort(new DOMException('Research timeout', 'TimeoutError'));
            }, timeoutDuration);
            
            // USE THE SAME ENDPOINT AS "ADD COMPANY" - both should use identical process
            console.log(`🟦 JS: 🚀 Starting fetch request to /api/process-company (same as Add Company)`);
            
            const response = await fetch('/api/process-company', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    company_name: companyName,
                    website: website
                }),
                signal: abortController.signal
            });
            
            // Clear timeout if request completed
            clearTimeout(timeoutId);

            const requestEndTime = Date.now();
            const requestDuration = requestEndTime - requestStartTime;
            
            
            const data = await response.json();

            if (response.ok && data.success) {
                
                this.showSuccess(`Research completed for ${companyName}! Generated ${data.sales_intelligence?.length || 0} character sales intelligence.`);
                
                // Create enhanced company object from /api/process-company response
                const enhancedCompany = {
                    id: data.company_id,
                    name: data.company_name,
                    company_name: data.company_name,  // Required by getResearchControls
                    website: website,
                    company_description: data.sales_intelligence,
                    // Add required research status fields
                    is_researched: false,  // Set to false so View Details button shows
                    research_status: 'success',
                    database_id: data.company_id,  // Ensure database_id is set
                    // Add more fields as available from the response
                    processing_time: data.processing_time,
                    pages_processed: data.pages_processed,
                    company_id: data.company_id,
                    token_usage: data.token_usage,
                    pages_crawled: data.pages_processed ? Array(data.pages_processed).fill('processed') : [],
                    research_timestamp: new Date().toISOString(),
                    discovery_method: 'Deep AI Research'
                };
                
                // Store the enhanced company data for later access
                this.storeResearchData(companyName, enhancedCompany);
                
                // Update the result card with enhanced data
                this.updateResultCardWithResearch(companyName, enhancedCompany);
                
                // Update the research button to show completed status
                this.updateResearchButton(companyName, 'completed');
                
                // Hide progress container and cleanup
                this.hideResearchProgressContainer(companyName);
                this.cleanupResearchJob(companyName);
                
                // Automatically show the full company details modal after research completion
                // Use viewCompanyDetails with the database_id since the company is now saved
                if (data.company_id) {
                    this.viewCompanyDetails(data.company_id, companyName);
                } else {
                    // Fallback to research details if no company_id
                    this.viewResearchDetails(companyName);
                }
                
                
            } else {
                console.error(`🟦 JS: ❌ Response status: ${response.status}`);
                console.error(`🟦 JS: ❌ Success flag: ${data.success}`);
                console.error(`🟦 JS: ❌ Error message: ${data.error}`);
                console.error(`🟦 JS: ❌ Exception type: ${data.exception_type}`);
                console.error(`🟦 JS: ❌ Full error data:`, data);
                
                const errorMessage = data.error || 'Failed to complete research';
                this.showError(errorMessage);
                
                // Reset button on error
                this.updateResearchButton(companyName, 'unknown');
                
                // Hide progress container and cleanup
                this.hideResearchProgressContainer(companyName);
                this.cleanupResearchJob(companyName);
            }
        } catch (networkError) {
            console.error(`🟦 JS: ❌ Exception caught:`, networkError);
            console.error(`🟦 JS: ❌ Error name: ${networkError.name}`);
            console.error(`🟦 JS: ❌ Error message: ${networkError.message}`);
            console.error(`🟦 JS: ❌ Error stack:`, networkError.stack);
            
            // Clear the timeout if it was set
            if (typeof timeoutId !== 'undefined') {
                clearTimeout(timeoutId);
            }
            
            // Check if it's a specific type of error
            let errorMessage = 'Unexpected error during research';
            
            if (networkError.name === 'AbortError' || networkError.name === 'TimeoutError') {
                console.error(`🟦 JS: ❌ Request was aborted (timeout or manual cancellation)`);
                errorMessage = `Research request timed out. Large sites like Amazon may take 3-5 minutes to analyze completely.`;
            } else if (networkError instanceof TypeError) {
                console.error(`🟦 JS: ❌ This is a TypeError - likely network issue`);
                errorMessage = 'Network error during research - check connection';
            } else if (networkError instanceof SyntaxError) {
                console.error(`🟦 JS: ❌ This is a SyntaxError - likely JSON parsing issue`);
                errorMessage = 'Error parsing server response';
            } else if (networkError.message.includes('fetch')) {
                console.error(`🟦 JS: ❌ Fetch-related error`);
                errorMessage = 'Network error during research - check connection';
            } else {
                console.error(`🟦 JS: ❌ Unknown error type: ${typeof networkError}`);
                errorMessage = `Research failed: ${networkError.message}`;
            }
                
            this.showError(errorMessage);
            
            // Reset button on error  
            this.updateResearchButton(companyName, 'unknown');
            
            // Hide progress container and cleanup
            this.hideResearchProgressContainer(companyName);
            this.cleanupResearchJob(companyName);
            
        }
    }

    getProgressContainer(companyName) {
        const progressId = `progress-${companyName.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '')}`;
        return document.getElementById(progressId);
    }

    showResearchProgressContainer(companyName) {
        // Create or show progress container for this company
        const progressId = `progress-${companyName.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '')}`;
        let progressContainer = document.getElementById(progressId);
        
        
        if (!progressContainer) {
            
            // Create progress container
            progressContainer = document.createElement('div');
            progressContainer.id = progressId;
            progressContainer.className = 'research-progress-container';
            progressContainer.style.display = 'block';  // Force visible immediately
            progressContainer.style.marginTop = '20px';
            progressContainer.style.padding = '20px';
            progressContainer.style.background = 'rgba(255, 255, 255, 0.05)';
            progressContainer.style.border = '1px solid rgba(255, 255, 255, 0.1)';
            progressContainer.style.borderRadius = '12px';
            progressContainer.style.backdropFilter = 'blur(20px)';
            progressContainer.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.15)';
            
            progressContainer.innerHTML = `
                <div class="progress-header">
                    <h4 style="margin: 0 0 15px 0; color: #ffffff; font-size: 1.1rem; font-weight: 600;">🔬 Researching ${companyName}</h4>
                </div>
                <div class="progress-bar" style="width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; margin-bottom: 12px;">
                    <div class="progress-fill" style="width: 0%; height: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); transition: width 0.3s ease;"></div>
                </div>
                <div class="progress-text" style="color: #a0a0b2; font-size: 0.9rem; margin-bottom: 8px;">Initializing research...</div>
                <div class="progress-details" style="display: none; margin-top: 8px; padding: 8px; background: rgba(255, 255, 255, 0.03); border-radius: 6px; font-size: 0.8rem; color: #a0a0b2; white-space: pre-line; font-family: 'JetBrains Mono', monospace;"></div>
            `;
            
            // Insert after the results container - try multiple insertion points
            const resultsContainer = document.getElementById('results');
            const resultsSection = document.getElementById('resultsSection');
            const mainContent = document.querySelector('.main-content');
            
            
            if (resultsContainer) {
                resultsContainer.appendChild(progressContainer);
            } else if (resultsSection) {
                resultsSection.appendChild(progressContainer);
            } else if (mainContent) {
                mainContent.appendChild(progressContainer);
            } else {
                document.body.appendChild(progressContainer);
            }
        } else {
        }
        
        // Ensure it's visible and scroll to it
        progressContainer.style.display = 'block';
        progressContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        return progressContainer;
    }

    hideResearchProgressContainer(companyName) {
        const progressId = `progress-${companyName.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '')}`;
        const progressContainer = document.getElementById(progressId);
        
        if (progressContainer) {
            setTimeout(() => {
                progressContainer.style.display = 'none';
            }, 2000); // Hide after 2 seconds
        }
    }

    async pollCurrentJobProgress(progressContainer, companyName) {
        try {
            
            const response = await fetch('/api/progress/current');
            const data = await response.json();
            
            // FORCE SHOW the progress container in case it's hidden (with error handling)
            try {
                if (progressContainer) {
                    progressContainer.style.display = 'block';
                }
            } catch (styleError) {
                console.log('Progress container styling blocked by browser security');
            }

            // Handle different response statuses
            if (response.ok && data.status === 'recent_completion') {
                
                // Show completion in progress container (with error handling for browser restrictions)
                try {
                    const progressFill = progressContainer.querySelector('.progress-fill');
                    const progressText = progressContainer.querySelector('.progress-text');
                    const progressDetails = progressContainer.querySelector('.progress-details');
                    
                    if (progressFill) {
                        progressFill.style.width = '100%';
                        progressFill.style.backgroundColor = '#43e97b'; // Green for success
                    }
                    
                    if (progressText) {
                        progressText.textContent = '✅ Research Completed Successfully';
                    }
                    
                    if (progressDetails) {
                        progressDetails.textContent = `Research completed for ${companyName}`;
                        progressDetails.style.display = 'block';
                        progressDetails.style.color = '#43e97b'; // Green text
                    }
                } catch (domError) {
                    console.log('Progress DOM manipulation blocked by browser security:', domError);
                }
                
                // Show success message
                try {
                    this.showSuccess(`Research completed successfully for ${companyName}!`);
                } catch (msgError) {
                    console.log('Success message blocked by browser security');
                }
                
                // Stop polling and update button
                try {
                    this.updateResearchButton(companyName, 'completed');
                } catch (btnError) {
                    console.log('Button update blocked by browser security');
                }
                
                // Hide progress container after showing success
                try {
                    setTimeout(async () => {
                        try {
                            this.hideResearchProgressContainer(companyName);
                            this.cleanupResearchJob(companyName);
                            
                            // Fetch the company data from database and show modal
                            // First try to get the company ID from the progress data
                            if (data.progress && data.progress.company_id) {
                                await this.viewCompanyDetails(data.progress.company_id, companyName);
                            } else {
                                // Fallback to search by name
                                await this.viewCompanyDetailsByName(companyName);
                            }
                        } catch (cleanupError) {
                            console.log('Cleanup or modal display error:', cleanupError);
                        }
                    }, 3000); // Show success for 3 seconds
                } catch (timeoutError) {
                    console.log('setTimeout blocked by browser security');
                }
                
                return; // Stop polling
            } else if (response.ok && data.status === 'recent_failure') {
                
                // Show failure in progress container
                const progressFill = progressContainer.querySelector('.progress-fill');
                const progressText = progressContainer.querySelector('.progress-text');
                const progressDetails = progressContainer.querySelector('.progress-details');
                
                if (progressFill) {
                    progressFill.style.width = '100%';
                    progressFill.style.backgroundColor = '#ef4444'; // Red for failure
                }
                
                if (progressText) {
                    progressText.textContent = '❌ Research Failed';
                }
                
                if (progressDetails) {
                    progressDetails.textContent = data.message;
                    progressDetails.style.display = 'block';
                    progressDetails.style.color = '#ef4444'; // Red text
                }
                
                // Stop polling and show error
                this.showError(data.message);
                this.updateResearchButton(companyName, 'unknown');
                
                // Hide progress container after showing error
                setTimeout(() => {
                    this.hideResearchProgressContainer(companyName);
                    this.cleanupResearchJob(companyName);
                }, 5000); // Show error for 5 seconds
                
                return; // Stop polling
            }
            
            // Check for any progress data - prioritize current company, but accept any running job
            let relevantProgress = null;
            if (response.ok && data.progress) {
                // First priority: exact company name match
                if (data.progress.company_name === companyName) {
                    relevantProgress = data.progress;
                }
                // Second priority: any running job (for Add Company flow)
                else if (data.progress.status === 'running') {
                    relevantProgress = data.progress;
                }
            } else if (response.ok && data.status === 'recent_failure' && data.progress && data.progress.company_name === companyName) {
                relevantProgress = data.progress;
            }
            
            if (relevantProgress) {
                const progress = relevantProgress;
                
                // Check if job has failed
                if (progress.status === 'failed') {
                    
                    const progressFill = progressContainer.querySelector('.progress-fill');
                    const progressText = progressContainer.querySelector('.progress-text');
                    const progressDetails = progressContainer.querySelector('.progress-details');
                    
                    if (progressFill) {
                        progressFill.style.width = '100%';
                        progressFill.style.backgroundColor = '#ef4444'; // Red for failure
                    }
                    
                    if (progressText) {
                        progressText.textContent = '❌ Research Failed';
                    }
                    
                    if (progressDetails) {
                        progressDetails.textContent = progress.error || 'Unknown error';
                        progressDetails.style.display = 'block';
                        progressDetails.style.color = '#ef4444'; // Red text
                    }
                    
                    // Stop polling and show error
                    this.showError(progress.error || 'Research failed');
                    this.updateResearchButton(companyName, 'unknown');
                    
                    // Hide progress container after showing error
                    setTimeout(() => {
                        this.hideResearchProgressContainer(companyName);
                        this.cleanupResearchJob(companyName);
                    }, 5000);
                    
                    return; // Stop polling
                }
                
                // Update progress bar for running/completed jobs
                const progressFill = progressContainer.querySelector('.progress-fill');
                const progressText = progressContainer.querySelector('.progress-text');
                const progressDetails = progressContainer.querySelector('.progress-details');
                
                // Calculate overall progress percentage
                const totalPhases = progress.total_phases || 4;
                const currentPhase = progress.current_phase || 0;
                let progressPercent = Math.round((currentPhase / totalPhases) * 100);
                
                // Get current phase details - check all phases for the running one
                let currentPhaseData = null;
                if (progress.phases && progress.phases.length > 0) {
                    // Find the currently running phase
                    currentPhaseData = progress.phases.find(phase => phase.status === 'running');
                    // If no running phase, get the last completed phase
                    if (!currentPhaseData) {
                        currentPhaseData = progress.phases[progress.phases.length - 1];
                    }
                }
                
                
                if (progressFill) {
                    progressFill.style.width = `${Math.min(progressPercent, 100)}%`;
                }
                
                let statusText = `Researching ${companyName}`;
                let detailsText = '';
                
                if (currentPhaseData) {
                    statusText = `${currentPhaseData.name} (${currentPhase}/${totalPhases})`;
                    
                    // Add page-specific details for Content Extraction phase
                    if (currentPhaseData.name === 'Content Extraction') {
                        if (currentPhaseData.current_page) {
                            const pageName = currentPhaseData.current_page.split('/').pop() || currentPhaseData.current_page;
                            const pagesInfo = currentPhaseData.pages_completed && currentPhaseData.total_pages 
                                ? ` (${currentPhaseData.pages_completed}/${currentPhaseData.total_pages})` 
                                : '';
                            
                            detailsText = `📄 Scraping: ${pageName}${pagesInfo}`;
                            
                            // Show content preview if available
                            if (currentPhaseData.scraped_content_preview) {
                                const preview = currentPhaseData.scraped_content_preview.substring(0, 200);
                                detailsText += `\n📝 Content: ${preview}...`;
                            }
                            
                            // ENHANCED CONSOLE LOGGING - Show exactly what's being scraped
                            if (currentPhaseData.scraped_content_preview) {
                            }
                        }
                    }
                    
                    // Add details for other phases too
                    if (currentPhaseData.status === 'running') {
                        const phaseDetails = [];
                        if (currentPhaseData.details) {
                            Object.entries(currentPhaseData.details).forEach(([key, value]) => {
                                if (key !== 'current_page' && key !== 'scraped_content_preview') {
                                    phaseDetails.push(`${key}: ${value}`);
                                }
                            });
                        }
                        if (phaseDetails.length > 0 && !detailsText) {
                            detailsText = phaseDetails.join(', ');
                        }
                    }
                }
                
                if (progressText) {
                    progressText.textContent = statusText;
                }
                
                if (progressDetails) {
                    progressDetails.textContent = detailsText;
                    progressDetails.style.display = detailsText ? 'block' : 'none';
                    if (detailsText) {
                    }
                }

                // Update static phase elements for "Add Company" form
                
                if (progress.phases && progress.phases.length > 0) {
                    progress.phases.forEach(phase => {
                        this.updatePhaseProgress(phase.name, phase.status, phase.details);
                    });
                } else {
                }

                // Continue polling if job is still running
                if (progress.status === 'running') {
                    const timeoutId = setTimeout(() => {
                        this.pollCurrentJobProgress(progressContainer, companyName);
                    }, 2000); // Poll every 2 seconds
                    
                    // Use different tracking for main processing vs research
                    if (companyName && progressContainer.id !== 'progressContainer') {
                        // This is research polling
                        this.pollingIntervals.set(companyName, timeoutId);
                    } else {
                        // This is main processing polling
                        this.currentPollingInterval = timeoutId;
                    }
                }
            } else {
                // No matching job found, poll again more frequently in case it hasn't started yet
                const timeoutId = setTimeout(() => {
                    this.pollCurrentJobProgress(progressContainer, companyName);
                }, 1000); // Poll every 1 second when waiting for job to start
                
                // Use different tracking for main processing vs research
                if (companyName && progressContainer.id !== 'progressContainer') {
                    // This is research polling
                    this.pollingIntervals.set(companyName, timeoutId);
                } else {
                    // This is main processing polling
                    this.currentPollingInterval = timeoutId;
                }
            }
        } catch (error) {
            console.error('Progress polling error:', error);
            // Continue polling despite errors
            const timeoutId = setTimeout(() => {
                this.pollCurrentJobProgress(progressContainer, companyName);
            }, 5000); // Poll less frequently on error
            
            // Use different tracking for main processing vs research
            if (companyName && progressContainer.id !== 'progressContainer') {
                // This is research polling
                this.pollingIntervals.set(companyName, timeoutId);
            } else {
                // This is main processing polling
                this.currentPollingInterval = timeoutId;
            }
        }
    }

    cancelResearch(companyName) {
        
        // Cleanup the research job
        this.cleanupResearchJob(companyName);
        
        // Hide progress container
        this.hideResearchProgressContainer(companyName);
        
        // Reset button
        this.updateResearchButton(companyName, 'unknown');
        
        // Show user feedback
        this.showError(`Research canceled for ${companyName}`);
    }

    cancelCurrentJob() {
        
        // Stop polling if active
        if (this.currentPollingInterval) {
            clearTimeout(this.currentPollingInterval);
            this.currentPollingInterval = null;
        }
        
        // Call backend to cancel the job
        this.cancelJobOnServer();
        
        // Reset the process button
        const processButton = document.getElementById('processButton');
        if (processButton) {
            processButton.disabled = false;
            processButton.innerHTML = '<span>🔍</span> Add Company';
        }
        
        // Hide progress container
        const progressContainer = document.getElementById('progressContainer');
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
        
        // Reset all phases to pending
        this.resetProgressPhases();
        
        // Show user feedback
        this.showError('Processing canceled by user');
        
    }

    async cancelJobOnServer() {
        try {
            const response = await fetch('/api/cancel-current-job', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
            } else {
            }
        } catch (error) {
            console.error('Error canceling job on server:', error);
        }
    }

    resetProgressPhases() {
        const phases = ['link-discovery', 'page-selection', 'content-extraction', 'ai-analysis'];
        phases.forEach(phase => {
            const phaseElement = document.getElementById(`phase-${phase}`);
            if (phaseElement) {
                const statusElement = phaseElement.querySelector('.phase-status');
                const checkElement = phaseElement.querySelector('.phase-check');
                const detailsElement = phaseElement.querySelector('.phase-details');
                
                if (statusElement) statusElement.textContent = 'Pending';
                if (checkElement) checkElement.textContent = '⏳';
                if (detailsElement) detailsElement.textContent = '';
                
                phaseElement.classList.remove('running', 'completed', 'failed');
            }
        });
    }

    cleanupResearchJob(companyName) {
        // Remove from active jobs
        this.activeResearchJobs.delete(companyName);
        
        // Clear any polling intervals
        const intervalId = this.pollingIntervals.get(companyName);
        if (intervalId) {
            clearTimeout(intervalId);
            this.pollingIntervals.delete(companyName);
        }
        
    }

    updateResultCardWithResearch(companyName, researchedCompany) {
        
        // Find the result card for this company
        const resultCard = document.querySelector(`[data-company-name="${this.escapeHtml(companyName)}"]`);
        if (!resultCard) {
            console.warn(`❌ Result card not found for ${companyName}`);
            return;
        }
        

        // Update the card with enhanced research data
        if (researchedCompany.research_status === 'success' || researchedCompany.research_status === 'completed') {
            
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
                    ${researchedCompany.business_model_framework ? `
                        <div class="research-section">
                            <strong>Business Model Framework:</strong> ${this.escapeHtml(researchedCompany.business_model_framework)}
                        </div>
                    ` : ''}
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
                    ${researchedCompany.company_size && researchedCompany.company_size !== 'Unknown' ? `
                        <div class="research-section">
                            <strong>Company Size:</strong> ${this.escapeHtml(researchedCompany.company_size)}
                        </div>
                    ` : ''}
                    ${researchedCompany.tech_stack && researchedCompany.tech_stack.length > 0 ? `
                        <div class="research-section">
                            <strong>Tech Stack:</strong> ${researchedCompany.tech_stack.map(t => this.escapeHtml(t)).join(', ')}
                        </div>
                    ` : ''}
                    ${researchedCompany.value_proposition && researchedCompany.value_proposition.trim() ? `
                        <div class="research-section">
                            <strong>Value Proposition:</strong> ${this.escapeHtml(researchedCompany.value_proposition.substring(0, 150))}${researchedCompany.value_proposition.length > 150 ? '...' : ''}
                        </div>
                    ` : ''}
                    ${researchedCompany.pain_points && researchedCompany.pain_points.length > 0 ? `
                        <div class="research-section">
                            <strong>Pain Points:</strong> ${researchedCompany.pain_points.map(p => this.escapeHtml(p)).join(', ')}
                        </div>
                    ` : ''}
                    ${researchedCompany.job_listings && researchedCompany.job_listings !== 'Job data unavailable' ? `
                        <div class="research-section job-listings-section">
                            <strong>Job Listings:</strong> ${this.escapeHtml(researchedCompany.job_listings)}
                            ${this.renderJobListingsDetails(researchedCompany.job_listings_details)}
                        </div>
                    ` : ''}
                    <div class="research-section research-meta-info">
                        <strong>Research Info:</strong> 
                        ${researchedCompany.pages_crawled && researchedCompany.pages_crawled.length > 0 ? `${researchedCompany.pages_crawled.length} pages crawled` : 'Pages data unavailable'}
                        ${researchedCompany.crawl_depth && researchedCompany.crawl_depth > 0 ? ` • ${researchedCompany.crawl_depth} levels deep` : ''}
                        ${researchedCompany.processing_time && researchedCompany.processing_time > 0 ? ` • ${researchedCompany.processing_time.toFixed(1)}s processing time` : ''}
                        ${researchedCompany.research_timestamp ? ` • ${new Date(researchedCompany.research_timestamp).toLocaleString()}` : ''}
                    </div>
                </div>
            `;
            

            // Insert research data after business context or before meta
            if (businessContextDiv) {
                businessContextDiv.insertAdjacentHTML('afterend', researchHTML);
            } else if (resultMetaDiv) {
                resultMetaDiv.insertAdjacentHTML('beforebegin', researchHTML);
            }

            // Update research status badge
            const statusBadge = resultCard.querySelector('.research-status-badge');
            if (statusBadge) {
                statusBadge.innerHTML = '✅ Researched';
                statusBadge.className = 'research-status-badge status-completed';
            }
            
            // Store company ID in the result card for later use
            if (researchedCompany.company_id || researchedCompany.id) {
                resultCard.dataset.companyId = researchedCompany.company_id || researchedCompany.id;
            }

            // Update research controls
            const controlsDiv = resultCard.querySelector('.research-controls');
            if (controlsDiv) {
                const newControls = this.getResearchControls({
                    company_name: researchedCompany.company_name || researchedCompany.name,
                    website: researchedCompany.website,
                    research_status: 'completed',
                    is_researched: false, // Set to false so it shows "View Details" button
                    database_id: researchedCompany.company_id || researchedCompany.id
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
            const response = await fetch(`/api/progress/current?job_id=${jobId}`);
            const data = await response.json();

            if (response.ok && data.progress) {
                const progress = data.progress;
                
                // Update progress bar
                const progressFill = progressContainer.querySelector('.progress-fill');
                const progressText = progressContainer.querySelector('.progress-text');
                const progressDetails = progressContainer.querySelector('.progress-details');
                
                // Calculate overall progress percentage
                const totalPhases = progress.total_phases || 4;
                const currentPhase = progress.current_phase || 0;
                let progressPercent = Math.round((currentPhase / totalPhases) * 100);
                
                // Get current phase details
                const currentPhaseData = progress.phases && progress.phases.length > 0 
                    ? progress.phases[progress.phases.length - 1] 
                    : null;
                
                if (progressFill) {
                    progressFill.style.width = `${Math.min(progressPercent, 100)}%`;
                }
                
                let statusText = progress.company_name ? `Researching ${progress.company_name}` : 'Processing...';
                let detailsText = '';
                
                if (currentPhaseData) {
                    statusText = `${currentPhaseData.name} (${currentPhase}/${totalPhases})`;
                    
                    // Add page-specific details for Content Extraction phase
                    if (currentPhaseData.name === 'Content Extraction' && currentPhaseData.status === 'running') {
                        if (currentPhaseData.current_page) {
                            const pageName = currentPhaseData.current_page.split('/').pop() || 'page';
                            const pagesInfo = currentPhaseData.pages_completed && currentPhaseData.total_pages 
                                ? `${currentPhaseData.pages_completed}/${currentPhaseData.total_pages}` 
                                : '';
                            
                            detailsText = `📄 Scraping: ${pageName} ${pagesInfo}`;
                            
                            // Show content preview if available
                            if (currentPhaseData.scraped_content_preview) {
                                const preview = currentPhaseData.scraped_content_preview.substring(0, 100);
                                detailsText += `\n📝 Content: ${preview}...`;
                            }
                        }
                    }
                }
                
                if (progressText) {
                    progressText.textContent = statusText;
                }
                
                if (progressDetails) {
                    progressDetails.textContent = detailsText;
                    progressDetails.style.display = detailsText ? 'block' : 'none';
                }

                // Console logging for developer visibility
                if (currentPhaseData && currentPhaseData.current_page) {
                    if (currentPhaseData.scraped_content_preview) {
                    }
                }

                // Continue polling if not complete
                if (progress.status === 'running' || progress.status === 'researching' || progress.status === 'queued') {
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
                // Get the company_id if it exists (for completed status)
                const companyId = resultCard.dataset.companyId || '';
                
                const newControls = this.getResearchControls({
                    company_name: companyName,
                    website: website,
                    research_status: status,
                    is_researched: (status === 'completed'),  // Set to true when research is completed
                    database_id: companyId
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
        // Helper function to safely display array data
        const displayArray = (arr, defaultText = 'Not specified') => {
            if (!arr || !Array.isArray(arr) || arr.length === 0) {
                return `<span style="color: #888; font-style: italic;">${defaultText}</span>`;
            }
            return arr.map(item => this.escapeHtml(item)).join(', ');
        };

        // Helper function to safely display object data
        const displayObject = (obj, defaultText = 'Not specified') => {
            if (!obj || typeof obj !== 'object' || Object.keys(obj).length === 0) {
                return `<span style="color: #888; font-style: italic;">${defaultText}</span>`;
            }
            return Object.entries(obj)
                .map(([key, value]) => `<strong>${this.escapeHtml(key)}:</strong> ${this.escapeHtml(value)}`)
                .join('<br>');
        };

        // Helper function to safely display text
        const displayText = (text, defaultText = 'Not specified') => {
            if (text && text !== 'unknown') {
                return this.escapeHtml(text);
            }
            return `<span style="color: #888; font-style: italic;">${defaultText}</span>`;
        };

        // Helper function to display numbers (like founding year)
        const displayNumber = (num, defaultText = 'Not specified') => {
            if (num && typeof num === 'number' && num > 0) {
                return num.toString();
            }
            return `<span style="color: #888; font-style: italic;">${defaultText}</span>`;
        };

        // Helper function to display boolean values
        const displayBoolean = (bool, trueText = 'Yes', falseText = 'No') => {
            if (typeof bool === 'boolean') {
                return bool ? trueText : falseText;
            }
            return `<span style="color: #888; font-style: italic;">Not specified</span>`;
        };

        // Helper function to display percentages
        const displayPercentage = (value, defaultText = 'Not calculated') => {
            if (value && typeof value === 'number') {
                return `${(value * 100).toFixed(1)}%`;
            }
            return `<span style="color: #888; font-style: italic;">${defaultText}</span>`;
        };

        // Helper function to check if a section has meaningful data
        const hasData = (fields) => {
            return fields.some(field => {
                if (Array.isArray(field)) return field && field.length > 0;
                if (typeof field === 'object') return field && Object.keys(field).length > 0;
                return field && field !== 'unknown' && field !== '';
            });
        };

        const modalContent = `
            <div class="company-details">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 style="margin: 0;">${this.escapeHtml(company.name)}</h3>
                    <button class="btn btn-accent" onclick="window.theodoreUI.showEditCompanyModal('${company.id}')" style="padding: 8px 16px;">
                        <span>✏️</span>
                        Edit Company
                    </button>
                </div>
                
                <!-- Data Availability Notice -->
                ${company.scrape_status === 'failed' || (company.sales_intelligence && company.sales_intelligence.startsWith('No content could be extracted')) ? `
                    <div class="detail-section full-width" style="background: rgba(255, 107, 107, 0.1); border: 1px solid rgba(255, 107, 107, 0.3); border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                        <h4 style="color: #ff6b6b;">⚠️ Limited Data Available</h4>
                        <p style="margin: 8px 0 0 0; color: var(--text-secondary);">
                            This company's data extraction was incomplete. Only basic information is available. 
                            Consider re-researching this company to get complete intelligence.
                        </p>
                    </div>
                ` : ''}
                
                <div class="details-grid">
                    <div class="details-column">
                        <!-- Basic Information -->
                        <div class="detail-section">
                            <h4>🏢 Basic Information</h4>
                            <p><strong>Website:</strong> <a href="${company.website}" target="_blank">${this.escapeHtml(company.website)}</a></p>
                            <p><strong>Industry:</strong> ${displayText(company.industry)}</p>
                            <p><strong>Business Model:</strong> ${displayText(company.business_model)}</p>
                            <p><strong>Company Size:</strong> ${displayText(company.company_size)}</p>
                            <p><strong>Company Stage:</strong> ${displayText(company.company_stage)}</p>
                            <p><strong>Founded:</strong> ${displayNumber(company.founding_year)}</p>
                            <p><strong>Location:</strong> ${displayText(company.location)}</p>
                            <p><strong>Employee Count:</strong> ${displayText(company.employee_count_range)}</p>
                            <p><strong>Geographic Scope:</strong> ${displayText(company.geographic_scope)}</p>
                        </div>

                        <!-- Business Model Classification -->
                        ${this.renderClassificationSection(company)}

                        <!-- Business Intelligence -->
                        <div class="detail-section">
                            <h4>💼 Business Intelligence</h4>
                            <p><strong>Key Services:</strong> ${displayArray(company.key_services)}</p>
                            <p><strong>Products/Services Offered:</strong> ${displayArray(company.products_services_offered)}</p>
                            <p><strong>Pain Points:</strong> ${displayArray(company.pain_points)}</p>
                            <p><strong>Competitive Advantages:</strong> ${displayArray(company.competitive_advantages)}</p>
                            <p><strong>Business Model Type:</strong> ${displayText(company.business_model_type)}</p>
                            <p><strong>Business Model Framework:</strong> ${displayText(company.business_model_framework)}</p>
                            <p><strong>Decision Maker Type:</strong> ${displayText(company.decision_maker_type)}</p>
                            <p><strong>Sales Complexity:</strong> ${displayText(company.sales_complexity)}</p>
                        </div>

                        <!-- Financial & Growth -->
                        <div class="detail-section">
                            <h4>💰 Financial & Growth</h4>
                            <p><strong>Funding Status:</strong> ${displayText(company.funding_status)}</p>
                            <p><strong>Funding Stage (Detailed):</strong> ${displayText(company.funding_stage_detailed)}</p>
                            <p><strong>Has Job Listings:</strong> ${displayBoolean(company.has_job_listings)}</p>
                            <p><strong>Job Openings Count:</strong> ${displayNumber(company.job_listings_count, 'Not specified')}</p>
                        </div>

                        <!-- Contact & Social -->
                        <div class="detail-section">
                            <h4>📞 Contact & Social Media</h4>
                            <div><strong>Contact Information:</strong><br>${displayObject(company.contact_info)}</div>
                            <div><strong>Social Media:</strong><br>${displayObject(company.social_media)}</div>
                        </div>
                    </div>

                    <div class="details-column">
                        <!-- Company Overview -->
                        <div class="detail-section">
                            <h4>📋 Company Overview</h4>
                            <p><strong>Description:</strong> ${displayText(company.company_description)}</p>
                            <p><strong>Value Proposition:</strong> ${displayText(company.value_proposition)}</p>
                            <p><strong>Target Market:</strong> ${displayText(company.target_market)}</p>
                            <p><strong>Company Culture:</strong> ${displayText(company.company_culture)}</p>
                        </div>

                        <!-- Technology & Tools -->
                        <div class="detail-section">
                            <h4>💻 Technology & Tools</h4>
                            <p><strong>Tech Stack:</strong> ${displayArray(company.tech_stack)}</p>
                            <p><strong>Tech Sophistication:</strong> ${displayText(company.tech_sophistication)}</p>
                            <p><strong>Has Chat Widget:</strong> ${displayBoolean(company.has_chat_widget)}</p>
                            <p><strong>Has Forms:</strong> ${displayBoolean(company.has_forms)}</p>
                            <p><strong>Sales/Marketing Tools:</strong> ${displayArray(company.sales_marketing_tools)}</p>
                        </div>

                        <!-- Leadership & Team -->
                        <div class="detail-section">
                            <h4>👥 Leadership & Team</h4>
                            <p><strong>Leadership Team:</strong> ${displayArray(company.leadership_team)}</p>
                            <div><strong>Key Decision Makers:</strong><br>${displayObject(company.key_decision_makers)}</div>
                        </div>

                        <!-- Recognition & Partnerships -->
                        <div class="detail-section">
                            <h4>🏆 Recognition & Partnerships</h4>
                            <p><strong>Awards:</strong> ${displayArray(company.awards)}</p>
                            <p><strong>Certifications:</strong> ${displayArray(company.certifications)}</p>
                            <p><strong>Partnerships:</strong> ${displayArray(company.partnerships)}</p>
                        </div>

                        <!-- Recent Activity -->
                        <div class="detail-section">
                            <h4>📈 Recent Activity</h4>
                            <p><strong>Recent News:</strong> ${displayArray(company.recent_news)}</p>
                            <div><strong>Recent News/Events:</strong><br>
                                ${company.recent_news_events && company.recent_news_events.length > 0 ? 
                                    company.recent_news_events.map(event => 
                                        `<p>• ${this.escapeHtml(event.date || 'Date unknown')}: ${this.escapeHtml(event.description || event.title || 'No description')}</p>`
                                    ).join('') : 'No recent news available'
                                }
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Job Listings Details -->
                ${company.job_listings_details && company.job_listings_details.length > 0 ? `
                    <div class="detail-section">
                        <h4>💼 Current Job Openings</h4>
                        ${company.job_listings_details.map(job => `
                            <div style="margin-bottom: 12px; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                                <strong>${this.escapeHtml(job.title || 'Job Title')}</strong><br>
                                <small>Department: ${this.escapeHtml(job.department || 'Not specified')} | Location: ${this.escapeHtml(job.location || 'Not specified')}</small>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}

                <!-- Crawling Information -->
                <div class="detail-section">
                    <h4>🕷️ Data Collection</h4>
                    <p><strong>Pages Crawled:</strong> ${displayNumber(company.scraped_urls_count || (company.pages_crawled ? company.pages_crawled.length : 0), '0')}</p>
                    <p><strong>Crawl Depth:</strong> ${displayNumber(company.crawl_depth)}</p>
                    <p><strong>Crawl Duration:</strong> ${company.crawl_duration ? `${company.crawl_duration.toFixed(2)}s` : `<span style="color: #888; font-style: italic;">Not specified</span>`}</p>
                    <p><strong>Scrape Status:</strong> ${displayText(company.scrape_status)}</p>
                    ${company.scrape_error ? `<p><strong>Scrape Error:</strong> <span style="color: #ff6b6b;">${this.escapeHtml(company.scrape_error)}</span></p>` : ''}
                </div>

                <!-- Confidence Scores -->
                <div class="detail-section">
                    <h4>📊 Confidence Scores</h4>
                    <p><strong>Stage Confidence:</strong> ${displayPercentage(company.stage_confidence)}</p>
                    <p><strong>Tech Confidence:</strong> ${displayPercentage(company.tech_confidence)}</p>
                    <p><strong>Industry Confidence:</strong> ${displayPercentage(company.industry_confidence)}</p>
                </div>

                <!-- AI Analysis -->
                ${company.ai_summary || company.sales_intelligence ? `
                    <div class="detail-section">
                        <h4>🤖 AI Analysis</h4>
                        ${company.sales_intelligence ? `
                            <div style="margin-bottom: 16px;">
                                <strong>Sales Intelligence:</strong>
                                <div class="sales-intelligence-content" style="margin-top: 8px; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 6px; line-height: 1.6;">
                                    ${this.escapeHtml(company.sales_intelligence).replace(/\n/g, '<br>')}
                                </div>
                            </div>
                        ` : ''}
                        ${company.ai_summary ? `
                            <div>
                                <strong>AI Summary:</strong>
                                <div style="margin-top: 8px; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 6px; line-height: 1.6;">
                                    ${this.escapeHtml(company.ai_summary).replace(/\n/g, '<br>')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                ` : ''}

                <!-- Metadata -->
                <div class="detail-section">
                    <h4>ℹ️ Metadata</h4>
                    <p><strong>ID:</strong> <code style="font-family: monospace; background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 3px;">${this.escapeHtml(company.id)}</code></p>
                    <p><strong>Created:</strong> ${company.created_at ? new Date(company.created_at).toLocaleString() : `<span style="color: #888; font-style: italic;">Not specified</span>`}</p>
                    <p><strong>Last Updated:</strong> ${company.last_updated ? new Date(company.last_updated).toLocaleString() : `<span style="color: #888; font-style: italic;">Not specified</span>`}</p>
                </div>
                
                <!-- Scraping Details Section -->
                ${company.scraped_urls_count > 0 || company.llm_interactions_count > 0 ? `
                    <div class="detail-section full-width" style="border: 2px solid rgba(102, 126, 234, 0.3); border-radius: 12px; padding: 20px; background: rgba(102, 126, 234, 0.05);">
                        <h4 style="color: var(--primary-color); margin-bottom: 16px;">🔍 Scraping & AI Details</h4>
                        
                        ${company.scraped_urls_count > 0 || company.total_input_tokens || company.total_output_tokens ? `
                            <div class="scraping-stats" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin-bottom: 16px;">
                                ${company.scraped_urls_count > 0 ? `
                                    <div class="stat-item" style="text-align: center; padding: 12px; background: var(--bg-tertiary); border-radius: 8px;">
                                        <div style="font-size: 1.5rem; font-weight: bold; color: var(--primary-color);">${company.scraped_urls_count}</div>
                                        <div style="font-size: 0.875rem; color: var(--text-secondary);">URLs Scraped</div>
                                    </div>
                                ` : ''}
                                ${company.llm_interactions_count ? `
                                    <div class="stat-item" style="text-align: center; padding: 12px; background: var(--bg-tertiary); border-radius: 8px;">
                                        <div style="font-size: 1.5rem; font-weight: bold; color: var(--accent-color);">${company.llm_interactions_count}</div>
                                        <div style="font-size: 0.875rem; color: var(--text-secondary);">LLM Calls</div>
                                    </div>
                                ` : ''}
                                ${(company.total_input_tokens || company.total_output_tokens) ? `
                                    <div class="stat-item" style="text-align: center; padding: 12px; background: var(--bg-tertiary); border-radius: 8px;">
                                        <div style="font-size: 1.5rem; font-weight: bold; color: #6f42c1;">${((company.total_input_tokens || 0) + (company.total_output_tokens || 0)).toLocaleString()}</div>
                                        <div style="font-size: 0.875rem; color: var(--text-secondary);">Total Tokens</div>
                                    </div>
                                ` : ''}
                                ${company.total_cost_usd ? `
                                    <div class="stat-item" style="text-align: center; padding: 12px; background: var(--bg-tertiary); border-radius: 8px;">
                                        <div style="font-size: 1.5rem; font-weight: bold; color: #e83e8c;">$${(company.total_cost_usd || 0).toFixed(4)}</div>
                                        <div style="font-size: 0.875rem; color: var(--text-secondary);">Total Cost</div>
                                    </div>
                                ` : ''}
                            </div>
                        ` : ''}
                        
                        <div class="scraping-actions" style="text-align: center;">
                            <button class="btn btn-secondary" style="background: var(--primary-gradient); color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;" onclick="window.theodoreUI.viewScrapingDetails('${company.id}')">
                                <span>📋</span>
                                View Detailed Scraping Log
                            </button>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        const modal = this.createModal('Company Details', modalContent);
        document.body.appendChild(modal);
    }

    async showEditCompanyModal(companyId) {
        try {
            // First fetch the current company data
            const response = await fetch(`/api/company/${companyId}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            if (!data.success) {
                this.showError('Failed to load company data for editing');
                return;
            }
            
            const company = data.company;
            this.showEditForm(company);
            
        } catch (error) {
            console.error('Error loading company for edit:', error);
            this.showError('Failed to load company data for editing');
        }
    }

    showEditForm(company) {
        const editFormContent = `
            <div class="edit-company-form">
                <form id="editCompanyForm" style="max-height: 70vh; overflow-y: auto;">
                    <div class="edit-form-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        
                        <!-- Left Column -->
                        <div class="edit-form-column">
                            <h4>🏢 Basic Information</h4>
                            
                            <div class="form-group">
                                <label for="edit_name">Company Name *</label>
                                <input type="text" id="edit_name" name="name" value="${this.escapeHtml(company.name || '')}" required class="form-input">
                            </div>
                            
                            <div class="form-group">
                                <label for="edit_website">Website *</label>
                                <input type="url" id="edit_website" name="website" value="${this.escapeHtml(company.website || '')}" required class="form-input">
                            </div>
                            
                            <div class="form-group">
                                <label for="edit_industry">Industry</label>
                                <input type="text" id="edit_industry" name="industry" value="${this.escapeHtml(company.industry || '')}" class="form-input">
                            </div>
                            
                            <div class="form-group">
                                <label for="edit_business_model">Business Model</label>
                                <select id="edit_business_model" name="business_model" class="form-select">
                                    <option value="">Select Business Model</option>
                                    <option value="B2B" ${company.business_model === 'B2B' ? 'selected' : ''}>B2B</option>
                                    <option value="B2C" ${company.business_model === 'B2C' ? 'selected' : ''}>B2C</option>
                                    <option value="B2B2C" ${company.business_model === 'B2B2C' ? 'selected' : ''}>B2B2C</option>
                                    <option value="Marketplace" ${company.business_model === 'Marketplace' ? 'selected' : ''}>Marketplace</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="edit_company_size">Company Size</label>
                                <select id="edit_company_size" name="company_size" class="form-select">
                                    <option value="">Select Company Size</option>
                                    <option value="startup" ${company.company_size === 'startup' ? 'selected' : ''}>Startup (1-10)</option>
                                    <option value="small" ${company.company_size === 'small' ? 'selected' : ''}>Small (11-50)</option>
                                    <option value="medium" ${company.company_size === 'medium' ? 'selected' : ''}>Medium (51-200)</option>
                                    <option value="large" ${company.company_size === 'large' ? 'selected' : ''}>Large (201-1000)</option>
                                    <option value="enterprise" ${company.company_size === 'enterprise' ? 'selected' : ''}>Enterprise (1000+)</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="edit_founding_year">Founded Year</label>
                                <input type="number" id="edit_founding_year" name="founding_year" value="${company.founding_year || ''}" min="1800" max="${new Date().getFullYear()}" class="form-input">
                            </div>
                            
                            <div class="form-group">
                                <label for="edit_location">Location</label>
                                <input type="text" id="edit_location" name="location" value="${this.escapeHtml(company.location || '')}" class="form-input" placeholder="City, State/Country">
                            </div>
                            
                            <div class="form-group">
                                <label for="edit_employee_count_range">Employee Count Range</label>
                                <input type="text" id="edit_employee_count_range" name="employee_count_range" value="${this.escapeHtml(company.employee_count_range || '')}" class="form-input" placeholder="e.g., 11-50">
                            </div>
                        </div>
                        
                        <!-- Right Column -->
                        <div class="edit-form-column">
                            <h4>💼 Business Details</h4>
                            
                            <div class="form-group">
                                <label for="edit_company_description">Company Description</label>
                                <textarea id="edit_company_description" name="company_description" class="form-input" rows="3" placeholder="Brief description of the company">${this.escapeHtml(company.company_description || '')}</textarea>
                            </div>
                            
                            <div class="form-group">
                                <label for="edit_value_proposition">Value Proposition</label>
                                <textarea id="edit_value_proposition" name="value_proposition" class="form-input" rows="3" placeholder="What value does the company provide?">${this.escapeHtml(company.value_proposition || '')}</textarea>
                            </div>
                            
                            <div class="form-group">
                                <label for="edit_target_market">Target Market</label>
                                <input type="text" id="edit_target_market" name="target_market" value="${this.escapeHtml(company.target_market || '')}" class="form-input" placeholder="e.g., SMBs, Enterprise, Consumers">
                            </div>
                            
                            <div class="form-group">
                                <label for="edit_key_services">Key Services (comma-separated)</label>
                                <input type="text" id="edit_key_services" name="key_services" value="${Array.isArray(company.key_services) ? company.key_services.join(', ') : (company.key_services || '')}" class="form-input" placeholder="Service 1, Service 2, Service 3">
                            </div>
                            
                            <div class="form-group">
                                <label for="edit_tech_stack">Tech Stack (comma-separated)</label>
                                <input type="text" id="edit_tech_stack" name="tech_stack" value="${Array.isArray(company.tech_stack) ? company.tech_stack.join(', ') : (company.tech_stack || '')}" class="form-input" placeholder="React, Node.js, AWS">
                            </div>
                            
                            <div class="form-group">
                                <label for="edit_funding_status">Funding Status</label>
                                <select id="edit_funding_status" name="funding_status" class="form-select">
                                    <option value="">Select Funding Status</option>
                                    <option value="bootstrapped" ${company.funding_status === 'bootstrapped' ? 'selected' : ''}>Bootstrapped</option>
                                    <option value="pre-seed" ${company.funding_status === 'pre-seed' ? 'selected' : ''}>Pre-Seed</option>
                                    <option value="seed" ${company.funding_status === 'seed' ? 'selected' : ''}>Seed</option>
                                    <option value="series-a" ${company.funding_status === 'series-a' ? 'selected' : ''}>Series A</option>
                                    <option value="series-b" ${company.funding_status === 'series-b' ? 'selected' : ''}>Series B</option>
                                    <option value="series-c" ${company.funding_status === 'series-c' ? 'selected' : ''}>Series C+</option>
                                    <option value="public" ${company.funding_status === 'public' ? 'selected' : ''}>Public</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="edit_geographic_scope">Geographic Scope</label>
                                <select id="edit_geographic_scope" name="geographic_scope" class="form-select">
                                    <option value="">Select Geographic Scope</option>
                                    <option value="local" ${company.geographic_scope === 'local' ? 'selected' : ''}>Local</option>
                                    <option value="regional" ${company.geographic_scope === 'regional' ? 'selected' : ''}>Regional</option>
                                    <option value="national" ${company.geographic_scope === 'national' ? 'selected' : ''}>National</option>
                                    <option value="international" ${company.geographic_scope === 'international' ? 'selected' : ''}>International</option>
                                    <option value="global" ${company.geographic_scope === 'global' ? 'selected' : ''}>Global</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-actions" style="margin-top: 24px; text-align: center; border-top: 1px solid var(--border-subtle); padding-top: 20px;">
                        <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()" style="margin-right: 12px;">
                            Cancel
                        </button>
                        <button type="submit" class="btn btn-primary">
                            <span>💾</span>
                            Update Company
                        </button>
                    </div>
                </form>
            </div>
        `;
        
        const modal = this.createModal('Edit Company', editFormContent);
        
        // Add form submit handler
        const form = modal.querySelector('#editCompanyForm');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleUpdateCompany(company.id, form, modal);
        });
        
        document.body.appendChild(modal);
    }

    async handleUpdateCompany(companyId, form, modal) {
        try {
            const formData = new FormData(form);
            const updateData = {};
            
            // Process form data
            for (const [key, value] of formData.entries()) {
                if (value.trim() !== '') {
                    // Handle comma-separated arrays
                    if (['key_services', 'tech_stack'].includes(key)) {
                        updateData[key] = value.split(',').map(item => item.trim()).filter(item => item.length > 0);
                    }
                    // Handle numbers
                    else if (key === 'founding_year') {
                        const year = parseInt(value);
                        if (!isNaN(year)) {
                            updateData[key] = year;
                        }
                    }
                    // Handle regular fields
                    else {
                        updateData[key] = value;
                    }
                }
            }
            
            // Show loading state
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span>⏳</span> Updating...';
            submitBtn.disabled = true;
            
            // Send update request
            const response = await fetch(`/api/company/${companyId}/update`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updateData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('Company updated successfully!');
                modal.remove();
                
                // Refresh any displayed data
                if (window.location.hash === '#database') {
                    this.loadDatabaseBrowser();
                }
            } else {
                throw new Error(result.error || 'Update failed');
            }
            
        } catch (error) {
            console.error('Error updating company:', error);
            this.showError(`Failed to update company: ${error.message}`);
            
            // Reset button state
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }
    
    async viewScrapingDetails(companyId) {
        try {
            const response = await fetch(`/api/company/${companyId}/scraping-details`);
            const data = await response.json();
            
            if (!data.success) {
                this.showError('Failed to load scraping details');
                return;
            }
            
            const details = data.scraping_details;
            
            const modalContent = `
                <div class="scraping-details">
                    <h3>🔍 Scraping Details for ${this.escapeHtml(data.company_name)}</h3>
                    
                    <!-- Scraping Overview -->
                    <div class="detail-section">
                        <h4>📊 Scraping Overview</h4>
                        <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-bottom: 16px;">
                            <div class="stat-card" style="text-align: center; padding: 16px; background: var(--bg-tertiary); border-radius: 8px;">
                                <div class="stat-number" style="font-size: 1.8rem; font-weight: bold; color: var(--primary-color);">${details.scraped_urls_count}</div>
                                <div class="stat-label" style="font-size: 0.875rem; color: var(--text-secondary);">URLs Scraped</div>
                            </div>
                            <div class="stat-card" style="text-align: center; padding: 16px; background: var(--bg-tertiary); border-radius: 8px;">
                                <div class="stat-number" style="font-size: 1.8rem; font-weight: bold; color: var(--accent-color);">${details.llm_interactions_count}</div>
                                <div class="stat-label" style="font-size: 0.875rem; color: var(--text-secondary);">LLM Calls</div>
                            </div>
                            <div class="stat-card" style="text-align: center; padding: 16px; background: var(--bg-tertiary); border-radius: 8px;">
                                <div class="stat-number" style="font-size: 1.8rem; font-weight: bold; color: #28a745;">${Math.round(details.crawl_duration)}s</div>
                                <div class="stat-label" style="font-size: 0.875rem; color: var(--text-secondary);">Duration</div>
                            </div>
                            ${details.total_input_tokens || details.total_output_tokens ? `
                                <div class="stat-card" style="text-align: center; padding: 16px; background: var(--bg-tertiary); border-radius: 8px;">
                                    <div class="stat-number" style="font-size: 1.8rem; font-weight: bold; color: #6f42c1;">${((details.total_input_tokens || 0) + (details.total_output_tokens || 0)).toLocaleString()}</div>
                                    <div class="stat-label" style="font-size: 0.875rem; color: var(--text-secondary);">Total Tokens</div>
                                </div>
                                <div class="stat-card" style="text-align: center; padding: 16px; background: var(--bg-tertiary); border-radius: 8px;">
                                    <div class="stat-number" style="font-size: 1.8rem; font-weight: bold; color: #e83e8c;">$${(details.total_cost_usd || 0).toFixed(4)}</div>
                                    <div class="stat-label" style="font-size: 0.875rem; color: var(--text-secondary);">Total Cost</div>
                                </div>
                            ` : ''}
                        </div>
                        <p><strong>Status:</strong> <span style="color: ${details.scrape_status === 'success' ? '#28a745' : '#dc3545'};">${details.scrape_status}</span></p>
                    </div>
                    
                    <!-- Scraped URLs -->
                    ${details.scraped_urls && details.scraped_urls.length > 0 ? `
                        <div class="detail-section">
                            <h4>🌐 Scraped URLs (${details.scraped_urls.length})</h4>
                            <div class="urls-list" style="max-height: 300px; overflow-y: auto; background: var(--bg-tertiary); border-radius: 8px; padding: 16px;">
                                ${details.scraped_urls.map((url, index) => `
                                    <div class="url-item" style="padding: 8px 0; border-bottom: 1px solid var(--border-subtle); display: flex; align-items: center; gap: 12px;">
                                        <span style="background: var(--primary-color); color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: bold;">${index + 1}</span>
                                        <a href="${this.escapeHtml(url)}" target="_blank" style="color: var(--primary-color); text-decoration: none; flex: 1; word-break: break-all;" onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">
                                            ${this.escapeHtml(url)}
                                        </a>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    <!-- Note about vector content -->
                    <div class="detail-section">
                        <h4>📝 Additional Data</h4>
                        <div style="background: rgba(255, 193, 7, 0.1); border: 1px solid rgba(255, 193, 7, 0.3); border-radius: 8px; padding: 16px;">
                            <p style="margin: 0; color: var(--text-secondary);">
                                <strong>Note:</strong> Detailed LLM prompts, responses, and scraped content are stored in the vector embedding 
                                for this company. This data is used for similarity analysis and can be accessed through the vector database.
                            </p>
                        </div>
                    </div>
                </div>
            `;
            
            const modal = this.createModal('Scraping Details', modalContent);
            document.body.appendChild(modal);
            
        } catch (error) {
            console.error('Error fetching scraping details:', error);
            this.showError('Failed to load scraping details');
        }
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
                    <button class="btn btn-primary" onclick="window.theodoreUI.startResearch('${this.escapeJs(companyName)}', '${this.escapeJs(website)}'); this.closest('.modal-overlay').remove();">
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
    
    storeResearchData(companyName, researchData) {
        // Store research data for later access by viewResearchDetails
        this.researchDataCache.set(companyName.toLowerCase(), researchData);
    }
    
    viewResearchDetails(companyName) {
        // Get stored research data
        const researchData = this.researchDataCache.get(companyName.toLowerCase());
        
        if (!researchData) {
            console.error(`❌ No cached research data found for ${companyName}`);
            this.showError(`No research data available for ${companyName}. Please re-research the company.`);
            return;
        }
        
        // Convert research data to company format expected by showCompanyDetailsModal
        const companyData = {
            // Required fields for modal
            id: researchData.company_id || `research_${Date.now()}`,
            name: researchData.name || researchData.company_name || companyName,
            website: researchData.website || '',
            company_description: researchData.company_description || 'No description available',
            
            // Required fields that may be empty
            industry: 'Unknown',
            business_model: 'Unknown', 
            company_size: 'Unknown',
            company_stage: 'Unknown',
            founding_year: null,
            location: 'Unknown',
            
            // Research-specific fields
            sales_intelligence: researchData.company_description || 'No sales intelligence available',
            ai_summary: '',
            scrape_status: 'completed',
            scrape_error: '',
            
            // Timestamps  
            created_at: researchData.research_timestamp || new Date().toISOString(),
            last_updated: researchData.research_timestamp || new Date().toISOString(),
            research_timestamp: researchData.research_timestamp || new Date().toISOString(),
            
            // Research metadata
            discovery_method: researchData.discovery_method || 'AI Research',
            processing_time: researchData.processing_time || 0,
            pages_processed: researchData.pages_processed || 0,
            token_usage: researchData.token_usage || {},
            
            // Mark as researched data
            is_researched: true,
            research_status: 'completed'
        };
        
        // Use the same modal as "Add Company" view details
        this.showCompanyDetailsModal(companyData);
    }

    // Keep the extractResearchField helper for potential future use
    extractResearchField_unused(researchElement, fieldName) {
        // Look for a research section with the given field name
        const resultCard = document.querySelector(`[data-company-name="${this.escapeHtml(companyName)}"]`);
        
        if (!resultCard) {
            console.error(`❌ Cannot find result card for ${companyName}`);
            this.showError(`Cannot find research data for ${companyName}`);
            return;
        }
        
        // Extract research data from the card (look for .research-data sections)
        const researchData = resultCard.querySelector('.research-data');
        
        if (!researchData) {
            console.error(`❌ No research data element found for ${companyName}`);
            this.showError(`No research data available for ${companyName}`);
            return;
        }
        
        // Build modal content from the research data
        const industry = this.extractResearchField(researchData, 'Industry') || 'Unknown';
        const businessModel = this.extractResearchField(researchData, 'Business Model') || 'Unknown';
        const description = this.extractResearchField(researchData, 'Description') || 'No description available';
        const targetMarket = this.extractResearchField(researchData, 'Target Market') || 'Unknown';
        const keyServices = this.extractResearchField(researchData, 'Key Services') || 'None listed';
        const location = this.extractResearchField(researchData, 'Location') || 'Unknown';
        const companySize = this.extractResearchField(researchData, 'Company Size') || 'Unknown';
        const techStack = this.extractResearchField(researchData, 'Tech Stack') || 'Not available';
        const valueProposition = this.extractResearchField(researchData, 'Value Proposition') || 'Not available';
        const painPoints = this.extractResearchField(researchData, 'Pain Points') || 'Not available';
        const researchInfo = this.extractResearchField(researchData, 'Research Info') || 'Research metadata unavailable';
        const jobListings = this.extractResearchField(researchData, 'Job Listings') || 'Not available';
        
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
                    <div class="detail-item">
                        <strong>Company Size:</strong> ${this.escapeHtml(companySize)}
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
                    ${valueProposition !== 'Not available' ? `
                        <div class="detail-item">
                            <strong>Value Proposition:</strong> ${this.escapeHtml(valueProposition)}
                        </div>
                    ` : ''}
                    ${painPoints !== 'Not available' ? `
                        <div class="detail-item">
                            <strong>Pain Points:</strong> ${this.escapeHtml(painPoints)}
                        </div>
                    ` : ''}
                    ${jobListings !== 'Not available' ? `
                        <div class="detail-item job-listings-modal-section">
                            <strong>Job Listings:</strong> ${this.escapeHtml(jobListings)}
                            ${this.extractJobListingsDetailsFromHTML(researchData)}
                        </div>
                    ` : ''}
                </div>
                
                ${techStack !== 'Not available' ? `
                    <div class="detail-section">
                        <h4>Technology Information</h4>
                        <div class="detail-item">
                            <strong>Tech Stack:</strong> ${this.escapeHtml(techStack)}
                        </div>
                    </div>
                ` : ''}
                
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
        }, 100);
        
        document.body.appendChild(modal);
    }
    
    extractResearchField(researchElement, fieldName) {
        // Look for a research section with the given field name
        const sections = researchElement.querySelectorAll('.research-section');
        
        for (const section of sections) {
            const strongElement = section.querySelector('strong');
            if (strongElement) {
                if (strongElement.textContent.includes(fieldName)) {
                    // Extract text after the strong element
                    const text = section.textContent.replace(strongElement.textContent, '').trim();
                    return text;
                }
            }
        }
        return null;
    }
    
    async saveToDatabase(companyName, website) {
        
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

    async loadDatabaseBrowser(searchParams = {}) {
        const tableContainer = document.getElementById('companiesTable');
        const totalElement = document.getElementById('totalCompanies');
        const showingElement = document.getElementById('showingCompanies');
        const currentPageElement = document.getElementById('currentPage');
        const paginationControls = document.getElementById('paginationControls');
        
        // Default parameters
        const params = {
            page: 1,
            page_size: 25,
            search: '',
            industry: '',
            business_model: '',
            company_size: '',
            ...searchParams
        };
        
        // Store current search state
        this.databaseSearchState = params;
        
        // Show loading state
        tableContainer.innerHTML = '<div class="loading">Loading companies...</div>';
        if (totalElement) totalElement.textContent = 'Loading...';
        if (showingElement) showingElement.textContent = '0 of 0';
        if (currentPageElement) currentPageElement.textContent = params.page;
        if (paginationControls) paginationControls.style.display = 'none';
        
        try {
            // Build query string
            const queryParams = new URLSearchParams();
            Object.keys(params).forEach(key => {
                if (params[key]) queryParams.append(key, params[key]);
            });
            
            const response = await fetch(`/api/companies?${queryParams.toString()}`);
            const data = await response.json();

            if (response.ok && data.success) {
                this.updateDatabaseStats(data);
                this.updateCompaniesTable(data.companies);
                this.updatePaginationControls(data);
                this.populateFilterOptions(data.filters || {});
            } else {
                this.showDatabaseError(data.error || 'Failed to load database');
            }
        } catch (error) {
            console.error('Database browser error:', error);
            this.showDatabaseError('Network error loading database');
        }
    }
    
    initializeDatabaseSearch() {
        // Search input - trigger on Enter key only
        const searchInput = document.getElementById('databaseSearch');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault(); // Prevent form submission
                    this.performDatabaseSearch();
                }
            });
        }
        
        // Filter dropdowns
        const industryFilter = document.getElementById('industryFilter');
        const businessModelFilter = document.getElementById('businessModelFilter');
        const companySizeFilter = document.getElementById('companySizeFilter');
        
        if (industryFilter) {
            industryFilter.addEventListener('change', () => this.performDatabaseSearch());
        }
        if (businessModelFilter) {
            businessModelFilter.addEventListener('change', () => this.performDatabaseSearch());
        }
        if (companySizeFilter) {
            companySizeFilter.addEventListener('change', () => this.performDatabaseSearch());
        }
        
        // Page size selector
        const pageSizeSelect = document.getElementById('pageSize');
        if (pageSizeSelect) {
            pageSizeSelect.addEventListener('change', () => this.changePageSize());
        }
    }
    
    performDatabaseSearch() {
        const searchInput = document.getElementById('databaseSearch');
        const industryFilter = document.getElementById('industryFilter');
        const businessModelFilter = document.getElementById('businessModelFilter');
        const companySizeFilter = document.getElementById('companySizeFilter');
        
        const searchParams = {
            page: 1, // Reset to first page on new search
            search: searchInput ? searchInput.value.trim() : '',
            industry: industryFilter ? industryFilter.value : '',
            business_model: businessModelFilter ? businessModelFilter.value : '',
            company_size: companySizeFilter ? companySizeFilter.value : '',
            page_size: this.databaseSearchState?.page_size || 25
        };
        
        this.loadDatabaseBrowser(searchParams);
    }

    updateDatabaseStats(data) {
        const totalElement = document.getElementById('totalCompanies');
        const showingElement = document.getElementById('showingCompanies');
        const currentPageElement = document.getElementById('currentPage');
        
        if (totalElement) {
            totalElement.textContent = data.total || 0;
        }
        if (showingElement) {
            showingElement.textContent = `${data.showing_start || 0}-${data.showing_end || 0} of ${data.total || 0}`;
        }
        if (currentPageElement) {
            currentPageElement.textContent = data.page || 1;
        }
    }
    
    updatePaginationControls(data) {
        const paginationControls = document.getElementById('paginationControls');
        const paginationInfo = document.getElementById('paginationInfo');
        const paginationPages = document.getElementById('paginationPages');
        const firstPageBtn = document.getElementById('firstPageBtn');
        const prevPageBtn = document.getElementById('prevPageBtn');
        const nextPageBtn = document.getElementById('nextPageBtn');
        const lastPageBtn = document.getElementById('lastPageBtn');
        
        if (!paginationControls) return;
        
        // Show/hide pagination controls
        if (data.total_pages <= 1) {
            paginationControls.style.display = 'none';
            return;
        }
        
        paginationControls.style.display = 'block';
        
        // Update pagination info
        if (paginationInfo) {
            paginationInfo.textContent = `Showing ${data.showing_start || 0}-${data.showing_end || 0} of ${data.total || 0} companies`;
        }
        
        // Update page buttons
        const currentPage = data.page || 1;
        const totalPages = data.total_pages || 1;
        
        if (firstPageBtn) firstPageBtn.disabled = currentPage === 1;
        if (prevPageBtn) prevPageBtn.disabled = currentPage === 1;
        if (nextPageBtn) nextPageBtn.disabled = currentPage === totalPages;
        if (lastPageBtn) lastPageBtn.disabled = currentPage === totalPages;
        
        // Generate page number buttons
        if (paginationPages) {
            const pageButtons = [];
            let startPage = Math.max(1, currentPage - 2);
            let endPage = Math.min(totalPages, currentPage + 2);
            
            // Adjust range if we're near the beginning or end
            if (endPage - startPage < 4) {
                if (startPage === 1) {
                    endPage = Math.min(totalPages, startPage + 4);
                } else if (endPage === totalPages) {
                    startPage = Math.max(1, endPage - 4);
                }
            }
            
            for (let i = startPage; i <= endPage; i++) {
                pageButtons.push(`
                    <button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">
                        ${i}
                    </button>
                `);
            }
            
            paginationPages.innerHTML = pageButtons.join('');
        }
    }
    
    populateFilterOptions(filters) {
        const industryFilter = document.getElementById('industryFilter');
        
        if (industryFilter && filters.industries) {
            // Clear existing options except the first one
            industryFilter.innerHTML = '<option value="">All Industries</option>';
            
            // Add industry options
            filters.industries.forEach(industry => {
                if (industry) {
                    const option = document.createElement('option');
                    option.value = industry;
                    option.textContent = industry;
                    if (filters.current_industry === industry) {
                        option.selected = true;
                    }
                    industryFilter.appendChild(option);
                }
            });
        }
        
        // Set current filter values
        const searchInput = document.getElementById('databaseSearch');
        const businessModelFilter = document.getElementById('businessModelFilter');
        const companySizeFilter = document.getElementById('companySizeFilter');
        
        if (searchInput) searchInput.value = filters.current_search || '';
        if (businessModelFilter) businessModelFilter.value = filters.current_business_model || '';
        if (companySizeFilter) companySizeFilter.value = filters.current_company_size || '';
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
                        <th>Classification</th>
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
                                <div class="classification-info">
                                    ${this.createTableClassificationBadge(company)}
                                </div>
                            </td>
                            <td>
                                <div class="sales-intelligence-preview">
                                    ${company.has_sales_intelligence ? 
                                        '<span class="intelligence-indicator">✅ Available</span>' : 
                                        '<span class="intelligence-indicator">❌ Not Available</span>'
                                    }
                                </div>
                            </td>
                            <td>
                                <div class="update-time">${company.last_updated ? new Date(company.last_updated).toLocaleDateString() : 'Unknown'}</div>
                            </td>
                            <td>
                                <div class="actions-dropdown">
                                    <button class="dropdown-trigger" onclick="window.theodoreUI.toggleDropdown(this, '${this.escapeHtml(company.id)}', '${this.escapeJs(company.name)}', '${this.escapeJs(company.website || '')}')">
                                        ⋯
                                    </button>
                                </div>
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
        await this.loadDatabaseBrowser();
        this.showSuccess('Database refreshed');
    }

    async addSampleCompanies() {
        
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
                    data.results.forEach(result => {
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

    toggleDropdown(triggerElement, companyId, companyName, website) {
        // Close any existing dropdowns
        this.closeAllDropdowns();
        
        // Create dropdown menu
        const dropdown = document.createElement('div');
        dropdown.className = 'dropdown-menu';
        dropdown.innerHTML = `
            <button class="dropdown-item" onclick="window.theodoreUI.viewCompanyDetails('${this.escapeJs(companyId)}', '${this.escapeJs(companyName)}'); window.theodoreUI.closeAllDropdowns();">
                <span class="dropdown-icon">👁️</span>
                <span class="dropdown-text">View Details</span>
            </button>
            <button class="dropdown-item" onclick="testSimilarity('${this.escapeJs(companyName)}'); window.theodoreUI.closeAllDropdowns();">
                <span class="dropdown-icon">🔍</span>
                <span class="dropdown-text">Test Similarity</span>
            </button>
            ${website ? `
                <button class="dropdown-item" onclick="window.open('${this.escapeJs(website)}', '_blank'); window.theodoreUI.closeAllDropdowns();">
                    <span class="dropdown-icon">🌐</span>
                    <span class="dropdown-text">Visit Website</span>
                </button>
            ` : ''}
        `;
        
        // Position dropdown relative to trigger - positioned to connect with trigger
        const triggerRect = triggerElement.getBoundingClientRect();
        dropdown.style.position = 'fixed';
        dropdown.style.top = (triggerRect.bottom - 2) + 'px'; // Overlap slightly to create connection
        dropdown.style.right = (window.innerWidth - triggerRect.right) + 'px';
        dropdown.style.zIndex = '1000';
        
        // Add dropdown to body
        document.body.appendChild(dropdown);
        
        // Add click outside to close
        setTimeout(() => {
            document.addEventListener('click', this.handleDropdownClickOutside.bind(this), { once: true });
        }, 0);
        
        // Add ESC key to close
        document.addEventListener('keydown', this.handleDropdownEscape.bind(this), { once: true });
        
        // Mark this dropdown as active
        triggerElement.classList.add('dropdown-active');
        dropdown.setAttribute('data-trigger-id', companyId);
    }
    
    closeAllDropdowns() {
        // Remove all dropdown menus
        document.querySelectorAll('.dropdown-menu').forEach(menu => menu.remove());
        
        // Remove active state from all triggers
        document.querySelectorAll('.dropdown-trigger.dropdown-active').forEach(trigger => {
            trigger.classList.remove('dropdown-active');
        });
    }
    
    handleDropdownClickOutside(event) {
        // Don't close if clicking on a dropdown trigger or menu item
        if (event.target.closest('.dropdown-trigger') || event.target.closest('.dropdown-menu')) {
            return;
        }
        this.closeAllDropdowns();
    }
    
    handleDropdownEscape(event) {
        if (event.key === 'Escape') {
            this.closeAllDropdowns();
        }
    }

    // Batch Processing Methods
    initializeBatchProcessing() {
        
        // Set up form submission handler
        const batchForm = document.getElementById('batchProcessForm');
        if (batchForm) {
            batchForm.addEventListener('submit', this.handleBatchProcessing.bind(this));
        }
        
        // Load Google Sheet URL from settings if available
        this.loadGoogleSheetUrl();
    }

    async loadGoogleSheetUrl() {
        try {
            const response = await fetch('/api/settings');
            if (response.ok) {
                const data = await response.json();
                const googleSheetUrlInput = document.getElementById('googleSheetUrl');
                if (googleSheetUrlInput && data.google_sheets && data.google_sheets.sheet_url) {
                    googleSheetUrlInput.value = data.google_sheets.sheet_url;
                }
            }
        } catch (error) {
        }
    }

    async handleBatchProcessing(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const googleSheetUrl = formData.get('google_sheet_url');
        const batchSize = parseInt(formData.get('batch_size'));
        const startRow = parseInt(formData.get('start_row'));
        
        if (!googleSheetUrl) {
            this.showError('Please enter a Google Sheet URL');
            return;
        }
        
        // Extract sheet ID from URL
        const sheetIdMatch = googleSheetUrl.match(/\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/);
        if (!sheetIdMatch) {
            this.showError('Invalid Google Sheet URL format');
            return;
        }
        
        const sheetId = sheetIdMatch[1];
        
        // Show processing status
        this.showBatchStatus('Starting batch processing...', 0, batchSize);
        
        try {
            // Start batch processing
            const response = await fetch('/api/batch/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sheet_id: sheetId,
                    batch_size: batchSize,
                    start_row: startRow
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // Start polling for progress
                    this.pollBatchProgress(data.job_id, batchSize);
                } else {
                    this.showBatchError(data.error || 'Failed to start batch processing');
                }
            } else {
                this.showBatchError('Server error starting batch processing');
            }
        } catch (error) {
            console.error('Batch processing error:', error);
            this.showBatchError('Network error starting batch processing');
        }
    }

    async validateGoogleSheet() {
        const googleSheetUrl = document.getElementById('googleSheetUrl').value;
        
        if (!googleSheetUrl) {
            this.showError('Please enter a Google Sheet URL');
            return;
        }
        
        // Extract sheet ID from URL
        const sheetIdMatch = googleSheetUrl.match(/\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/);
        if (!sheetIdMatch) {
            this.showError('Invalid Google Sheet URL format');
            return;
        }
        
        const sheetId = sheetIdMatch[1];
        
        try {
            const response = await fetch('/api/batch/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sheet_id: sheetId
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.showSuccess(`✅ Sheet validated: ${data.companies_count} companies found`);
                } else {
                    this.showError(data.error || 'Failed to validate sheet');
                }
            } else {
                this.showError('Server error validating sheet');
            }
        } catch (error) {
            console.error('Sheet validation error:', error);
            this.showError('Network error validating sheet');
        }
    }

    showBatchStatus(message, processed, total) {
        const statusContainer = document.getElementById('batchStatus');
        const statusText = document.getElementById('statusText');
        const progressText = document.getElementById('progressText');
        const progressFill = statusContainer.querySelector('.progress-fill');
        
        if (statusContainer) {
            statusContainer.classList.remove('hidden');
        }
        
        if (statusText) {
            statusText.textContent = message;
            // Add appropriate styling based on status
            if (message.includes('✅')) {
                statusText.style.color = '#10b981'; // Green for success
            } else if (message.includes('❌')) {
                statusText.style.color = '#ef4444'; // Red for failure
            } else {
                statusText.style.color = ''; // Default color
            }
        }
        
        if (progressText) {
            progressText.textContent = `${processed}/${total}`;
        }
        
        if (progressFill) {
            const percentage = total > 0 ? (processed / total) * 100 : 0;
            progressFill.style.width = `${percentage}%`;
            
            // Add smooth transition for progress bar
            progressFill.style.transition = 'width 0.3s ease';
        }
    }

    showBatchError(message) {
        const statusContainer = document.getElementById('batchStatus');
        const statusText = document.getElementById('statusText');
        
        if (statusContainer) {
            statusContainer.classList.remove('hidden');
        }
        
        if (statusText) {
            statusText.textContent = `❌ Error: ${message}`;
            statusText.style.color = '#ef4444';
        }
        
        this.showError(message);
    }

    async pollBatchProgress(jobId, totalCompanies) {
        const pollInterval = 2000; // Poll every 2 seconds
        let retryCount = 0;
        const maxRetries = 3;
        
        const poll = async () => {
            try {
                const response = await fetch(`/api/batch/progress/${jobId}`);
                if (response.ok) {
                    const data = await response.json();
                    retryCount = 0; // Reset retry count on success
                    
                    if (data.status === 'completed') {
                        this.showBatchStatus('✅ Batch processing completed!', totalCompanies, totalCompanies);
                        this.showBatchResults(data.results);
                        return;
                    } else if (data.status === 'failed') {
                        this.showBatchError(data.error || 'Batch processing failed');
                        return;
                    } else {
                        // Update progress with detailed information
                        const processed = data.processed || 0;
                        const currentCompany = data.current_company || 'Initializing';
                        const message = data.current_message || 'Processing...';
                        
                        // Extract success/failure counts from message if available
                        let statusText = `Processing companies... (${currentCompany})`;
                        if (message.includes('✅') || message.includes('❌')) {
                            // Show the detailed status message
                            statusText = message;
                        }
                        
                        this.showBatchStatus(statusText, processed, totalCompanies);
                        
                        // Update additional UI elements if they exist
                        const successCountEl = document.getElementById('batchSuccessCount');
                        const failedCountEl = document.getElementById('batchFailedCount');
                        if (successCountEl && data.successful !== undefined) {
                            successCountEl.textContent = data.successful;
                        }
                        if (failedCountEl && data.failed !== undefined) {
                            failedCountEl.textContent = data.failed;
                        }
                        
                        // Continue polling
                        setTimeout(poll, pollInterval);
                    }
                } else if (response.status === 404 && retryCount < maxRetries) {
                    // Job not found yet, retry with backoff
                    retryCount++;
                    console.log(`Job not found yet, retrying... (${retryCount}/${maxRetries})`);
                    setTimeout(poll, pollInterval * retryCount);
                } else {
                    this.showBatchError('Failed to get progress updates');
                }
            } catch (error) {
                console.error('Progress polling error:', error);
                this.showBatchError('Network error getting progress');
            }
        };
        
        // Start polling with a small delay to allow job creation
        setTimeout(poll, 1000);
    }

    showBatchResults(results) {
        const resultsContainer = document.getElementById('batchResults');
        const resultsContent = document.getElementById('batchResultsContent');
        
        if (!results || !resultsContainer || !resultsContent) {
            return;
        }
        
        resultsContainer.classList.remove('hidden');
        
        // Handle the correct data structure: results.successful and results.failed arrays
        const successful = results.successful || [];
        const failed = results.failed || [];
        const successCount = successful.length;
        const failureCount = failed.length;
        const totalCost = results.total_cost_usd || 0;
        const totalTokens = (results.total_input_tokens || 0) + (results.total_output_tokens || 0);
        
        const resultsHTML = `
            <div class="batch-summary">
                <div class="summary-stats">
                    <div class="summary-stat success">
                        <span class="stat-number">${successCount}</span>
                        <span class="stat-label">Successful</span>
                    </div>
                    <div class="summary-stat failure">
                        <span class="stat-number">${failureCount}</span>
                        <span class="stat-label">Failed</span>
                    </div>
                    <div class="summary-stat total">
                        <span class="stat-number">${successCount + failureCount}</span>
                        <span class="stat-label">Total</span>
                    </div>
                    <div class="summary-stat cost">
                        <span class="stat-number">$${totalCost.toFixed(2)}</span>
                        <span class="stat-label">Total Cost</span>
                    </div>
                    <div class="summary-stat tokens">
                        <span class="stat-number">${totalTokens.toLocaleString()}</span>
                        <span class="stat-label">Tokens</span>
                    </div>
                </div>
            </div>
            <div class="batch-results-list">
                ${successful.map(result => `
                    <div class="batch-result-item success">
                        <div class="result-company">${this.escapeHtml(result.name)}</div>
                        <div class="result-status">✅ Success (Row ${result.row})</div>
                        <div class="result-details">
                            Cost: $${result.cost_usd ? result.cost_usd.toFixed(3) : '0.000'} | 
                            Tokens: ${result.tokens ? (result.tokens.input + result.tokens.output).toLocaleString() : '0'}
                        </div>
                    </div>
                `).join('')}
                ${failed.map(result => `
                    <div class="batch-result-item failure">
                        <div class="result-company">${this.escapeHtml(result.name)}</div>
                        <div class="result-status">❌ Failed (Row ${result.row})</div>
                        <div class="result-error">${this.escapeHtml(result.error || 'Unknown error')}</div>
                    </div>
                `).join('')}
            </div>
        `;
        
        resultsContent.innerHTML = resultsHTML;
        
        this.showSuccess(`Batch processing completed: ${successCount}/${successCount + failureCount} companies processed successfully. Total cost: $${totalCost.toFixed(2)}`);
    }

    // =============================================================================
    // CLASSIFICATION ANALYTICS METHODS (Phase 3)
    // =============================================================================

    async loadClassificationAnalytics() {
        try {
            
            // Load stats, categories, and unclassified count in parallel
            const [statsResponse, categoriesResponse, unclassifiedResponse] = await Promise.all([
                fetch('/api/classification/stats'),
                fetch('/api/classification/categories'),
                fetch('/api/classification/unclassified')
            ]);
            
            if (!statsResponse.ok || !categoriesResponse.ok || !unclassifiedResponse.ok) {
                throw new Error('Failed to load classification data');
            }
            
            const stats = await statsResponse.json();
            const categories = await categoriesResponse.json();
            const unclassified = await unclassifiedResponse.json();
            
            this.updateClassificationStats(stats);
            this.updateTopCategories(categories.categories.slice(0, 10)); // Top 10 categories
            this.updateUnclassifiedCount(unclassified.total_unclassified);
            
            
        } catch (error) {
            console.error('❌ Failed to load classification analytics:', error);
            this.showError('Failed to load classification analytics. Please try again.');
        }
    }

    updateClassificationStats(stats) {
        // Update main stats
        document.getElementById('totalCompanies').textContent = stats.total_companies;
        document.getElementById('classifiedCompanies').textContent = stats.classified_companies;
        document.getElementById('saasCompanies').textContent = stats.saas_companies;
        document.getElementById('classificationPercentage').textContent = `${stats.classification_percentage}%`;
        
        // Update confidence distribution
        const totalClassified = stats.classified_companies;
        const highCount = stats.confidence_distribution.high;
        const mediumCount = stats.confidence_distribution.medium;
        const lowCount = stats.confidence_distribution.low;
        
        // Calculate percentages for progress bars
        const highPercent = totalClassified > 0 ? (highCount / totalClassified) * 100 : 0;
        const mediumPercent = totalClassified > 0 ? (mediumCount / totalClassified) * 100 : 0;
        const lowPercent = totalClassified > 0 ? (lowCount / totalClassified) * 100 : 0;
        
        // Update progress bars with animation
        setTimeout(() => {
            document.getElementById('highConfidenceBar').style.width = `${highPercent}%`;
            document.getElementById('mediumConfidenceBar').style.width = `${mediumPercent}%`;
            document.getElementById('lowConfidenceBar').style.width = `${lowPercent}%`;
        }, 100);
        
        // Update counts
        document.getElementById('highConfidenceCount').textContent = highCount;
        document.getElementById('mediumConfidenceCount').textContent = mediumCount;
        document.getElementById('lowConfidenceCount').textContent = lowCount;
    }

    updateTopCategories(categories) {
        const categoriesList = document.getElementById('categoriesList');
        
        if (!categories || categories.length === 0) {
            categoriesList.innerHTML = '<p style="color: var(--text-muted); text-align: center;">No categories found</p>';
            return;
        }
        
        const categoriesHTML = categories.map(category => `
            <div class="category-item">
                <span class="category-name">${this.escapeHtml(category.name)}</span>
                <div>
                    <span class="category-count">${category.count}</span>
                    ${!category.in_taxonomy ? '<span class="category-badge">Custom</span>' : ''}
                </div>
            </div>
        `).join('');
        
        categoriesList.innerHTML = categoriesHTML;
    }

    async exportClassificationData(format) {
        try {
            const includeUnclassified = document.getElementById('includeUnclassified').checked;
            const url = `/api/classification/export?format=${format}&include_unclassified=${includeUnclassified}`;
            
            
            if (format === 'csv') {
                // For CSV, trigger a download
                const link = document.createElement('a');
                link.href = url;
                link.download = `theodore_classification_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                this.showSuccess('CSV export started. Check your downloads folder.');
            } else {
                // For JSON, fetch and display
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error('Export failed');
                }
                
                const data = await response.json();
                
                // Create a downloadable JSON file
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const downloadUrl = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = `theodore_classification_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(downloadUrl);
                
                this.showSuccess(`JSON export completed. ${data.total_companies} companies exported.`);
            }
            
        } catch (error) {
            console.error('❌ Export failed:', error);
            this.showError('Export failed. Please try again.');
        }
    }

    // =============================================================================
    // BATCH CLASSIFICATION METHODS (Phase 4)
    // =============================================================================

    updateUnclassifiedCount(count) {
        document.getElementById('unclassifiedCount').textContent = count;
    }

    async loadUnclassifiedCompanies() {
        try {
            
            const response = await fetch('/api/classification/unclassified');
            if (!response.ok) {
                throw new Error('Failed to load unclassified companies');
            }
            
            const data = await response.json();
            this.updateUnclassifiedCount(data.total_unclassified);
            
            this.showSuccess(`Found ${data.total_unclassified} unclassified companies`);
            
        } catch (error) {
            console.error('❌ Failed to load unclassified companies:', error);
            this.showError('Failed to refresh unclassified count. Please try again.');
        }
    }

    async startBatchClassification() {
        try {
            const batchSize = parseInt(document.getElementById('batchClassificationSize').value);
            const forceReclassify = document.getElementById('forceReclassify').checked;
            const startBtn = document.getElementById('startBatchClassificationBtn');
            
            
            // Disable button and show progress
            startBtn.disabled = true;
            startBtn.textContent = '🔄 Classifying...';
            this.showBatchClassificationProgress();
            
            const response = await fetch('/api/classification/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    batch_size: batchSize,
                    force_reclassify: forceReclassify
                })
            });
            
            if (!response.ok) {
                throw new Error('Batch classification request failed');
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.updateBatchClassificationProgress(100, result.processed, result.processed, result.successful);
                this.showBatchClassificationResults(result);
                this.showSuccess(`Batch classification completed: ${result.successful}/${result.processed} companies classified successfully`);
                
                // Refresh the analytics after classification
                setTimeout(() => {
                    this.loadClassificationAnalytics();
                }, 1000);
            } else {
                throw new Error(result.message || 'Batch classification failed');
            }
            
        } catch (error) {
            console.error('❌ Batch classification failed:', error);
            this.showError('Batch classification failed. Please try again.');
            this.hideBatchClassificationProgress();
        } finally {
            // Re-enable button
            const startBtn = document.getElementById('startBatchClassificationBtn');
            startBtn.disabled = false;
            startBtn.textContent = '🏷️ Start Batch Classification';
        }
    }

    showBatchClassificationProgress() {
        const progressContainer = document.getElementById('batchClassificationProgress');
        const resultsContainer = document.getElementById('batchClassificationResults');
        
        if (progressContainer) {
            progressContainer.classList.remove('hidden');
        }
        if (resultsContainer) {
            resultsContainer.classList.add('hidden');
        }
        
        // Reset progress
        this.updateBatchClassificationProgress(0, 0, 0, 0);
        document.getElementById('batchProgressStatus').textContent = 'Starting classification...';
    }

    hideBatchClassificationProgress() {
        const progressContainer = document.getElementById('batchClassificationProgress');
        if (progressContainer) {
            progressContainer.classList.add('hidden');
        }
    }

    updateBatchClassificationProgress(percentage, current, total, successful) {
        document.getElementById('batchProgressFill').style.width = `${percentage}%`;
        document.getElementById('batchProgressText').textContent = `${current}/${total} companies processed`;
        document.getElementById('batchProgressSuccess').textContent = `${successful} successful`;
        
        if (percentage === 100) {
            document.getElementById('batchProgressStatus').textContent = 'Classification completed';
        } else {
            document.getElementById('batchProgressStatus').textContent = `Processing company ${current + 1} of ${total}...`;
        }
    }

    showBatchClassificationResults(result) {
        const resultsContainer = document.getElementById('batchClassificationResults');
        const resultsContent = document.getElementById('batchClassificationResultsContent');
        
        if (!result.results || !resultsContainer || !resultsContent) {
            return;
        }
        
        resultsContainer.classList.remove('hidden');
        
        const successCount = result.successful || 0;
        const failureCount = result.processed - successCount;
        
        const resultsHTML = `
            <div class="batch-summary">
                <div class="batch-summary-stats">
                    <div class="batch-stat success">
                        <span class="batch-stat-number">${successCount}</span>
                        <span class="batch-stat-label">Successful</span>
                    </div>
                    <div class="batch-stat failure">
                        <span class="batch-stat-number">${failureCount}</span>
                        <span class="batch-stat-label">Failed</span>
                    </div>
                    <div class="batch-stat total">
                        <span class="batch-stat-number">${result.processed}</span>
                        <span class="batch-stat-label">Total</span>
                    </div>
                </div>
            </div>
            
            <div class="batch-results-list">
                ${result.results.map(item => `
                    <div class="batch-result-item ${item.status}">
                        <div class="batch-result-company">${this.escapeHtml(item.company_name)}</div>
                        <div class="batch-result-details">
                            ${item.status === 'success' ? `
                                <span class="batch-result-category">${this.escapeHtml(item.category || 'Unknown')}</span>
                                <span class="batch-result-confidence">${Math.round((item.confidence || 0) * 100)}% confidence</span>
                                <span>${item.is_saas ? '✅ SaaS' : '❌ Non-SaaS'}</span>
                            ` : `
                                <span class="batch-result-error">❌ ${this.escapeHtml(item.error || 'Classification failed')}</span>
                            `}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        resultsContent.innerHTML = resultsHTML;
    }
    
    renderClassificationSection(company) {
        // Helper function to format display text
        const displayText = (value) => value && value !== 'Unknown' && value !== 'N/A' && value.trim() !== '' ? value : 'Not Available';
        const displayPercentage = (value) => value ? `${Math.round(value * 100)}%` : 'Not Available';
        
        // Check if we have any classification data to show
        const hasClassificationData = company.is_saas !== undefined || 
                                    company.saas_classification || 
                                    company.business_model_framework ||
                                    company.classification_confidence;
        
        if (!hasClassificationData) {
            return ''; // No classification data to show
        }
        
        return `
            <div class="detail-section">
                <h4>🏷️ Business Model Classification</h4>
                ${company.is_saas !== undefined ? `<p><strong>SaaS Classification:</strong> ${company.is_saas ? '✅ SaaS' : '❌ Non-SaaS'}</p>` : ''}
                ${company.saas_classification ? `<p><strong>Category:</strong> ${displayText(company.saas_classification)}</p>` : ''}
                ${company.business_model_framework ? `<p><strong>Business Model Framework:</strong> ${displayText(company.business_model_framework)}</p>` : ''}
                ${company.classification_confidence ? `<p><strong>Classification Confidence:</strong> ${displayPercentage(company.classification_confidence)}</p>` : ''}
                ${company.classification_justification ? `<p><strong>Justification:</strong> ${displayText(company.classification_justification)}</p>` : ''}
            </div>
        `;
    }
}

// Global pagination functions
function goToPage(page) {
    const ui = window.theodoreUI;
    if (ui && ui.databaseSearchState) {
        ui.loadDatabaseBrowser({
            ...ui.databaseSearchState,
            page: page
        });
    }
}

function goToPreviousPage() {
    const ui = window.theodoreUI;
    if (ui && ui.databaseSearchState) {
        const currentPage = ui.databaseSearchState.page || 1;
        if (currentPage > 1) {
            goToPage(currentPage - 1);
        }
    }
}

function goToNextPage() {
    const ui = window.theodoreUI;
    if (ui && ui.databaseSearchState) {
        const currentPage = ui.databaseSearchState.page || 1;
        goToPage(currentPage + 1);
    }
}

function goToLastPage() {
    const ui = window.theodoreUI;
    if (ui && ui.databaseSearchState) {
        // Get last page from pagination info
        const paginationInfo = document.getElementById('paginationInfo');
        if (paginationInfo) {
            const text = paginationInfo.textContent;
            const match = text.match(/of (\d+) companies/);
            if (match) {
                const total = parseInt(match[1]);
                const pageSize = ui.databaseSearchState.page_size || 25;
                const lastPage = Math.ceil(total / pageSize);
                goToPage(lastPage);
            }
        }
    }
}

function changePageSize() {
    const ui = window.theodoreUI;
    const pageSizeSelect = document.getElementById('pageSize');
    if (ui && ui.databaseSearchState && pageSizeSelect) {
        ui.loadDatabaseBrowser({
            ...ui.databaseSearchState,
            page: 1, // Reset to first page
            page_size: parseInt(pageSizeSelect.value)
        });
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

function validateGoogleSheet() {
    const ui = window.theodoreUI || new TheodoreUI();
    ui.validateGoogleSheet();
}

// Test function for debugging progress indicator
function testProgressIndicator() {
    
    const progressEl = document.getElementById('progressContainer');
    
    if (progressEl) {
        progressEl.style.display = 'block';
        
        // Scroll into view to make sure it's visible
        progressEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
        console.error('🔧 Progress container not found!');
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.theodoreUI = new TheodoreUI();
        
        // Make test function available globally
        window.testProgressIndicator = testProgressIndicator;
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

async function viewProcessedCompanyDetails() {
    // View details of the just-processed company using the proper detailed modal
    if (window.lastProcessedCompanyId) {
        try {
            const response = await fetch(`/api/company/${window.lastProcessedCompanyId}`);
            const data = await response.json();
            
            if (data.success && data.company) {
                // Use the proper detailed modal function
                if (window.theodoreUI) {
                    window.theodoreUI.showCompanyDetailsModal(data.company);
                } else {
                    console.error('Theodore UI not available');
                    alert('Unable to show company details. Please try again.');
                }
            } else {
                alert('Company details not available.');
            }
        } catch (error) {
            console.error('Error fetching company details:', error);
            alert('Failed to load company details.');
        }
    } else {
        console.error('No processed company ID available');
        alert('Company details not available. Please try again.');
    }
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
                                <strong>Pages Processed:</strong> ${data.company.scraped_urls_count || (data.company.pages_crawled ? data.company.pages_crawled.length : 0)}
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