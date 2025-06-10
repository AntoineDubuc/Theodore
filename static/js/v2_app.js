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
        
        result.similar_companies.forEach((company, index) => {
            const card = this.createCompanyCard(company, index);
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

        // Update UI
        const button = document.querySelector(`#${companyId}-progress`).previousElementSibling.querySelector('.btn-research');
        const progressDiv = document.getElementById(`${companyId}-progress`);
        const resultsDiv = document.getElementById(`${companyId}-results`);
        const progressText = document.getElementById(`${companyId}-progress-text`);

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
        // Reset button and hide progress
        const button = document.querySelector(`#${companyId}-progress`).previousElementSibling.querySelector('.btn-research');
        const progressDiv = document.getElementById(`${companyId}-progress`);
        
        button.disabled = false;
        button.innerHTML = '<span>🔬</span> Research Now';
        progressDiv.style.display = 'none';
        
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
        return text.replace(/\\/g, '\\\\')
                  .replace(/'/g, "\\'")
                  .replace(/"/g, '\\"')
                  .replace(/\n/g, '\\n')
                  .replace(/\r/g, '\\r')
                  .replace(/\t/g, '\\t');
    }
}

// Global functions
function clearDiscovery() {
    document.getElementById('discoveryForm').reset();
    document.getElementById('inputTypeIndicator').style.display = 'none';
    document.getElementById('discoveryResults').style.display = 'none';
    document.getElementById('messages').innerHTML = '';
}

// Initialize V2 UI
const theodoreV2 = new TheodoreV2UI();

// Debug info
console.log('🚀 Theodore V2 UI loaded successfully');
console.log('✨ Features: URL detection, fast discovery, focused research');