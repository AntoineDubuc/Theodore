// Theodore Web UI - Modern JavaScript

class TheodoreUI {
    constructor() {
        this.initializeEventListeners();
        this.setupFormValidation();
        this.initializeAnimations();
        this.initializeDatabaseBrowser();
        this.activeResearchJobs = new Map(); // Track active research jobs
        this.pollingIntervals = new Map(); // Track polling intervals
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
        
        // If switching to batch tab, initialize batch processing
        if (tabId === 'batchTab') {
            this.initializeBatchProcessing();
        }
        
        // If switching to classification tab, load classification analytics
        if (tabId === 'classificationTab') {
            this.loadClassificationAnalytics();
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
        console.log(`🟦 JS: ===== RESEARCH STARTED =====`);
        console.log(`🟦 JS: Company: ${companyName}`);
        console.log(`🟦 JS: Website: ${website}`);
        console.log(`🟦 JS: Timestamp: ${new Date().toISOString()}`);
        
        // Validate inputs
        if (!companyName || !website) {
            console.error(`🟦 JS: ❌ VALIDATION ERROR - Missing required data`);
            console.error(`🟦 JS: companyName: '${companyName}'`);
            console.error(`🟦 JS: website: '${website}'`);
            this.showError('Missing company name or website');
            return;
        }
        
        console.log(`🟦 JS: ✅ Input validation passed`);
        
        // Prepare request payload
        const requestPayload = {
            company: {
                name: companyName,
                website: website
            }
        };
        console.log(`🟦 JS: Request payload prepared:`, requestPayload);
        
        // Update UI immediately
        console.log(`🟦 JS: Step 1 - Updating UI state...`);
        this.updateResearchButton(companyName, 'researching');
        console.log(`🟦 JS: ✅ Research button updated`);
        
        // Track this research job
        const jobData = {
            status: 'starting',
            startTime: Date.now(),
            companyName: companyName,
            website: website
        };
        this.activeResearchJobs.set(companyName, jobData);
        console.log(`🟦 JS: ✅ Job tracking started:`, jobData);
        
        try {
            console.log(`🟦 JS: Step 2 - Setting up progress tracking...`);
            const progressContainer = this.showResearchProgressContainer(companyName);
            console.log(`🟦 JS: ✅ Progress container created`);
            
            console.log(`🟦 JS: Starting progress polling immediately...`);
            // Start polling immediately, no delay
            this.pollCurrentJobProgress(progressContainer, companyName);
            console.log(`🟦 JS: ✅ Progress polling started`);
            
            console.log(`🟦 JS: Step 3 - Making API request...`);
            console.log(`🟦 JS: URL: /api/research`);
            console.log(`🟦 JS: Method: POST`);
            console.log(`🟦 JS: Headers: Content-Type: application/json`);
            console.log(`🟦 JS: Body:`, JSON.stringify(requestPayload, null, 2));
            
            const requestStartTime = Date.now();
            
            // Create abort controller for timeout
            const abortController = new AbortController();
            const timeoutId = setTimeout(() => {
                console.log(`🟦 JS: ⏰ Request timeout after 30 seconds, aborting...`);
                abortController.abort();
            }, 30000); // 30 second timeout
            
            console.log(`🟦 JS: Sending fetch request with 30s timeout...`);
            const response = await fetch('/api/research', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestPayload),
                signal: abortController.signal
            });
            
            // Clear timeout if request completed
            clearTimeout(timeoutId);

            const requestEndTime = Date.now();
            const requestDuration = requestEndTime - requestStartTime;
            
            console.log(`🟦 JS: ===== API RESPONSE RECEIVED =====`);
            console.log(`🟦 JS: Response status: ${response.status}`);
            console.log(`🟦 JS: Response status text: ${response.statusText}`);
            console.log(`🟦 JS: Response headers:`, Object.fromEntries(response.headers.entries()));
            console.log(`🟦 JS: Request duration: ${requestDuration}ms`);
            
            console.log(`🟦 JS: Parsing JSON response...`);
            const data = await response.json();
            console.log(`🟦 JS: ✅ JSON parsed successfully`);
            console.log(`🟦 JS: Response data keys:`, Object.keys(data));
            console.log(`🟦 JS: Full response:`, data);

            if (response.ok && data.success) {
                console.log(`🟦 JS: ===== RESEARCH SUCCESS =====`);
                console.log(`🟦 JS: ✅ Research completed for ${companyName}`);
                console.log(`🟦 JS: Processing time: ${data.processing_time}s`);
                console.log(`🟦 JS: Enhanced company data keys:`, Object.keys(data.company || {}));
                console.log(`🟦 JS: Research status: ${data.company?.research_status}`);
                console.log(`🟦 JS: Full enhanced data:`, data.company);
                
                const enhancedCompany = data.company;
                console.log(`🟦 JS: Step 4 - Updating UI with results...`);
                
                this.showSuccess(`Research completed for ${companyName}! Generated comprehensive business intelligence.`);
                console.log(`🟦 JS: ✅ Success message shown`);
                
                // Update the result card with enhanced data
                console.log(`🟦 JS: Updating result card...`);
                this.updateResultCardWithResearch(companyName, enhancedCompany);
                console.log(`🟦 JS: ✅ Result card updated`);
                
                // Hide progress container and cleanup
                console.log(`🟦 JS: Cleaning up progress tracking...`);
                this.hideResearchProgressContainer(companyName);
                this.cleanupResearchJob(companyName);
                console.log(`🟦 JS: ✅ Cleanup completed`);
                
                console.log(`🟦 JS: ===== RESEARCH FLOW COMPLETED SUCCESSFULLY =====`);
                
            } else {
                console.log(`🟦 JS: ===== RESEARCH FAILED =====`);
                console.error(`🟦 JS: ❌ Response status: ${response.status}`);
                console.error(`🟦 JS: ❌ Success flag: ${data.success}`);
                console.error(`🟦 JS: ❌ Error message: ${data.error}`);
                console.error(`🟦 JS: ❌ Exception type: ${data.exception_type}`);
                console.error(`🟦 JS: ❌ Full error data:`, data);
                
                const errorMessage = data.error || 'Failed to complete research';
                console.log(`🟦 JS: Showing error message: ${errorMessage}`);
                this.showError(errorMessage);
                
                // Reset button on error
                console.log(`🟦 JS: Resetting research button state...`);
                this.updateResearchButton(companyName, 'unknown');
                
                // Hide progress container and cleanup
                console.log(`🟦 JS: Cleaning up after error...`);
                this.hideResearchProgressContainer(companyName);
                this.cleanupResearchJob(companyName);
                console.log(`🟦 JS: ✅ Error cleanup completed`);
            }
        } catch (networkError) {
            console.log(`🟦 JS: ===== NETWORK/EXCEPTION ERROR =====`);
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
            
            if (networkError.name === 'AbortError') {
                console.error(`🟦 JS: ❌ Request was aborted (timeout or manual cancellation)`);
                errorMessage = 'Research request timed out after 30 seconds';
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
                
            console.log(`🟦 JS: Showing error message: ${errorMessage}`);
            this.showError(errorMessage);
            
            // Reset button on error  
            console.log(`🟦 JS: Resetting research button due to exception...`);
            this.updateResearchButton(companyName, 'unknown');
            
            // Hide progress container and cleanup
            console.log(`🟦 JS: Cleaning up after exception...`);
            this.hideResearchProgressContainer(companyName);
            this.cleanupResearchJob(companyName);
            console.log(`🟦 JS: ✅ Exception cleanup completed`);
            
            console.log(`🟦 JS: ===== RESEARCH FLOW FAILED WITH EXCEPTION =====`);
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
        
        console.log(`🔍 PROGRESS CONTAINER: Looking for container with ID: ${progressId}`);
        console.log(`🔍 PROGRESS CONTAINER: Container exists: ${!!progressContainer}`);
        
        if (!progressContainer) {
            console.log(`🔍 PROGRESS CONTAINER: Creating new container for ${companyName}`);
            
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
            
            console.log(`🔍 PROGRESS CONTAINER: Results container found: ${!!resultsContainer}`);
            console.log(`🔍 PROGRESS CONTAINER: Results section found: ${!!resultsSection}`);
            console.log(`🔍 PROGRESS CONTAINER: Main content found: ${!!mainContent}`);
            
            if (resultsContainer) {
                resultsContainer.appendChild(progressContainer);
                console.log(`🔍 PROGRESS CONTAINER: ✅ Appended to results container`);
            } else if (resultsSection) {
                resultsSection.appendChild(progressContainer);
                console.log(`🔍 PROGRESS CONTAINER: ✅ Appended to results section`);
            } else if (mainContent) {
                mainContent.appendChild(progressContainer);
                console.log(`🔍 PROGRESS CONTAINER: ✅ Appended to main content`);
            } else {
                document.body.appendChild(progressContainer);
                console.log(`🔍 PROGRESS CONTAINER: ✅ Appended to body as fallback`);
            }
        } else {
            console.log(`🔍 PROGRESS CONTAINER: Using existing container`);
        }
        
        // Ensure it's visible and scroll to it
        progressContainer.style.display = 'block';
        progressContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        console.log(`🔍 PROGRESS CONTAINER: ✅ Container is now visible and scrolled into view`);
        
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
            console.log(`🔄 PROGRESS POLL: Checking progress for ${companyName}`);
            console.log(`🔄 PROGRESS POLL: Progress container exists: ${!!progressContainer}`);
            console.log(`🔄 PROGRESS POLL: Progress container visible: ${progressContainer ? progressContainer.style.display !== 'none' : false}`);
            
            const response = await fetch('/api/progress/current');
            const data = await response.json();
            console.log(`📊 PROGRESS POLL: Server response:`, data);
            
            // FORCE SHOW the progress container in case it's hidden
            if (progressContainer) {
                progressContainer.style.display = 'block';
                console.log(`🔄 PROGRESS POLL: ✅ Forced progress container to be visible`);
            }

            // Handle different response statuses
            if (response.ok && data.status === 'recent_completion') {
                console.log(`🔄 POLLING: Detected recent completion for ${companyName}`);
                console.log(`🔄 POLLING: Completion message: ${data.message}`);
                
                // Show completion in progress container
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
                
                // Show success message
                console.log(`🔄 POLLING: Showing success message`);
                this.showSuccess(`Research completed successfully for ${companyName}!`);
                
                // Stop polling and update button
                this.updateResearchButton(companyName, 'researched');
                
                // Hide progress container after showing success
                setTimeout(() => {
                    this.hideResearchProgressContainer(companyName);
                    this.cleanupResearchJob(companyName);
                }, 3000); // Show success for 3 seconds
                
                return; // Stop polling
            } else if (response.ok && data.status === 'recent_failure') {
                console.log(`🔄 POLLING: Detected recent failure for ${companyName}`);
                console.log(`🔄 POLLING: Failure reason: ${data.message}`);
                
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
                console.log(`🔄 POLLING: Stopping polling due to failure`);
                this.showError(data.message);
                this.updateResearchButton(companyName, 'unknown');
                
                // Hide progress container after showing error
                setTimeout(() => {
                    this.hideResearchProgressContainer(companyName);
                    this.cleanupResearchJob(companyName);
                }, 5000); // Show error for 5 seconds
                
                return; // Stop polling
            }
            
            // Check for any progress data that matches our company (running OR recently completed)
            let relevantProgress = null;
            if (response.ok && data.progress && data.progress.company_name === companyName) {
                relevantProgress = data.progress;
            } else if (response.ok && data.status === 'recent_failure' && data.progress && data.progress.company_name === companyName) {
                relevantProgress = data.progress;
            }
            
            if (relevantProgress) {
                const progress = relevantProgress;
                console.log(`📊 Processing progress data:`, progress);
                
                // Check if job has failed
                if (progress.status === 'failed') {
                    console.log(`🔄 POLLING: Job failed - ${progress.error}`);
                    
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
                
                console.log(`🎯 Current phase data:`, currentPhaseData);
                
                if (progressFill) {
                    progressFill.style.width = `${Math.min(progressPercent, 100)}%`;
                }
                
                let statusText = `Researching ${companyName}`;
                let detailsText = '';
                
                if (currentPhaseData) {
                    statusText = `${currentPhaseData.name} (${currentPhase}/${totalPhases})`;
                    console.log(`📝 Updated status text: ${statusText}`);
                    
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
                            console.log(`🔍 SCRAPING: Currently scraping page ${currentPhaseData.pages_completed}/${currentPhaseData.total_pages}`);
                            console.log(`🔍 SCRAPING: Page URL: ${currentPhaseData.current_page}`);
                            if (currentPhaseData.scraped_content_preview) {
                                console.log(`📄 SCRAPED CONTENT PREVIEW:`);
                                console.log(`📄 ${currentPhaseData.scraped_content_preview.substring(0, 500)}...`);
                                console.log(`📄 END OF CONTENT PREVIEW`);
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
                    console.log(`✅ Updated progress text to: "${statusText}"`);
                }
                
                if (progressDetails) {
                    progressDetails.textContent = detailsText;
                    progressDetails.style.display = detailsText ? 'block' : 'none';
                    if (detailsText) {
                        console.log(`✅ Updated progress details to: "${detailsText}"`);
                    }
                }

                // Continue polling if job is still running
                if (progress.status === 'running') {
                    const timeoutId = setTimeout(() => {
                        this.pollCurrentJobProgress(progressContainer, companyName);
                    }, 2000); // Poll every 2 seconds
                    this.pollingIntervals.set(companyName, timeoutId);
                }
            } else {
                console.log(`🔄 PROGRESS POLL: No matching job found, will retry in 1 second...`);
                console.log(`🔄 PROGRESS POLL: Available jobs in response:`, data);
                // No matching job found, poll again more frequently in case it hasn't started yet
                const timeoutId = setTimeout(() => {
                    this.pollCurrentJobProgress(progressContainer, companyName);
                }, 1000); // Poll every 1 second when waiting for job to start
                this.pollingIntervals.set(companyName, timeoutId);
            }
        } catch (error) {
            console.error('Progress polling error:', error);
            // Continue polling despite errors
            const timeoutId = setTimeout(() => {
                this.pollCurrentJobProgress(progressContainer, companyName);
            }, 5000); // Poll less frequently on error
            this.pollingIntervals.set(companyName, timeoutId);
        }
    }

    cancelResearch(companyName) {
        console.log(`🛑 Canceling research for: ${companyName}`);
        
        // Cleanup the research job
        this.cleanupResearchJob(companyName);
        
        // Hide progress container
        this.hideResearchProgressContainer(companyName);
        
        // Reset button
        this.updateResearchButton(companyName, 'unknown');
        
        // Show user feedback
        this.showError(`Research canceled for ${companyName}`);
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
        
        console.log(`🧹 Cleaned up research job for: ${companyName}`);
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
            console.log(`📋 Tech Stack:`, researchedCompany.tech_stack);
            console.log(`📋 Company Size: "${researchedCompany.company_size}"`);
            console.log(`📋 Value Proposition: "${researchedCompany.value_proposition}"`);
            console.log(`📋 Pain Points:`, researchedCompany.pain_points);
            console.log(`📋 Job Listings: "${researchedCompany.job_listings}"`);
            console.log(`📋 Job Listings Details:`, researchedCompany.job_listings_details);
            console.log(`📋 Crawl Depth:`, researchedCompany.crawl_depth);
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
                    console.log(`🔍 Scraping: ${currentPhaseData.current_page}`);
                    if (currentPhaseData.scraped_content_preview) {
                        console.log(`📄 Content preview: ${currentPhaseData.scraped_content_preview.substring(0, 200)}...`);
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
                <h3>${this.escapeHtml(company.name)}</h3>
                
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
                    <p><strong>Pages Crawled:</strong> ${displayNumber(company.pages_crawled ? company.pages_crawled.length : 0, '0')}</p>
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
        const companySize = this.extractResearchField(researchData, 'Company Size') || 'Unknown';
        console.log(`📋 Extracted Company Size: "${companySize}"`);
        const techStack = this.extractResearchField(researchData, 'Tech Stack') || 'Not available';
        console.log(`📋 Extracted Tech Stack: "${techStack}"`);
        const valueProposition = this.extractResearchField(researchData, 'Value Proposition') || 'Not available';
        console.log(`📋 Extracted Value Proposition: "${valueProposition}"`);
        const painPoints = this.extractResearchField(researchData, 'Pain Points') || 'Not available';
        console.log(`📋 Extracted Pain Points: "${painPoints}"`);
        const researchInfo = this.extractResearchField(researchData, 'Research Info') || 'Research metadata unavailable';
        console.log(`📋 Extracted Research Info: "${researchInfo}"`);
        const jobListings = this.extractResearchField(researchData, 'Job Listings') || 'Not available';
        console.log(`📋 Extracted Job Listings: "${jobListings}"`);
        
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
        console.log('Initializing batch processing...');
        
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
                if (googleSheetUrlInput && data.google_sheet_url) {
                    googleSheetUrlInput.value = data.google_sheet_url;
                }
            }
        } catch (error) {
            console.log('Could not load saved Google Sheet URL:', error);
        }
    }

    async handleBatchProcessing(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const googleSheetUrl = formData.get('google_sheet_url');
        const batchSize = parseInt(formData.get('batch_size'));
        
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
                    batch_size: batchSize
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
        }
        
        if (progressText) {
            progressText.textContent = `${processed}/${total}`;
        }
        
        if (progressFill) {
            const percentage = total > 0 ? (processed / total) * 100 : 0;
            progressFill.style.width = `${percentage}%`;
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
        
        const poll = async () => {
            try {
                const response = await fetch(`/api/batch/progress/${jobId}`);
                if (response.ok) {
                    const data = await response.json();
                    
                    if (data.status === 'completed') {
                        this.showBatchStatus('✅ Batch processing completed!', totalCompanies, totalCompanies);
                        this.showBatchResults(data.results);
                        return;
                    } else if (data.status === 'failed') {
                        this.showBatchError(data.error || 'Batch processing failed');
                        return;
                    } else {
                        // Update progress
                        const processed = data.processed || 0;
                        this.showBatchStatus(`Processing companies... (${data.current_company || 'Loading'})`, processed, totalCompanies);
                        
                        // Continue polling
                        setTimeout(poll, pollInterval);
                    }
                } else {
                    this.showBatchError('Failed to get progress updates');
                }
            } catch (error) {
                console.error('Progress polling error:', error);
                this.showBatchError('Network error getting progress');
            }
        };
        
        poll();
    }

    showBatchResults(results) {
        const resultsContainer = document.getElementById('batchResults');
        const resultsContent = document.getElementById('batchResultsContent');
        
        if (!results || !resultsContainer || !resultsContent) {
            return;
        }
        
        resultsContainer.classList.remove('hidden');
        
        const successCount = results.filter(r => r.status === 'success').length;
        const failureCount = results.filter(r => r.status === 'failed').length;
        
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
                        <span class="stat-number">${results.length}</span>
                        <span class="stat-label">Total</span>
                    </div>
                </div>
            </div>
            <div class="batch-results-list">
                ${results.map(result => `
                    <div class="batch-result-item ${result.status}">
                        <div class="result-company">${this.escapeHtml(result.company)}</div>
                        <div class="result-status">
                            ${result.status === 'success' ? '✅' : '❌'} ${result.status}
                        </div>
                        ${result.products_count ? `<div class="result-details">${result.products_count} products/services extracted</div>` : ''}
                        ${result.error ? `<div class="result-error">${this.escapeHtml(result.error)}</div>` : ''}
                    </div>
                `).join('')}
            </div>
        `;
        
        resultsContent.innerHTML = resultsHTML;
        
        this.showSuccess(`Batch processing completed: ${successCount}/${results.length} companies processed successfully`);
    }

    // =============================================================================
    // CLASSIFICATION ANALYTICS METHODS (Phase 3)
    // =============================================================================

    async loadClassificationAnalytics() {
        try {
            console.log('📊 Loading classification analytics...');
            
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
            
            console.log('✅ Classification analytics loaded successfully');
            
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
            
            console.log(`📊 Exporting classification data as ${format.toUpperCase()}...`);
            
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
            console.log('🔄 Refreshing unclassified companies count...');
            
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
            
            console.log(`🏷️ Starting batch classification: ${batchSize} companies, force: ${forceReclassify}`);
            
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