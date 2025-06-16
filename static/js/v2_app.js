// Theodore V2 Web UI - Fast Discovery & Focused Research

class TheodoreV2UI {
    constructor() {
        this.initializeEventListeners();
        this.setupInputDetection();
        this.activeResearchJobs = new Map();
    }

    initializeEventListeners() {
        // Discovery form
        const discoveryForm = document.getElementById('discoveryForm');
        if (discoveryForm) {
            discoveryForm.addEventListener('submit', this.handleDiscovery.bind(this));
        }

        // Input change detection
        const companyInput = document.getElementById('companyInput');
        if (companyInput) {
            companyInput.addEventListener('input', this.handleInputChange.bind(this));
        }

        // Tab navigation
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', this.handleTabSwitch.bind(this));
        });
    }

    setupInputDetection() {
        console.log('🎯 V2 UI initialized with smart input detection');
    }

    async handleInputChange(event) {
        const inputText = event.target.value.trim();
        const indicator = document.getElementById('inputTypeIndicator');

        if (!inputText) {
            indicator.style.display = 'none';
            return;
        }

        try {
            // Call backend to validate URL
            const response = await fetch('/api/v2/validate-url', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ input_text: inputText })
            });

            const result = await response.json();

            if (result.success) {
                indicator.style.display = 'block';
                indicator.textContent = result.is_url ? '🌐 URL' : '🏢 Company';
                indicator.style.background = result.is_url ? 
                    'rgba(40, 167, 69, 0.1)' : 'rgba(102, 126, 234, 0.1)';
            } else {
                indicator.style.display = 'none';
            }
        } catch (error) {
            console.warn('Input validation error:', error);
            indicator.style.display = 'none';
        }
    }

    async handleDiscovery(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const inputText = formData.get('input_text').trim();
        const limit = parseInt(formData.get('limit'));

        if (!inputText) {
            this.showMessage('Please enter a company name or website URL', 'error');
            return;
        }

        console.log(`🔍 V2 Discovery starting: "${inputText}" (limit: ${limit})`);

        // Update UI
        this.setDiscoveryLoading(true);
        this.hideDiscoveryResults();

        try {
            const response = await fetch('/api/v2/discover', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    input_text: inputText,
                    limit: limit 
                })
            });

            const result = await response.json();

            if (result.success) {
                console.log(`✅ V2 Discovery completed: ${result.total_found} companies found`);
                this.displayDiscoveryResults(result);
                this.showMessage(`Found ${result.total_found} similar companies!`, 'success');
            } else {
                console.error('❌ V2 Discovery failed:', result.error);
                this.showMessage(`Discovery failed: ${result.error}`, 'error');
            }

        } catch (error) {
            console.error('❌ V2 Discovery error:', error);
            this.showMessage('Discovery request failed. Please try again.', 'error');
        } finally {
            this.setDiscoveryLoading(false);
        }
    }

    displayDiscoveryResults(result) {
        const resultsContainer = document.getElementById('discoveryResults');
        const metadataContainer = document.getElementById('discoveryMetadata');
        const cardsContainer = document.getElementById('companyCards');

        // Show results section
        resultsContainer.style.display = 'block';

        // Display metadata
        metadataContainer.innerHTML = `
            <div class="metadata-item">
                <span class="metadata-label">Input Type:</span>
                <span class="metadata-value">${result.input_type === 'url' ? '🌐 Website URL' : '🏢 Company Name'}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Primary Company:</span>
                <span class="metadata-value">${result.primary_company.name}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Similar Companies Found:</span>
                <span class="metadata-value">${result.total_found}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Discovery Method:</span>
                <span class="metadata-value">${result.discovery_method}</span>
            </div>
        `;

        // Display company cards
        cardsContainer.innerHTML = '';
        
        // First, add the primary company card with "Research this company" button
        const primaryCard = this.createPrimaryCompanyCard(result.primary_company);
        cardsContainer.appendChild(primaryCard);
        
        // Then add similar companies
        result.similar_companies.forEach((company, index) => {
            const card = this.createCompanyCard(company, index + 1); // +1 to offset after primary
            cardsContainer.appendChild(card);
        });

        // Smooth scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    createCompanyCard(company, index) {
        const card = document.createElement('div');
        card.className = 'company-card';
        card.style.animationDelay = `${index * 0.1}s`;

        const similarityScore = (company.similarity_score * 100).toFixed(0);
        const companyId = `company-${index}`;

        card.innerHTML = `
            <div class="company-header">
                <div class="company-info">
                    <h3>${this.escapeHtml(company.name)}</h3>
                    <a href="${this.escapeHtml(company.website)}" 
                       target="_blank" 
                       class="website">${this.escapeHtml(company.website)}</a>
                </div>
                <div class="similarity-score">${similarityScore}% similar</div>
            </div>
            
            <div class="company-details">
                <div class="detail-item">
                    <div class="detail-label">Relationship Type</div>
                    <div class="detail-value">${this.escapeHtml(company.relationship_type)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Why Similar</div>
                    <div class="detail-value">${this.escapeHtml(company.reasoning)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Business Context</div>
                    <div class="detail-value">${this.escapeHtml(company.business_context)}</div>
                </div>
            </div>
            
            <div class="company-actions">
                <button class="btn-research" 
                        onclick="theodoreV2.startResearch('${companyId}', '${this.escapeJs(company.name)}', '${this.escapeJs(company.website)}')">
                    <span>🔬</span>
                    Research Now
                </button>
                <button class="btn-review" 
                        id="${companyId}-review-btn"
                        style="display: none;"
                        onclick="theodoreV2.showResearchReview('${companyId}', '${this.escapeJs(company.name)}')">
                    <span>📊</span>
                    Review Research
                </button>
            </div>
            
            <div id="${companyId}-progress" class="research-progress" style="display: none;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <div class="loading-spinner"></div>
                    <span>Researching company...</span>
                </div>
                <div id="${companyId}-progress-text" style="font-size: 0.85rem; color: var(--text-muted);"></div>
            </div>
            
            <div id="${companyId}-results" class="research-results" style="display: none;">
                <h5 style="margin: 0 0 12px 0; color: var(--text-primary);">Research Results</h5>
                <div id="${companyId}-content" class="research-content"></div>
            </div>
        `;

        return card;
    }

    createPrimaryCompanyCard(company) {
        const card = document.createElement('div');
        card.className = 'company-card primary-company';
        card.style.animationDelay = '0s';

        const companyId = 'primary-company';

        const websiteDisplay = company.website ? 
            `<a href="${this.escapeHtml(company.website)}" target="_blank" class="website">${this.escapeHtml(company.website)}</a>` :
            `<span class="website">Website will be detected during research</span>`;

        card.innerHTML = `
            <div class="company-header">
                <div class="company-info">
                    <h3>${this.escapeHtml(company.name)} <span class="primary-badge">You searched for this</span></h3>
                    ${websiteDisplay}
                </div>
            </div>
            
            <div class="company-actions">
                <button class="btn-research primary-research" 
                        id="${companyId}-research-btn"
                        onclick="theodoreV2.startResearch('${companyId}', '${this.escapeJs(company.name)}', '${this.escapeJs(company.website || '')}')">
                    <span>🔬</span>
                    Research This Company
                </button>
                <button class="btn-review" 
                        id="${companyId}-review-btn"
                        style="display: none;"
                        onclick="theodoreV2.showResearchReview('${companyId}', '${this.escapeJs(company.name || '')}')">
                    <span>📊</span>
                    View Research
                </button>
            </div>
            
            <div id="${companyId}-progress" class="research-progress" style="display: none;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <div class="loading-spinner"></div>
                    <span>Researching company...</span>
                </div>
                <div id="${companyId}-progress-text" style="font-size: 0.85rem; color: var(--text-muted);"></div>
            </div>
            
            <div id="${companyId}-results" class="research-results" style="display: none;">
                <h5 style="margin: 0 0 12px 0; color: var(--text-primary);">Research Results</h5>
                <div id="${companyId}-content" class="research-content"></div>
            </div>
        `;

        return card;
    }

    async startResearch(companyId, companyName, websiteUrl) {
        console.log(`🔬 Starting V2 research for ${companyName} at ${websiteUrl}`);

        // Handle different UI layouts based on companyId
        let button, progressDiv, resultsDiv, progressText;
        
        if (companyId === 'main-input-company') {
            // Main input research flow
            button = document.getElementById('researchThisButton');
            progressDiv = document.getElementById('main-input-company-progress');
            resultsDiv = document.getElementById('main-input-company-results');
            progressText = document.getElementById('main-input-company-progress-text');
            
            // Show the main research section
            document.getElementById('mainResearchSection').style.display = 'block';
        } else {
            // Company card research flow
            button = document.querySelector(`#${companyId}-progress`).previousElementSibling.querySelector('.btn-research');
            progressDiv = document.getElementById(`${companyId}-progress`);
            resultsDiv = document.getElementById(`${companyId}-results`);
            progressText = document.getElementById(`${companyId}-progress-text`);
        }

        if (!button || !progressDiv || !resultsDiv || !progressText) {
            console.error(`❌ Could not find required UI elements for ${companyId}`);
            this.showMessage(`UI error: Could not find required elements for research`, 'error');
            return;
        }

        button.disabled = true;
        button.innerHTML = '<div class="loading-spinner"></div> Researching...';
        progressDiv.style.display = 'block';
        resultsDiv.style.display = 'none';

        // Track active research
        this.activeResearchJobs.set(companyId, {
            company_name: companyName,
            website_url: websiteUrl,
            start_time: Date.now(),
            polling_interval: null
        });

        try {
            // Step 1: Start the research job asynchronously
            const response = await fetch('/api/v2/research/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    company_name: companyName,
                    website_url: websiteUrl
                })
            });

            const startResult = await response.json();

            if (!startResult.success) {
                this.displayResearchError(companyId, startResult.error);
                this.showMessage(`Failed to start research for ${companyName}: ${startResult.error}`, 'error');
                this.resetResearchUI(companyId);
                return;
            }

            // Step 2: Start progress polling immediately with job_id
            const jobId = startResult.job_id;
            console.log(`📋 Started research job ${jobId} for ${companyName}, beginning progress polling`);
            
            const pollingInterval = setInterval(() => {
                this.updateResearchProgressAndCheckCompletion(companyId, progressText, jobId, companyName);
            }, 1000);
            
            this.activeResearchJobs.get(companyId).polling_interval = pollingInterval;
            this.activeResearchJobs.get(companyId).job_id = jobId;

            this.showMessage(`Research started for ${companyName}...`, 'info');

        } catch (error) {
            console.error(`❌ V2 research error for ${companyName}:`, error);
            this.displayResearchError(companyId, 'Network error occurred');
            this.showMessage(`Research request failed for ${companyName}`, 'error');
            this.resetResearchUI(companyId);
        }
        // Note: No finally block - polling will be stopped when research completes/fails
    }

    async updateResearchProgressAndCheckCompletion(companyId, progressText, jobId, companyName) {
        try {
            // Use specific job_id to get progress
            const response = await fetch(`/api/progress/current?job_id=${jobId}`);
            const data = await response.json();

            if (data.success && data.progress) {
                const progress = data.progress;
                
                // Check if research is completed
                if (progress.status === 'completed') {
                    console.log(`✅ Research completed for ${companyName}`);
                    
                    // Stop polling
                    const activeJob = this.activeResearchJobs.get(companyId);
                    if (activeJob && activeJob.polling_interval) {
                        clearInterval(activeJob.polling_interval);
                    }
                    
                    // Get final results from the completed job and display them
                    await this.getAndDisplayCompletedResearch(companyId, jobId, companyName);
                    return;
                }
                
                // Check if research failed
                if (progress.status === 'failed') {
                    console.error(`❌ Research failed for ${companyName}: ${progress.error || 'Unknown error'}`);
                    
                    // Stop polling
                    const activeJob = this.activeResearchJobs.get(companyId);
                    if (activeJob && activeJob.polling_interval) {
                        clearInterval(activeJob.polling_interval);
                    }
                    
                    this.displayResearchError(companyId, progress.error || 'Research failed');
                    this.showMessage(`Research failed for ${companyName}`, 'error');
                    
                    // Reset UI
                    this.resetResearchUI(companyId);
                    return;
                }
                
                // Update progress display for running research
                this.updateProgressDisplay(progress, progressText);
            }
        } catch (error) {
            console.debug('Progress update failed:', error);
        }
    }

    updateProgressDisplay(progress, progressText) {
        // Find current phase details
        const phases = progress.phases || {};
        let statusMessage = 'Researching...';

        // Look for active phase
        for (const [phaseName, phaseData] of Object.entries(phases)) {
            if (phaseData.status === 'running') {
                if (phaseData.current_url) {
                    // Show current URL being crawled
                    const urlDisplay = this.shortenUrl(phaseData.current_url);
                    statusMessage = `${phaseData.progress_step || ''} ${urlDisplay}`;
                } else if (phaseData.status_message) {
                    statusMessage = phaseData.status_message;
                } else {
                    statusMessage = `${phaseName}...`;
                }
                break;
            }
        }

        // Update progress text
        progressText.textContent = statusMessage;
    }

    async getAndDisplayCompletedResearch(companyId, jobId, companyName) {
        try {
            // Get the completed research results from the progress system
            const progressResponse = await fetch(`/api/progress/current?job_id=${jobId}`);
            const progressData = await progressResponse.json();
            
            // Check if we have stored results in the progress data
            if (progressData.success && progressData.progress && progressData.progress.results) {
                // Use stored results from the completed job
                this.displayResearchResults(companyId, progressData.progress.results);
                this.showMessage(`Research completed for ${companyName}!`, 'success');
                
                // Show review button and store research data
                this.showReviewButton(companyId, progressData.progress.results);
            } else {
                // Fallback: call the synchronous endpoint to get fresh results
                const activeJob = this.activeResearchJobs.get(companyId);
                if (!activeJob) {
                    throw new Error('No active job data found');
                }
                
                const response = await fetch('/api/v2/research', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        company_name: companyName,
                        website_url: activeJob.website_url
                    })
                });

                const result = await response.json();

                if (result.success) {
                    this.displayResearchResults(companyId, result);
                    this.showMessage(`Research completed for ${companyName}!`, 'success');
                    
                    // Show review button and store research data
                    this.showReviewButton(companyId, result);
                } else {
                    this.displayResearchError(companyId, result.error || 'Failed to get results');
                    this.showMessage(`Failed to get results for ${companyName}`, 'error');
                }
            }
        } catch (error) {
            console.error('Failed to get completed research results:', error);
            this.displayResearchError(companyId, 'Failed to retrieve results');
            this.showMessage(`Failed to get results for ${companyName}`, 'error');
        } finally {
            this.resetResearchUI(companyId);
        }
    }

    resetResearchUI(companyId) {
        // Handle different UI layouts based on companyId
        let button, progressDiv;
        
        if (companyId === 'main-input-company') {
            // Main input research flow
            button = document.getElementById('researchThisButton');
            progressDiv = document.getElementById('main-input-company-progress');
        } else {
            // Company card research flow
            button = document.querySelector(`#${companyId}-progress`).previousElementSibling.querySelector('.btn-research');
            progressDiv = document.getElementById(`${companyId}-progress`);
        }
        
        if (button && progressDiv) {
            button.disabled = false;
            if (companyId === 'main-input-company') {
                button.innerHTML = '<span>🔬</span> Research This Company';
            } else {
                button.innerHTML = '<span>🔬</span> Research Now';
            }
            progressDiv.style.display = 'none';
        }
        
        // Remove from active jobs
        this.activeResearchJobs.delete(companyId);
    }

    shortenUrl(url) {
        try {
            const urlObj = new URL(url);
            const path = urlObj.pathname;
            
            // Show just the meaningful part of the path
            if (path === '/' || path === '') {
                return '🏠 Home page';
            } else {
                const parts = path.split('/').filter(part => part);
                const lastPart = parts[parts.length - 1] || 'page';
                return `📄 /${lastPart}`;
            }
        } catch (e) {
            return '📄 Page';
        }
    }

    displayResearchResults(companyId, result) {
        const resultsDiv = document.getElementById(`${companyId}-results`);
        const contentDiv = document.getElementById(`${companyId}-content`);

        resultsDiv.style.display = 'block';
        
        contentDiv.innerHTML = `
            <div style="margin-bottom: 16px;">
                <strong>Pages Analyzed:</strong> ${result.pages_analyzed}<br>
                <strong>Content Length:</strong> ${result.total_content_length.toLocaleString()} characters<br>
            </div>
            
            <div style="margin-bottom: 12px;">
                <strong>Page Breakdown:</strong>
                <ul style="margin: 8px 0 0 20px; font-size: 0.85rem;">
                    ${result.page_breakdown.map(page => 
                        `<li>${page.type}: ${page.content_length.toLocaleString()} chars</li>`
                    ).join('')}
                </ul>
            </div>
            
            <div style="margin-top: 16px;">
                <strong>Business Intelligence Analysis:</strong>
                <div style="margin-top: 8px; padding: 12px; background: rgba(255, 255, 255, 0.02); border-radius: 8px; white-space: pre-wrap; line-height: 1.6;">
${this.escapeHtml(result.analysis)}
                </div>
            </div>
        `;
    }

    displayResearchError(companyId, error) {
        const resultsDiv = document.getElementById(`${companyId}-results`);
        const contentDiv = document.getElementById(`${companyId}-content`);

        resultsDiv.style.display = 'block';
        contentDiv.innerHTML = `
            <div style="color: #ff6b6b;">
                <strong>Research Failed:</strong><br>
                ${this.escapeHtml(error)}
            </div>
        `;
    }

    setDiscoveryLoading(loading) {
        const button = document.getElementById('discoverButton');
        const buttonText = document.getElementById('discoverButtonText');

        if (loading) {
            button.disabled = true;
            buttonText.innerHTML = '<div class="loading-spinner"></div> Discovering...';
        } else {
            button.disabled = false;
            buttonText.textContent = 'Discover Similar Companies';
        }
    }

    hideDiscoveryResults() {
        const resultsContainer = document.getElementById('discoveryResults');
        resultsContainer.style.display = 'none';
    }

    showMessage(message, type) {
        const messagesContainer = document.getElementById('messages');
        const messageElement = document.createElement('div');
        
        messageElement.className = `message ${type}`;
        messageElement.style.cssText = `
            padding: 12px 20px;
            margin: 16px 0;
            border-radius: 8px;
            font-weight: 500;
            ${type === 'success' ? 
                'background: rgba(40, 167, 69, 0.1); border: 1px solid rgba(40, 167, 69, 0.3); color: #28a745;' :
                type === 'info' ?
                'background: rgba(102, 126, 234, 0.1); border: 1px solid rgba(102, 126, 234, 0.3); color: #667eea;' :
                'background: rgba(220, 53, 69, 0.1); border: 1px solid rgba(220, 53, 69, 0.3); color: #dc3545;'
            }
        `;
        messageElement.textContent = message;

        messagesContainer.appendChild(messageElement);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 5000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    escapeJs(text) {
        if (!text) return '';
        return text.replace(/\\/g, '\\\\')
                  .replace(/'/g, "\\'")
                  .replace(/"/g, '\\"')
                  .replace(/\n/g, '\\n')
                  .replace(/\r/g, '\\r')
                  .replace(/\t/g, '\\t');
    }
    
    showReviewButton(companyId, researchData) {
        const reviewBtn = document.getElementById(`${companyId}-review-btn`);
        if (reviewBtn) {
            reviewBtn.style.display = 'inline-block';
            
            // Store research data for review
            if (!this.researchDataStore) {
                this.researchDataStore = new Map();
            }
            this.researchDataStore.set(companyId, researchData);
            
            // Hide the old markdown-style results since we now have the review button
            const resultsDiv = document.getElementById(`${companyId}-results`);
            if (resultsDiv) {
                resultsDiv.style.display = 'none';
            }
            
            // Actions are now in the form buttons, no separate section needed
        }
    }

    hideViewResearchButton(companyName) {
        // Find the company ID that matches this company name
        let targetCompanyId = null;
        
        if (this.researchDataStore) {
            for (const [companyId, data] of this.researchDataStore.entries()) {
                if (data.company_name === companyName || data.name === companyName) {
                    targetCompanyId = companyId;
                    break;
                }
            }
        }
        
        if (targetCompanyId) {
            const reviewBtn = document.getElementById(`${targetCompanyId}-review-btn`);
            if (reviewBtn) {
                reviewBtn.style.display = 'none';
                console.log(`🔸 Hid View Research button for ${companyName} (${targetCompanyId})`);
            }
        } else {
            console.log(`⚠️ Could not find company ID for ${companyName} to hide View Research button`);
        }
    }
    
    showResearchReview(companyId, companyName) {
        const researchData = this.researchDataStore?.get(companyId);
        if (!researchData) {
            this.showMessage('No research data available for review', 'error');
            return;
        }
        
        // Debug: Log the research data to see what we have
        console.log('🔍 Research data for modal:', researchData);
        
        this.openResearchModal(companyName, researchData);
    }
    
    openResearchModal(companyName, researchData) {
        const modal = document.getElementById('researchModal');
        if (!modal) return;
        
        // Build modal content based on CompanyData model
        const modalContent = this.buildResearchModalContent(companyName, researchData);
        modal.innerHTML = modalContent;
        
        // Show modal
        modal.style.display = 'flex';
        
        // Add event listeners
        this.setupModalEventListeners(companyName, researchData);
    }
    
    buildResearchModalContent(companyName, researchData) {
        // Calculate completion percentage based on CompanyData model fields
        const completionStats = this.calculateCompletionStats(researchData);
        
        return `
            <div class="research-modal-content">
                <div class="research-modal-header">
                    <h2 class="research-modal-title">Research Review: ${this.escapeHtml(companyName)}</h2>
                    <button class="research-modal-close" onclick="theodoreV2.closeResearchModal()">
                        ×
                    </button>
                </div>
                
                <div class="research-modal-body">
                    <!-- Completion Stats -->
                    <div class="completion-stats">
                        <div class="completion-percentage">${completionStats.percentage}%</div>
                        <div class="completion-label">
                            ${completionStats.completed} of ${completionStats.total} fields completed
                        </div>
                    </div>
                    
                    <!-- Company Data Fields -->
                    <div class="field-grid">
                        ${this.buildFieldItems(researchData)}
                    </div>
                </div>
                
                <div class="modal-actions">
                    <button class="btn-cancel" onclick="theodoreV2.closeResearchModal()">
                        Cancel
                    </button>
                    <button class="btn-save" onclick="theodoreV2.saveToIndex('${this.escapeJs(companyName)}', this)">
                        💾 Add to Index
                    </button>
                </div>
            </div>
        `;
    }
    
    calculateCompletionStats(researchData) {
        // Complete CompanyData model fields from models.py including batch research fields
        const allFields = [
            'company_name', 'website', 'industry', 'business_model', 'company_size',
            'tech_stack', 'has_chat_widget', 'has_forms', 'pain_points', 'key_services',
            'competitive_advantages', 'target_market', 'company_description', 'value_proposition',
            'founding_year', 'location', 'employee_count_range', 'company_culture',
            'funding_status', 'social_media', 'contact_info', 'leadership_team',
            'recent_news', 'certifications', 'partnerships', 'awards', 'company_stage',
            'tech_sophistication', 'geographic_scope', 'business_model_type',
            'decision_maker_type', 'sales_complexity', 'ai_summary',
            // Batch Research Intelligence fields
            'has_job_listings', 'job_listings_count', 'job_listings_details',
            'products_services_offered', 'key_decision_makers', 'funding_stage_detailed',
            'sales_marketing_tools', 'recent_news_events'
        ];
        
        let completed = 0;
        allFields.forEach(field => {
            const value = researchData[field];
            
            let isPopulated = false;
            
            if (value === null || value === undefined || value === 'Unknown') {
                isPopulated = false;
            } else if (typeof value === 'string') {
                isPopulated = value.trim() !== '';
            } else if (Array.isArray(value)) {
                isPopulated = value.length > 0;
            } else if (typeof value === 'object') {
                // For objects, check if they have meaningful content
                const keys = Object.keys(value);
                isPopulated = keys.length > 0 && keys.some(key => {
                    const objValue = value[key];
                    return objValue !== null && objValue !== undefined && objValue !== '' && objValue !== 'Unknown';
                });
            } else if (typeof value === 'boolean') {
                isPopulated = true; // Booleans are always considered populated
            } else if (typeof value === 'number') {
                isPopulated = !isNaN(value);
            } else {
                isPopulated = !!value;
            }
            
            if (isPopulated) {
                completed++;
            }
        });
        
        const percentage = Math.round((completed / allFields.length) * 100);
        
        return {
            completed,
            total: allFields.length,
            percentage
        };
    }
    
    buildFieldItems(researchData) {
        // Complete CompanyData model structure with organized categories
        const fieldCategories = {
            'Basic Information': [
                { key: 'company_name', label: 'Company Name' },
                { key: 'website', label: 'Website' },
                { key: 'industry', label: 'Industry' },
                { key: 'business_model', label: 'Business Model' },
                { key: 'company_size', label: 'Company Size' },
                { key: 'location', label: 'Location' },
                { key: 'founding_year', label: 'Founded' }
            ],
            'Business Intelligence': [
                { key: 'company_description', label: 'Description' },
                { key: 'value_proposition', label: 'Value Proposition' },
                { key: 'target_market', label: 'Target Market' },
                { key: 'key_services', label: 'Key Services' },
                { key: 'competitive_advantages', label: 'Competitive Advantages' },
                { key: 'pain_points', label: 'Pain Points' }
            ],
            'Technology & Operations': [
                { key: 'tech_stack', label: 'Technology Stack' },
                { key: 'has_chat_widget', label: 'Has Chat Widget' },
                { key: 'has_forms', label: 'Has Lead Forms' },
                { key: 'tech_sophistication', label: 'Tech Sophistication' }
            ],
            'Company Details': [
                { key: 'employee_count_range', label: 'Employee Count' },
                { key: 'company_culture', label: 'Company Culture' },
                { key: 'funding_status', label: 'Funding Status' },
                { key: 'company_stage', label: 'Company Stage' },
                { key: 'geographic_scope', label: 'Geographic Scope' },
                { key: 'business_model_type', label: 'Business Model Type' },
                { key: 'decision_maker_type', label: 'Decision Maker Type' },
                { key: 'sales_complexity', label: 'Sales Complexity' }
            ],
            'Contacts & Social': [
                { key: 'leadership_team', label: 'Leadership Team' },
                { key: 'contact_info', label: 'Contact Information', isObject: true },
                { key: 'social_media', label: 'Social Media', isObject: true }
            ],
            'Batch Research Intelligence': [
                { key: 'has_job_listings', label: 'Has Job Listings' },
                { key: 'job_listings_count', label: 'Job Openings Count' },
                { key: 'job_listings_details', label: 'Job Listings Details', isSpecial: true },
                { key: 'products_services_offered', label: 'Products & Services Offered' },
                { key: 'key_decision_makers', label: 'Key Decision Makers', isObject: true },
                { key: 'funding_stage_detailed', label: 'Detailed Funding Stage' },
                { key: 'sales_marketing_tools', label: 'Sales & Marketing Tools' },
                { key: 'recent_news_events', label: 'Recent News & Events', isSpecial: true }
            ],
            'Additional Intelligence': [
                { key: 'recent_news', label: 'Recent News' },
                { key: 'certifications', label: 'Certifications' },
                { key: 'partnerships', label: 'Partnerships' },
                { key: 'awards', label: 'Awards' }
            ],
            'Research Metadata': [
                { key: 'pages_analyzed', label: 'Pages Analyzed' },
                { key: 'total_content_length', label: 'Content Length (chars)' },
                { key: 'page_breakdown', label: 'Page Breakdown', isSpecial: true }
            ],
            'AI Analysis': [
                { key: 'ai_summary', label: 'AI Summary', isLongText: true }
            ]
        };
        
        let fieldsHtml = '';
        
        Object.entries(fieldCategories).forEach(([category, fields]) => {
            fieldsHtml += `<div class="field-item" style="grid-column: 1 / -1;"><h4 style="margin: 0; color: var(--primary-color);">${category}</h4></div>`;
            
            fields.forEach(field => {
                const value = researchData[field.key];
                let displayValue;
                
                if (field.isSpecial && field.key === 'page_breakdown') {
                    // Special formatting for page breakdown
                    if (Array.isArray(value) && value.length > 0) {
                        displayValue = value.map(page => 
                            `<div style="margin-bottom: 8px;">
                                <strong>${page.type || 'Page'}:</strong> 
                                ${page.content_length ? page.content_length.toLocaleString() + ' chars' : 'N/A'}
                                <br><small style="color: var(--text-muted);">${page.url || 'Unknown URL'}</small>
                            </div>`
                        ).join('');
                    } else {
                        displayValue = 'No page data available';
                    }
                } else if (field.isSpecial && field.key === 'job_listings_details') {
                    // Special formatting for job listings details
                    if (Array.isArray(value) && value.length > 0) {
                        displayValue = value.map(job => 
                            `<div style="margin-bottom: 12px; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                                <strong>${job.title || 'Job Title'}</strong>
                                <br><small style="color: var(--text-muted);">Department: ${job.department || 'N/A'}</small>
                                <br><small style="color: var(--text-muted);">Location: ${job.location || 'N/A'}</small>
                            </div>`
                        ).join('');
                    } else {
                        displayValue = 'No job listings available';
                    }
                } else if (field.isSpecial && field.key === 'recent_news_events') {
                    // Special formatting for recent news/events
                    if (Array.isArray(value) && value.length > 0) {
                        displayValue = value.map(news => 
                            `<div style="margin-bottom: 12px; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                                <strong>${news.title || news.description || 'News Item'}</strong>
                                <br><small style="color: var(--text-muted);">Date: ${news.date || 'N/A'}</small>
                                ${news.description && news.title ? `<br><span style="font-size: 0.9em;">${news.description}</span>` : ''}
                            </div>`
                        ).join('');
                    } else {
                        displayValue = 'No recent news available';
                    }
                } else if (field.isLongText) {
                    // Special formatting for long analysis text
                    displayValue = value ? 
                        `<div style="max-height: 200px; overflow-y: auto; white-space: pre-wrap; font-family: inherit;">${this.escapeHtml(value)}</div>` : 
                        'No analysis available';
                } else if (field.isObject) {
                    // Special formatting for object fields like contact_info, social_media
                    if (value && typeof value === 'object' && Object.keys(value).length > 0) {
                        displayValue = Object.entries(value)
                            .filter(([k, v]) => v)
                            .map(([k, v]) => `<strong>${k}:</strong> ${this.escapeHtml(v)}`)
                            .join('<br>');
                    } else {
                        displayValue = 'Not available';
                    }
                } else {
                    displayValue = this.formatFieldValue(value);
                }
                
                const isEmpty = this.isFieldEmpty(value);
                
                fieldsHtml += `
                    <div class="field-item" ${field.isLongText ? 'style="grid-column: 1 / -1;"' : ''}>
                        <div class="field-label">${field.label}</div>
                        <div class="field-value ${isEmpty ? 'field-empty' : ''}">
                            ${displayValue}
                        </div>
                    </div>
                `;
            });
        });
        
        return fieldsHtml;
    }
    
    formatFieldValue(value) {
        if (this.isFieldEmpty(value)) {
            return 'Not available';
        }
        
        if (Array.isArray(value)) {
            return value.length > 0 ? value.join(', ') : 'Not available';
        }
        
        if (typeof value === 'object') {
            const entries = Object.entries(value).filter(([k, v]) => v);
            return entries.length > 0 ? 
                entries.map(([k, v]) => `${k}: ${v}`).join('<br>') : 
                'Not available';
        }
        
        if (typeof value === 'boolean') {
            return value ? 'Yes' : 'No';
        }
        
        return this.escapeHtml(String(value));
    }
    
    isFieldEmpty(value) {
        return value === null || 
               value === undefined || 
               value === '' || 
               (Array.isArray(value) && value.length === 0) ||
               (typeof value === 'object' && Object.keys(value).length === 0);
    }
    
    setupModalEventListeners(companyName, researchData) {
        // Close modal when clicking outside
        const modal = document.getElementById('researchModal');
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeResearchModal();
            }
        });
        
        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeResearchModal();
            }
        });
    }
    
    closeResearchModal() {
        const modal = document.getElementById('researchModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    async saveToIndex(companyName, buttonElement) {
        // Show saving state
        const saveBtn = buttonElement || document.querySelector('.btn-save');
        const originalText = saveBtn.innerHTML;
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<div class="loading-spinner"></div> Adding to Index...';
        
        try {
            // Get the research data for this company
            let researchData = null;
            
            // Find the research data in our stored data
            if (this.researchDataStore) {
                for (const [companyId, data] of this.researchDataStore.entries()) {
                    if (data.company_name === companyName || data.name === companyName) {
                        researchData = data;
                        console.log('📋 Found research data for indexing:', researchData);
                        break;
                    }
                }
            }
            
            // Call backend to save to Pinecone
            const requestBody = {
                company_name: companyName
            };
            
            // Include research data if we have it
            if (researchData) {
                requestBody.research_data = researchData;
                console.log('📤 Sending research data to backend for indexing');
            } else {
                console.log('⚠️ No research data found in store, backend will try to find it');
            }
            
            const response = await fetch('/api/v2/save-to-index', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('✅ Successfully added to index:', result);
                this.showMessage(
                    `${companyName} added to index! (${result.fields_saved || 'Multiple'} fields saved)`, 
                    'success'
                );
                this.closeResearchModal();
                
                // Update button text to show it's been added
                if (saveBtn.parentNode) {
                    saveBtn.innerHTML = '✅ Added to Index';
                    saveBtn.disabled = true;
                    saveBtn.style.background = 'rgba(40, 167, 69, 0.8)';
                }
                
                // Hide the "View Research" button now that data is in index
                this.hideViewResearchButton(companyName);
            } else {
                console.error('❌ Failed to add to index:', result.error);
                this.showMessage(`Failed to add ${companyName} to index: ${result.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Save to index error:', error);
            this.showMessage(`Failed to add ${companyName} to index: ${error.message}`, 'error');
        } finally {
            // Reset button state if there was an error
            if (!saveBtn.innerHTML.includes('✅')) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = originalText;
            }
        }
    }
    
    handleTabSwitch(event) {
        const targetTab = event.target.getAttribute('data-tab');
        
        // Remove active class from all tabs and content
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        // Add active class to clicked tab and corresponding content
        event.target.classList.add('active');
        const targetContent = document.getElementById(targetTab);
        if (targetContent) {
            targetContent.classList.add('active');
        }
        
        // Load data for specific tabs
        if (targetTab === 'databaseTab') {
            this.loadDatabaseBrowser();
        }
        
        console.log(`📋 Switched to tab: ${targetTab}`);
    }
    
    async loadDatabaseBrowser() {
        console.log('🗄️ Loading database browser...');
        console.log('🔍 DEBUG: loadDatabaseBrowser called');
        
        const tableContainer = document.getElementById('companiesTable');
        const totalElement = document.getElementById('totalCompanies');
        const lastUpdatedElement = document.getElementById('lastUpdated');
        
        // Show loading state
        if (tableContainer) {
            tableContainer.innerHTML = '<div class="loading">Loading companies from Pinecone index...</div>';
        }
        if (totalElement) {
            totalElement.textContent = 'Loading...';
        }
        if (lastUpdatedElement) {
            lastUpdatedElement.textContent = 'Loading...';
        }
        
        try {
            const response = await fetch('/api/database');
            const data = await response.json();

            if (response.ok && data.success) {
                console.log('✅ Database loaded:', data);
                console.log(`🔍 DEBUG: Found ${data.companies?.length || 0} companies`);
                this.updateDatabaseStats(data);
                this.updateCompaniesTable(data.companies);
            } else {
                console.error('❌ Database load failed:', data.error);
                this.showDatabaseError(data.error || 'Failed to load database');
            }
            
        } catch (error) {
            console.error('❌ Database load error:', error);
            this.showDatabaseError('Network error loading database');
        }
    }
    
    updateDatabaseStats(data) {
        const totalElement = document.getElementById('totalCompanies');
        const lastUpdatedElement = document.getElementById('lastUpdated');
        
        if (totalElement) {
            totalElement.textContent = data.total_companies || 0;
        }
        
        if (lastUpdatedElement) {
            const timestamp = data.timestamp ? new Date(data.timestamp).toLocaleString() : 'Unknown';
            lastUpdatedElement.textContent = timestamp;
        }
    }
    
    updateCompaniesTable(companies) {
        const tableContainer = document.getElementById('companiesTable');
        console.log(`🔍 DEBUG: updateCompaniesTable called with ${companies?.length || 0} companies`);
        
        if (!companies || companies.length === 0) {
            console.log('⚠️ DEBUG: No companies to display');
            tableContainer.innerHTML = '<div class="loading">No companies found in the index.</div>';
            return;
        }
        
        // Store companies data for details modal
        this.companiesData = companies;
        
        const tableHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Company</th>
                        <th>Industry</th>
                        <th>Stage</th>
                        <th>Tech Level</th>
                        <th>Business Model</th>
                        <th>Size</th>
                        <th>Website</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${companies.map((company, index) => `
                        <tr>
                            <td>
                                <strong>${this.escapeHtml(company.name)}</strong>
                            </td>
                            <td>${this.escapeHtml(company.industry || 'Unknown')}</td>
                            <td>
                                <span class="company-stage stage-${(company.stage || 'unknown').toLowerCase()}">
                                    ${this.escapeHtml(company.stage || 'Unknown')}
                                </span>
                            </td>
                            <td>${this.escapeHtml(company.tech_level || 'Unknown')}</td>
                            <td>${this.escapeHtml(company.business_model || 'Unknown')}</td>
                            <td>${this.escapeHtml(company.company_size || 'Unknown')}</td>
                            <td>
                                ${company.website && company.website !== 'Unknown' ? 
                                    `<a href="${this.escapeHtml(company.website)}" target="_blank" class="company-website">
                                        ${this.escapeHtml(this.shortenWebsiteUrl(company.website))}
                                    </a>` : 
                                    'N/A'
                                }
                            </td>
                            <td>
                                <button class="btn-details" onclick="theodoreV2.showCompanyDetails(${index})">
                                    <span>👁️</span>
                                    View Details
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        tableContainer.innerHTML = tableHTML;
    }
    
    showDatabaseError(error) {
        const tableContainer = document.getElementById('companiesTable');
        if (tableContainer) {
            tableContainer.innerHTML = `
                <div class="loading" style="color: #ff6b6b;">
                    ❌ Error loading database: ${this.escapeHtml(error)}
                </div>
            `;
        }
    }
    
    async refreshDatabase() {
        console.log('🔄 Refreshing database...');
        await this.loadDatabaseBrowser();
        this.showMessage('Database refreshed successfully!', 'success');
    }
    
    async exportDatabase() {
        console.log('📥 Exporting database...');
        try {
            const response = await fetch('/api/database');
            const data = await response.json();
            
            if (response.ok && data.success) {
                // Create and download JSON file
                const dataStr = JSON.stringify(data, null, 2);
                const dataBlob = new Blob([dataStr], {type: 'application/json'});
                const url = URL.createObjectURL(dataBlob);
                
                const link = document.createElement('a');
                link.href = url;
                link.download = `theodore-database-${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
                
                this.showMessage(`Exported ${data.total_companies} companies successfully!`, 'success');
            } else {
                this.showMessage('Failed to export database', 'error');
            }
        } catch (error) {
            console.error('Export error:', error);
            this.showMessage('Failed to export database', 'error');
        }
    }
    
    shortenWebsiteUrl(url) {
        try {
            const urlObj = new URL(url);
            return urlObj.hostname.replace('www.', '');
        } catch (e) {
            return url;
        }
    }
    
    async showCompanyDetails(companyIndex) {
        console.log('🔍 Showing company details for index:', companyIndex);
        
        if (!this.companiesData || !this.companiesData[companyIndex]) {
            this.showMessage('Company data not found', 'error');
            return;
        }
        
        const company = this.companiesData[companyIndex];
        console.log('📋 Company data:', company);
        
        try {
            // Fetch detailed company data from backend
            const response = await fetch(`/api/company/${company.id}`);
            const result = await response.json();
            
            if (response.ok && result.success) {
                // Use the detailed company data
                this.openCompanyDetailsModal(company.name, result.company);
            } else {
                // Fallback to basic data from table
                console.log('⚠️ Could not fetch detailed data, using table data');
                this.openCompanyDetailsModal(company.name, company);
            }
        } catch (error) {
            console.error('❌ Error fetching company details:', error);
            // Fallback to basic data from table
            this.openCompanyDetailsModal(company.name, company);
        }
    }
    
    openCompanyDetailsModal(companyName, companyData) {
        console.log('🔍 Opening details modal for:', companyName);
        console.log('📊 Company data keys:', Object.keys(companyData));
        
        const modal = document.getElementById('researchModal');
        if (!modal) {
            console.error('❌ Research modal not found');
            return;
        }
        
        console.log('✅ Modal element found:', modal);
        
        // Build modal content using the same structure as research modal but for stored data
        const modalContent = this.buildCompanyDetailsModalContent(companyName, companyData);
        console.log('📝 Modal content length:', modalContent.length);
        modal.innerHTML = modalContent;
        
        console.log('🎭 Setting modal display to flex...');
        
        // Move modal to body if it's not already there (common modal issue)
        if (modal.parentElement !== document.body) {
            console.log('📍 Moving modal to body level...');
            document.body.appendChild(modal);
        }
        
        // Show modal with explicit styles for debugging
        modal.style.display = 'flex';
        modal.style.position = 'fixed';
        modal.style.top = '0';
        modal.style.left = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        modal.style.zIndex = '9999';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';
        
        console.log('🎭 Modal styles after setting:', {
            display: modal.style.display,
            position: getComputedStyle(modal).position,
            zIndex: getComputedStyle(modal).zIndex,
            backgroundColor: modal.style.backgroundColor
        });
        
        // Add event listeners
        this.setupDetailsModalEventListeners(companyName, companyData);
    }
    
    buildCompanyDetailsModalContent(companyName, companyData) {
        // Calculate completion stats
        const completionStats = this.calculateCompanyDataCompletionStats(companyData);
        
        return `
            <div class="research-modal-content">
                <div class="research-modal-header">
                    <h2 class="research-modal-title">Company Details: ${this.escapeHtml(companyName)}</h2>
                    <button class="research-modal-close" onclick="theodoreV2.closeResearchModal()">
                        ×
                    </button>
                </div>
                
                <div class="research-modal-body">
                    <!-- Completion Stats -->
                    <div class="completion-stats">
                        <div class="completion-percentage">${completionStats.percentage}%</div>
                        <div class="completion-label">
                            ${completionStats.completed} of ${completionStats.total} fields populated
                        </div>
                    </div>
                    
                    <!-- Company Data Fields -->
                    <div class="field-grid">
                        ${this.buildCompanyDetailsFieldItems(companyData)}
                    </div>
                </div>
                
                <div class="modal-actions">
                    <button class="btn-cancel" onclick="theodoreV2.closeResearchModal()">
                        Close
                    </button>
                    <button class="btn-export" onclick="theodoreV2.exportCompanyData('${this.escapeJs(companyName)}')">
                        📥 Export Data
                    </button>
                </div>
            </div>
        `;
    }
    
    calculateCompanyDataCompletionStats(companyData) {
        // IMPORTANT: Use the SAME field list as calculateCompletionStats() to ensure consistency
        const allFields = [
            'company_name', 'website', 'industry', 'business_model', 'company_size',
            'tech_stack', 'has_chat_widget', 'has_forms', 'pain_points', 'key_services',
            'competitive_advantages', 'target_market', 'company_description', 'value_proposition',
            'founding_year', 'location', 'employee_count_range', 'company_culture',
            'funding_status', 'social_media', 'contact_info', 'leadership_team',
            'recent_news', 'certifications', 'partnerships', 'awards', 'company_stage',
            'tech_sophistication', 'geographic_scope', 'business_model_type',
            'decision_maker_type', 'sales_complexity', 'ai_summary',
            // Batch Research Intelligence fields
            'has_job_listings', 'job_listings_count', 'job_listings_details',
            'products_services_offered', 'key_decision_makers', 'funding_stage_detailed',
            'sales_marketing_tools', 'recent_news_events'
        ];
        
        console.log('🔍 DEBUG: Database completion calculation for', companyData.name || companyData.company_name);
        console.log('🔍 DEBUG: Available fields in companyData:', Object.keys(companyData).sort());
        
        let completed = 0;
        let populatedFields = [];
        let missingFields = [];
        
        allFields.forEach(field => {
            // Handle field name mapping for consistency (database uses 'name' vs 'company_name')
            let fieldToCheck = field;
            if (field === 'company_name' && !companyData.company_name && companyData.name) {
                fieldToCheck = 'name';
            }
            
            const value = companyData[fieldToCheck];
            
            let isPopulated = false;
            
            if (value === null || value === undefined || value === 'Unknown') {
                isPopulated = false;
            } else if (typeof value === 'string') {
                isPopulated = value.trim() !== '';
            } else if (Array.isArray(value)) {
                isPopulated = value.length > 0;
            } else if (typeof value === 'object') {
                // For objects, check if they have meaningful content
                const keys = Object.keys(value);
                isPopulated = keys.length > 0 && keys.some(key => {
                    const objValue = value[key];
                    return objValue !== null && objValue !== undefined && objValue !== '' && objValue !== 'Unknown';
                });
                
                // Debug object content for fields that show [object Object]
                if (fieldToCheck === 'social_media' || fieldToCheck === 'contact_info' || fieldToCheck === 'key_decision_makers') {
                    console.log(`🔍 DEBUG OBJECT ${fieldToCheck}:`, JSON.stringify(value, null, 2));
                    console.log(`🔍 DEBUG OBJECT ${fieldToCheck} keys:`, keys);
                    console.log(`🔍 DEBUG OBJECT ${fieldToCheck} isPopulated:`, isPopulated);
                }
            } else if (typeof value === 'boolean') {
                isPopulated = true; // Booleans are always considered populated
            } else if (typeof value === 'number') {
                isPopulated = !isNaN(value);
            } else {
                isPopulated = !!value;
            }
                
            if (isPopulated) {
                completed++;
                populatedFields.push(fieldToCheck);
            } else {
                missingFields.push(`${fieldToCheck} (${typeof value}: "${value}")`);
            }
        });
        
        console.log('🔍 DEBUG: Populated fields (' + completed + '):', populatedFields);
        console.log('🔍 DEBUG: Missing fields (' + missingFields.length + '):', missingFields);
        
        const percentage = Math.round((completed / allFields.length) * 100);
        
        return {
            completed,
            total: allFields.length,
            percentage
        };
    }
    
    buildCompanyDetailsFieldItems(companyData) {
        // Organized field categories for company details
        const fieldCategories = {
            'Basic Information': [
                { key: 'name', label: 'Company Name' },
                { key: 'website', label: 'Website' },
                { key: 'industry', label: 'Industry' },
                { key: 'business_model', label: 'Business Model' },
                { key: 'company_size', label: 'Company Size' },
                { key: 'location', label: 'Location' },
                { key: 'founding_year', label: 'Founded' }
            ],
            'Business Intelligence': [
                { key: 'company_description', label: 'Description', isLongText: true },
                { key: 'sales_intelligence', label: 'Sales Intelligence', isLongText: true },
                { key: 'value_proposition', label: 'Value Proposition' },
                { key: 'target_market', label: 'Target Market' },
                { key: 'key_services', label: 'Key Services' },
                { key: 'competitive_advantages', label: 'Competitive Advantages' },
                { key: 'pain_points', label: 'Pain Points' }
            ],
            'Technology & Operations': [
                { key: 'tech_stack', label: 'Technology Stack' },
                { key: 'has_chat_widget', label: 'Has Chat Widget' },
                { key: 'has_forms', label: 'Has Lead Forms' },
                { key: 'tech_sophistication', label: 'Tech Sophistication' }
            ],
            'Company Metrics': [
                { key: 'employee_count_range', label: 'Employee Count' },
                { key: 'company_culture', label: 'Company Culture' },
                { key: 'funding_status', label: 'Funding Status' },
                { key: 'company_stage', label: 'Company Stage' },
                { key: 'geographic_scope', label: 'Geographic Scope' },
                { key: 'business_model_type', label: 'Business Model Type' },
                { key: 'decision_maker_type', label: 'Decision Maker Type' },
                { key: 'sales_complexity', label: 'Sales Complexity' }
            ],
            'Contacts & Social': [
                { key: 'leadership_team', label: 'Leadership Team' },
                { key: 'contact_info', label: 'Contact Information', isObject: true },
                { key: 'social_media', label: 'Social Media', isObject: true }
            ],
            'Job Listings & Hiring': [
                { key: 'has_job_listings', label: 'Has Job Listings' },
                { key: 'job_listings_count', label: 'Job Openings Count' },
                { key: 'job_listings_details', label: 'Job Listings Details', isSpecial: true }
            ],
            'Additional Intelligence': [
                { key: 'recent_news', label: 'Recent News' },
                { key: 'certifications', label: 'Certifications' },
                { key: 'partnerships', label: 'Partnerships' },
                { key: 'awards', label: 'Awards' },
                { key: 'ai_summary', label: 'AI Summary', isLongText: true }
            ]
        };
        
        let fieldsHtml = '';
        
        Object.entries(fieldCategories).forEach(([category, fields]) => {
            fieldsHtml += `<div class="field-item" style="grid-column: 1 / -1;"><h4 style="margin: 0; color: var(--primary-color);">${category}</h4></div>`;
            
            fields.forEach(field => {
                const value = companyData[field.key];
                let displayValue;
                
                if (field.isSpecial && field.key === 'job_listings_details') {
                    // Special formatting for job listings
                    if (Array.isArray(value) && value.length > 0) {
                        displayValue = value.map(job => 
                            `<div style="margin-bottom: 12px; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                                <strong>${job.title || 'Job Title'}</strong>
                                <br><small style="color: var(--text-muted);">Department: ${job.department || 'N/A'}</small>
                                <br><small style="color: var(--text-muted);">Location: ${job.location || 'N/A'}</small>
                            </div>`
                        ).join('');
                    } else {
                        displayValue = 'No job listings available';
                    }
                } else if (field.isLongText) {
                    // Special formatting for long text
                    displayValue = value ? 
                        `<div style="max-height: 200px; overflow-y: auto; white-space: pre-wrap; font-family: inherit;">${this.escapeHtml(value)}</div>` : 
                        'Not available';
                } else if (field.isObject) {
                    // Special formatting for object fields
                    if (value && typeof value === 'object' && Object.keys(value).length > 0) {
                        displayValue = Object.entries(value)
                            .filter(([k, v]) => v)
                            .map(([k, v]) => `<strong>${k}:</strong> ${this.escapeHtml(v)}`)
                            .join('<br>');
                    } else {
                        displayValue = 'Not available';
                    }
                } else {
                    displayValue = this.formatFieldValue(value);
                }
                
                const isEmpty = this.isFieldEmpty(value);
                
                fieldsHtml += `
                    <div class="field-item" ${field.isLongText ? 'style="grid-column: 1 / -1;"' : ''}>
                        <div class="field-label">${field.label}</div>
                        <div class="field-value ${isEmpty ? 'field-empty' : ''}">
                            ${displayValue}
                        </div>
                    </div>
                `;
            });
        });
        
        return fieldsHtml;
    }
    
    setupDetailsModalEventListeners(companyName, companyData) {
        // Close modal when clicking outside
        const modal = document.getElementById('researchModal');
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeResearchModal();
            }
        });
        
        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeResearchModal();
            }
        });
    }
    
    exportCompanyData(companyName) {
        console.log('📥 Exporting company data for:', companyName);
        
        // Find the company data
        const company = this.companiesData?.find(c => c.name === companyName);
        if (!company) {
            this.showMessage('Company data not found for export', 'error');
            return;
        }
        
        try {
            // Create and download JSON file
            const dataStr = JSON.stringify(company, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            const url = URL.createObjectURL(dataBlob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `${companyName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}-data.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            this.showMessage(`Exported ${companyName} data successfully!`, 'success');
        } catch (error) {
            console.error('Export error:', error);
            this.showMessage('Failed to export company data', 'error');
        }
    }
}

// Global functions
function researchThisCompany() {
    const inputText = document.getElementById('companyInput').value.trim();
    if (!inputText) {
        theodoreV2.showMessage('Please enter a company name or website URL first', 'warning');
        return;
    }
    
    console.log(`🔬 Research This Company clicked for: ${inputText}`);
    
    // Use the same research flow as the primary company card
    const companyId = 'main-input-company';
    let companyName = inputText;
    let websiteUrl = '';
    
    // Check if input is a URL
    if (inputText.startsWith('http://') || inputText.startsWith('https://') || inputText.includes('.')) {
        websiteUrl = inputText.startsWith('http') ? inputText : `https://${inputText}`;
        // Extract company name from URL (simple approach)
        try {
            const domain = new URL(websiteUrl).hostname.replace('www.', '');
            companyName = domain.split('.')[0];
        } catch (e) {
            companyName = inputText;
        }
    } else {
        // If it's just a company name, we'll let the backend handle finding the website
        websiteUrl = `https://${inputText.toLowerCase().replace(/\s+/g, '')}.com`;
    }
    
    // Show the research section
    document.getElementById('mainResearchSection').style.display = 'block';
    
    // Start the research
    theodoreV2.startResearch(companyId, companyName, websiteUrl);
}

function clearDiscovery() {
    document.getElementById('discoveryForm').reset();
    document.getElementById('inputTypeIndicator').style.display = 'none';
    document.getElementById('discoveryResults').style.display = 'none';
    document.getElementById('mainResearchSection').style.display = 'none';
    document.getElementById('messages').innerHTML = '';
}

function startBatchProcessing() {
    // Placeholder function for batch processing
    alert('Batch Processing feature coming soon!\n\nThis will allow you to:\n• Upload CSV or connect Google Sheets\n• Enrich up to 1,000 companies\n• Extract job listings, funding stage, key personnel\n• Get cost estimates before running');
}

// Initialize V2 UI
const theodoreV2 = new TheodoreV2UI();

// Debug info
console.log('🚀 Theodore V2 UI loaded successfully');
console.log('✨ Features: URL detection, fast discovery, focused research');