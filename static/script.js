// JavaScript for Marksheet Extraction API Demo

class MarksheetExtractor {
    constructor() {
        this.apiBaseUrl = '/api';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupFormValidation();
    }

    setupEventListeners() {
        // Single file upload
        document.getElementById('uploadForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSingleUpload();
        });

        // Batch file upload
        document.getElementById('batchUploadForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleBatchUpload();
        });

        // Copy JSON button
        document.getElementById('copyJsonBtn').addEventListener('click', () => {
            this.copyJsonToClipboard();
        });

        // Download JSON button
        document.getElementById('downloadJsonBtn').addEventListener('click', () => {
            this.downloadJson();
        });

        // File input change handlers
        document.getElementById('fileInput').addEventListener('change', (e) => {
            this.validateSingleFile(e.target.files[0]);
        });

        document.getElementById('batchFileInput').addEventListener('change', (e) => {
            this.validateBatchFiles(e.target.files);
        });
    }

    setupFormValidation() {
        // Add Bootstrap validation classes
        const forms = document.querySelectorAll('.needs-validation');
        Array.from(forms).forEach(form => {
            form.addEventListener('submit', (event) => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    }

    validateSingleFile(file) {
        if (!file) return;

        const maxSize = 10 * 1024 * 1024; // 10MB
        const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf'];
        
        if (file.size > maxSize) {
            this.showError('File size exceeds 10MB limit');
            return false;
        }

        if (!allowedTypes.includes(file.type)) {
            this.showError('Unsupported file type. Please use JPG, PNG, or PDF');
            return false;
        }

        return true;
    }

    validateBatchFiles(files) {
        if (!files || files.length === 0) return;

        if (files.length > 5) {
            this.showError('Maximum 5 files allowed for batch processing');
            return false;
        }

        for (let file of files) {
            if (!this.validateSingleFile(file)) {
                return false;
            }
        }

        return true;
    }

    async handleSingleUpload() {
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];

        if (!file || !this.validateSingleFile(file)) {
            return;
        }

        this.showProgress('Extracting data from marksheet...');
        this.hideResults();
        this.hideError();

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${this.apiBaseUrl}/extract`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Extraction failed');
            }

            const result = await response.json();
            this.hideProgress();
            this.showResults([result]);

        } catch (error) {
            this.hideProgress();
            this.showError(`Extraction failed: ${error.message}`);
        }
    }

    async handleBatchUpload() {
        const fileInput = document.getElementById('batchFileInput');
        const files = fileInput.files;

        if (!files || files.length === 0 || !this.validateBatchFiles(files)) {
            return;
        }

        this.showProgress(`Processing ${files.length} files...`);
        this.hideResults();
        this.hideError();

        try {
            const formData = new FormData();
            for (let file of files) {
                formData.append('files', file);
            }

            const response = await fetch(`${this.apiBaseUrl}/batch-extract`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Batch extraction failed');
            }

            const results = await response.json();
            this.hideProgress();
            this.showResults(results);

        } catch (error) {
            this.hideProgress();
            this.showError(`Batch extraction failed: ${error.message}`);
        }
    }

    showProgress(message) {
        document.getElementById('progressText').textContent = message;
        document.getElementById('progressSection').style.display = 'block';
    }

    hideProgress() {
        document.getElementById('progressSection').style.display = 'none';
    }

    showResults(results) {
        const resultsContent = document.getElementById('resultsContent');
        
        if (Array.isArray(results) && results.length > 1) {
            // Multiple results (batch processing)
            resultsContent.innerHTML = this.renderBatchResults(results);
        } else {
            // Single result
            const result = Array.isArray(results) ? results[0] : results;
            resultsContent.innerHTML = this.renderSingleResult(result);
        }

        document.getElementById('resultsSection').style.display = 'block';
        this.currentResults = results;
    }

    hideResults() {
        document.getElementById('resultsSection').style.display = 'none';
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorSection').style.display = 'block';
    }

    hideError() {
        document.getElementById('errorSection').style.display = 'none';
    }

    renderSingleResult(result) {
        return `
            <div class="fade-in">
                ${this.renderCandidateDetails(result.candidate_details)}
                ${this.renderSubjects(result.subjects)}
                ${this.renderOverallResult(result.overall_result)}
                ${this.renderDocumentInfo(result.document_info)}
                ${this.renderMetadata(result.metadata)}
                ${this.renderJsonView(result)}
            </div>
        `;
    }

    renderBatchResults(results) {
        let html = '<div class="fade-in">';
        
        results.forEach((result, index) => {
            html += `
                <div class="card mb-3">
                    <div class="card-header">
                        <h6 class="mb-0">
                            <i class="fas fa-file-alt"></i> 
                            File ${index + 1}: ${result.metadata.file_name}
                            ${this.renderConfidenceBadge(result.metadata.overall_confidence)}
                        </h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                ${this.renderCandidateDetails(result.candidate_details)}
                            </div>
                            <div class="col-md-6">
                                ${this.renderSubjects(result.subjects)}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }

    renderCandidateDetails(details) {
        return `
            <div class="result-section">
                <h6><i class="fas fa-user"></i> Candidate Details ${this.renderConfidenceBadge(details.confidence)}</h6>
                <div class="row">
                    <div class="col-md-6">
                        <div class="metadata-item">
                            <span class="metadata-label">Name:</span>
                            <span class="metadata-value">${details.name || 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="metadata-label">Father's Name:</span>
                            <span class="metadata-value">${details.father_name || 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="metadata-label">Mother's Name:</span>
                            <span class="metadata-value">${details.mother_name || 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="metadata-label">Date of Birth:</span>
                            <span class="metadata-value">${details.date_of_birth || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="metadata-item">
                            <span class="metadata-label">Roll No:</span>
                            <span class="metadata-value">${details.roll_no || 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="metadata-label">Registration No:</span>
                            <span class="metadata-value">${details.registration_no || 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="metadata-label">Exam Year:</span>
                            <span class="metadata-value">${details.exam_year || 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="metadata-label">Board/University:</span>
                            <span class="metadata-value">${details.board_university || 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="metadata-label">Institution:</span>
                            <span class="metadata-value">${details.institution || 'N/A'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderSubjects(subjects) {
        if (!subjects || subjects.length === 0) {
            return `
                <div class="result-section">
                    <h6><i class="fas fa-book"></i> Subjects</h6>
                    <p class="text-muted">No subject data found</p>
                </div>
            `;
        }

        let tableRows = subjects.map(subject => `
            <tr>
                <td>${subject.subject || 'N/A'}</td>
                <td class="text-center">${subject.max_marks || 'N/A'}</td>
                <td class="text-center">${subject.obtained_marks || 'N/A'}</td>
                <td class="text-center">${subject.grade || 'N/A'}</td>
                <td class="text-center">${this.renderConfidenceBadge(subject.confidence)}</td>
            </tr>
        `).join('');

        return `
            <div class="result-section">
                <h6><i class="fas fa-book"></i> Subjects (${subjects.length})</h6>
                <div class="table-responsive">
                    <table class="table table-sm subject-table">
                        <thead>
                            <tr>
                                <th>Subject</th>
                                <th class="text-center">Max Marks</th>
                                <th class="text-center">Obtained</th>
                                <th class="text-center">Grade</th>
                                <th class="text-center">Confidence</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${tableRows}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    renderOverallResult(result) {
        return `
            <div class="result-section">
                <h6><i class="fas fa-trophy"></i> Overall Result ${this.renderConfidenceBadge(result.confidence)}</h6>
                <div class="row">
                    <div class="col-md-6">
                        <div class="metadata-item">
                            <span class="metadata-label">Result:</span>
                            <span class="metadata-value">${result.result || 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="metadata-label">Grade:</span>
                            <span class="metadata-value">${result.grade || 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="metadata-label">Division:</span>
                            <span class="metadata-value">${result.division || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="metadata-item">
                            <span class="metadata-label">Percentage:</span>
                            <span class="metadata-value">${result.percentage ? `${result.percentage}%` : 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="metadata-label">CGPA:</span>
                            <span class="metadata-value">${result.cgpa || 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="metadata-label">Total Marks:</span>
                            <span class="metadata-value">${result.total_marks ? `${result.total_marks}/${result.max_total_marks || '?'}` : 'N/A'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderDocumentInfo(docInfo) {
        return `
            <div class="result-section">
                <h6><i class="fas fa-file-alt"></i> Document Information ${this.renderConfidenceBadge(docInfo.confidence)}</h6>
                <div class="row">
                    <div class="col-md-4">
                        <div class="metadata-item">
                            <span class="metadata-label">Document Type:</span>
                            <span class="metadata-value">${docInfo.document_type || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="metadata-item">
                            <span class="metadata-label">Issue Date:</span>
                            <span class="metadata-value">${docInfo.issue_date || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="metadata-item">
                            <span class="metadata-label">Issue Place:</span>
                            <span class="metadata-value">${docInfo.issue_place || 'N/A'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderMetadata(metadata) {
        return `
            <div class="result-section">
                <h6><i class="fas fa-info-circle"></i> Processing Metadata ${this.renderConfidenceBadge(metadata.overall_confidence)}</h6>
                <div class="row">
                    <div class="col-md-6">
                        <div class="metadata-item">
                            <span class="metadata-label">Processing Time:</span>
                            <span class="metadata-value">${metadata.processing_time.toFixed(2)}s</span>
                        </div>
                        <div class="metadata-item">
                            <span class="metadata-label">Extraction Method:</span>
                            <span class="metadata-value">${metadata.extraction_method}</span>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="metadata-item">
                            <span class="metadata-label">Text Length:</span>
                            <span class="metadata-value">${metadata.text_length} chars</span>
                        </div>
                        <div class="metadata-item">
                            <span class="metadata-label">Confidence Explanation:</span>
                            <span class="metadata-value"><small>${metadata.confidence_explanation}</small></span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderJsonView(result) {
        return `
            <div class="result-section">
                <h6><i class="fas fa-code"></i> Raw JSON Data</h6>
                <pre class="json-display"><code>${JSON.stringify(result, null, 2)}</code></pre>
            </div>
        `;
    }

    renderConfidenceBadge(confidence) {
        const percentage = Math.round(confidence * 100);
        let badgeClass = 'confidence-low';
        
        if (confidence >= 0.8) {
            badgeClass = 'confidence-high';
        } else if (confidence >= 0.6) {
            badgeClass = 'confidence-medium';
        }

        return `<span class="badge confidence-badge ${badgeClass}">${percentage}%</span>`;
    }

    copyJsonToClipboard() {
        if (!this.currentResults) return;

        const jsonText = JSON.stringify(this.currentResults, null, 2);
        
        navigator.clipboard.writeText(jsonText).then(() => {
            // Show success message
            const btn = document.getElementById('copyJsonBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
            btn.classList.add('btn-success');
            btn.classList.remove('btn-outline-primary');
            
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.classList.remove('btn-success');
                btn.classList.add('btn-outline-primary');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy JSON:', err);
            this.showError('Failed to copy JSON to clipboard');
        });
    }

    downloadJson() {
        if (!this.currentResults) return;

        const jsonText = JSON.stringify(this.currentResults, null, 2);
        const blob = new Blob([jsonText], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `marksheet-extraction-${new Date().getTime()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MarksheetExtractor();
});
