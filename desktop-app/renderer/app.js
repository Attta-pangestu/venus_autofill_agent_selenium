// Venus AutoFill Desktop App - Main Application Logic

class VenusAutoFillApp {
    constructor() {
        this.stagingData = [];
        this.filteredData = [];
        this.selectedIds = new Set();
        this.currentView = 'table'; // 'table' or 'cards'
        this.activeFilters = {
            dateFrom: '',
            dateTo: '',
            status: '',
            search: ''
        };
        this.automationStatus = {
            isRunning: false,
            progress: 0,
            currentItem: null,
            processed: 0,
            total: 0
        };
        this.browserStatus = {
            isInitialized: false,
            isInitializing: false
        };
        this.settings = {
            flaskServerUrl: 'http://localhost:5000',
            autoRefresh: true,
            refreshInterval: 30000,
            autoLaunchBrowser: true
        };
        this.refreshTimer = null;
        this.statusTimer = null;
        
        this.init();
    }

    async init() {
        console.log('Initializing Venus AutoFill Desktop App...');
        
        // Load settings
        await this.loadSettings();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Setup startup event listeners for automatic data loading and browser initialization
        this.setupStartupEventListeners();
        
        // Show startup status
        this.showStartupStatus();
        
        // Initialize view
        this.switchView('table');
        
        // Start auto-refresh if enabled (will be activated after initial data load)
        if (this.settings.autoRefresh) {
            // Auto-refresh will be started after initial data is loaded
            console.log('Auto-refresh will be enabled after startup sequence');
        }
        
        console.log('App initialized successfully - waiting for startup sequence...');
    }

    setupEventListeners() {
        // Data refresh
        document.getElementById('refresh-data').addEventListener('click', () => this.refreshData());
        
        // Grouped data refresh
        document.getElementById('refresh-grouped-btn').addEventListener('click', () => {
            this.refreshGroupedData();
        });
        
        // Browser initialization
        document.getElementById('init-browser').addEventListener('click', () => this.initializeBrowser());
        
        // Automation controls
        document.getElementById('start-automation').addEventListener('click', () => this.startAutomation());
        document.getElementById('stop-automation').addEventListener('click', () => this.stopAutomation());
        
        // Selection controls
        document.getElementById('select-all').addEventListener('click', () => this.selectAll());
        document.getElementById('clear-selection').addEventListener('click', () => this.clearSelection());
        document.getElementById('master-checkbox').addEventListener('change', (e) => this.toggleAllSelection(e.target.checked));
        
        // Filters
        document.getElementById('date-from').addEventListener('change', () => this.applyFilters());
        document.getElementById('date-to').addEventListener('change', () => this.applyFilters());
        document.getElementById('status-filter').addEventListener('change', () => this.applyFilters());
        document.getElementById('search-text').addEventListener('input', () => this.applyFilters());
        
        // Settings
        document.getElementById('settings-btn').addEventListener('click', () => this.openSettings());
        document.getElementById('save-settings').addEventListener('click', () => this.saveSettings());
        
        // View toggle buttons
        const viewTableBtn = document.getElementById('view-table');
        const viewCardsBtn = document.getElementById('view-cards');
        
        if (viewTableBtn) {
            viewTableBtn.addEventListener('click', () => {
                this.switchView('table');
            });
        }

        if (viewCardsBtn) {
            viewCardsBtn.addEventListener('click', () => {
                this.switchView('cards');
            });
        }
        
        // Filter inputs
        document.getElementById('date-from').addEventListener('change', () => {
            this.applyFilters();
        });

        document.getElementById('date-to').addEventListener('change', () => {
            this.applyFilters();
        });

        document.getElementById('status-filter').addEventListener('change', () => {
            this.applyFilters();
        });

        document.getElementById('search-text').addEventListener('input', () => {
            this.applyFilters();
        });

        // Crosscheck
        document.getElementById('refresh-crosscheck').addEventListener('click', () => this.refreshCrosscheckResults());
    }

    setupStartupEventListeners() {
        // Listen for initial data loading events from main process
        window.electronAPI.onInitialDataLoaded((event, result) => {
            console.log('Initial data loaded event received:', result);
            
            if (result.success) {
                // Handle grouped data from database
                this.groupedData = result.data.data || [];
                this.stagingData = this.flattenGroupedData(this.groupedData);
                this.updateDataTable();
                this.updateStats();
                this.updateConnectionStatus('connected', 'Connected - Database data loaded');
                this.showAlert('success', result.message);
                
                // Start auto-refresh after successful data load
                if (this.settings.autoRefresh) {
                    this.startAutoRefresh();
                }
                
                // Auto-launch browser initialization if enabled in settings
                if (this.settings.autoLaunchBrowser && !this.browserStatus.isInitialized) {
                    console.log('Auto-launching browser initialization...');
                    setTimeout(() => {
                        this.initializeBrowser();
                    }, 2000); // Small delay to let data loading complete
                }
            } else {
                this.updateConnectionStatus('error', 'Failed to load database data');
                this.showAlert('error', result.message || 'Failed to load staging data from database');
            }
        });
        
        // Listen for browser initialization events
        window.electronAPI.onBrowserInitializationStarted(() => {
            console.log('Browser initialization started');
            this.updateBrowserStatus('initializing', 'Preparing WebDriver and navigating to Task Register...');
            this.showAlert('info', 'WebDriver initialization started - preparing browser and navigating to Task Register page...');
            
            // Show loading overlay during browser initialization
            this.showBrowserInitializationLoading();
        });
        
        window.electronAPI.onBrowserInitializationCompleted((event, result) => {
            console.log('Browser initialization completed:', result);
            
            // Hide loading overlay
            this.hideBrowserInitializationLoading();
            
            if (result.success) {
                this.updateBrowserStatus('ready', 'WebDriver ready - Task Register page loaded');
                this.showAlert('success', 'WebDriver is ready! You can now select data to input and start automation.');
                this.browserStatus.isInitialized = true;
                this.browserStatus.isInitializing = false;
            } else {
                this.updateBrowserStatus('error', 'WebDriver initialization failed');
                this.showAlert('danger', `WebDriver initialization failed: ${result.message}`);
                this.browserStatus.isInitialized = false;
                this.browserStatus.isInitializing = false;
            }
            
            this.updateBrowserControls();
        });
    }

    showStartupStatus() {
        // Show startup status in the UI
        this.updateConnectionStatus('processing', 'Connecting to staging API server...');
        this.updateBrowserStatus('waiting', 'Waiting for data to load...');
        this.showAlert('info', 'Application starting up - connecting to staging API server and loading database records...');
    }

    updateConnectionStatus(status, message) {
        const indicator = document.getElementById('connection-indicator');
        const text = document.getElementById('connection-text');
        
        if (indicator && text) {
            indicator.className = `status-indicator status-${status}`;
            text.textContent = message;
        }
    }

    updateBrowserStatus(status, message) {
        const indicator = document.getElementById('browser-status-indicator');
        const text = document.getElementById('browser-status-text');
        
        if (indicator && text) {
            indicator.className = `status-indicator status-${status}`;
            text.textContent = message;
        }
    }

    updateBrowserControls() {
        const initButton = document.getElementById('init-browser');
        const startButton = document.getElementById('start-automation');
        
        if (initButton) {
            if (this.browserStatus.isInitialized) {
                initButton.textContent = 'WebDriver Ready';
                initButton.disabled = true;
                initButton.classList.add('btn-success');
                initButton.classList.remove('btn-primary');
            } else {
                initButton.textContent = 'Initialize WebDriver';
                initButton.disabled = false;
                initButton.classList.add('btn-primary');
                initButton.classList.remove('btn-success');
            }
        }
        
        if (startButton) {
            startButton.disabled = !this.browserStatus.isInitialized;
        }
    }

    showBrowserInitializationLoading() {
        // Create loading overlay if it doesn't exist
        let overlay = document.getElementById('browser-init-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'browser-init-overlay';
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `
                <div class="loading-content">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <h5>Preparing WebDriver</h5>
                    <p class="text-muted">Initializing browser and navigating to Task Register page...</p>
                    <div class="progress mt-3" style="width: 300px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 100%"></div>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'flex';
    }

    hideBrowserInitializationLoading() {
        const overlay = document.getElementById('browser-init-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    async loadSettings() {
        try {
            const result = await window.electronAPI.getSettings();
            this.settings = { ...this.settings, ...result };
            console.log('Settings loaded:', this.settings);
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }

    async checkConnection() {
        const indicator = document.getElementById('connection-indicator');
        const text = document.getElementById('connection-text');
        
        indicator.className = 'status-indicator status-processing';
        text.textContent = 'Checking connection...';
        
        try {
            const result = await window.electronAPI.checkFlaskConnection();
            
            if (result.success) {
                indicator.className = 'status-indicator status-connected';
                text.textContent = 'Connected to Flask server';
                this.showAlert('success', 'Successfully connected to Flask server');
            } else {
                indicator.className = 'status-indicator status-disconnected';
                text.textContent = 'Connection failed';
                this.showAlert('danger', `Connection failed: ${result.error}`);
            }
        } catch (error) {
            indicator.className = 'status-indicator status-error';
            text.textContent = 'Connection error';
            this.showAlert('danger', `Connection error: ${error.message}`);
        }
    }

    async refreshData() {
        const button = document.getElementById('refresh-data');
        const spinner = button.querySelector('.loading-spinner');
        
        button.classList.add('loading');
        spinner.classList.remove('d-none');
        
        try {
            const filters = this.getFilters();
            const result = await window.electronAPI.getStagingData(filters);
            
            if (result.success) {
                this.stagingData = result.data.data || [];
                this.updateDataTable();
                this.updateStats();
                this.showAlert('success', `Data refreshed successfully. ${this.stagingData.length} records loaded.`);
            } else {
                this.showAlert('danger', `Failed to load data: ${result.error}`);
            }
        } catch (error) {
            this.showAlert('danger', `Error loading data: ${error.message}`);
        } finally {
            button.classList.remove('loading');
            spinner.classList.add('d-none');
        }
    }

    async refreshGroupedData() {
        try {
            const filters = this.getFilters();
            const result = await window.electronAPI.getGroupedStagingData(filters);
            
            if (result.success) {
                this.groupedData = result.data || [];
                // Flatten grouped data for display
                this.stagingData = this.flattenGroupedData(this.groupedData);
                this.filteredData = [...this.stagingData]; // Initialize filtered data
                this.applyFilters(); // Apply any existing filters
                this.updateStats();
                this.showAlert('success', `Loaded ${this.stagingData.length} records from ${this.groupedData.length} employees from database`);
            } else {
                this.showAlert('danger', `Failed to load grouped data from database: ${result.error}`);
            }
        } catch (error) {
            this.showAlert('danger', `Error loading grouped data from database: ${error.message}`);
        }
    }

    flattenGroupedData(groupedData) {
        const flattened = [];
        let recordId = 1;
        
        groupedData.forEach(employeeGroup => {
            const identitas = employeeGroup.identitas_karyawan || {};
            const dataPresensi = employeeGroup.data_presensi || [];
            
            dataPresensi.forEach(record => {
                flattened.push({
                    id: recordId++,
                    employee_name: identitas.employee_name || 'Unknown',
                    employee_id_ptrj: identitas.employee_id_ptrj || '',
                    employee_id_venus: identitas.employee_id_venus || '',
                    date: record.date || '',
                    time_in: record.time_in || '',
                    time_out: record.time_out || '',
                    regular_hours: record.regular_hours || 0,
                    overtime_hours: record.overtime_hours || 0,
                    total_hours: record.total_hours || 0,
                    task_code: record.task_code || '',
                    status: record.status || 'staged',
                    is_overtime: record.is_overtime || false,
                    original_data: record
                });
            });
        });
        
        return flattened;
    }

    getFilters() {
        const dateFrom = document.getElementById('date-from');
        const dateTo = document.getElementById('date-to');
        const statusFilter = document.getElementById('status-filter');
        const searchText = document.getElementById('search-text');
        
        this.activeFilters = {
            date_from: dateFrom ? dateFrom.value : '',
            date_to: dateTo ? dateTo.value : '',
            status: statusFilter ? statusFilter.value : '',
            search: searchText ? searchText.value : ''
        };
        
        return this.activeFilters;
    }

    applyFilters() {
        const filters = this.getFilters();
        
        this.filteredData = this.stagingData.filter(item => {
            // Date range filter
            if (filters.date_from && item.date < filters.date_from) return false;
            if (filters.date_to && item.date > filters.date_to) return false;
            
            // Status filter
            if (filters.status && item.status !== filters.status) return false;
            
            // Search filter
            if (filters.search) {
                const searchTerm = filters.search.toLowerCase();
                const searchableText = [
                    item.employee_name,
                    item.employee_id_ptrj,
                    item.employee_id_venus,
                    item.task_code
                ].join(' ').toLowerCase();
                
                if (!searchableText.includes(searchTerm)) return false;
            }
            
            return true;
        });
        
        this.updateDataTable();
        this.updateStats();
        this.updateFilterIndicator();
    }

    updateFilterIndicator() {
        const filterIndicator = document.getElementById('filter-indicator');
        if (!filterIndicator) return;
        
        const hasActiveFilters = Object.values(this.activeFilters).some(value => value !== '');
        
        if (hasActiveFilters) {
            filterIndicator.textContent = 'Filters applied';
            filterIndicator.style.display = 'inline';
        } else {
            filterIndicator.style.display = 'none';
        }
    }

    applyFilters() {
        const filters = this.getFilters();
        
        this.filteredData = this.stagingData.filter(item => {
            // Date range filter
            if (filters.date_from && item.date < filters.date_from) return false;
            if (filters.date_to && item.date > filters.date_to) return false;
            
            // Status filter
            if (filters.status && item.status !== filters.status) return false;
            
            // Search filter
            if (filters.search) {
                const searchTerm = filters.search.toLowerCase();
                const searchableText = [
                    item.employee_name,
                    item.employee_id_ptrj,
                    item.employee_id_venus,
                    item.task_code
                ].join(' ').toLowerCase();
                
                if (!searchableText.includes(searchTerm)) return false;
            }
            
            return true;
        });
        
        this.updateDataTable();
        this.updateStats();
    }

    updateDataTable(data = null) {
        const dataToShow = data || this.filteredData || this.stagingData;
        
        // Update data info
        this.updateDataInfo(dataToShow);
        
        if (this.currentView === 'table') {
            this.updateTableView(dataToShow);
        } else {
            this.updateCardView(dataToShow);
        }
        
        this.updateSelectionStats();
        this.updateMasterCheckbox();
    }

    updateTableView(dataToShow) {
        const tableBody = document.getElementById('data-table-body');
        const tableView = document.getElementById('table-view');
        const cardView = document.getElementById('card-view');
        
        if (tableView) tableView.style.display = 'block';
        if (cardView) cardView.style.display = 'none';
        
        if (!dataToShow || dataToShow.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4">
                        <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                        <p class="text-muted">No data available</p>
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = dataToShow.map(item => {
            const isSelected = this.selectedIds.has(item.id);
            return `
                <tr data-id="${item.id}" class="${isSelected ? 'selected' : ''}">
                    <td>
                        <input type="checkbox" class="form-check-input row-checkbox" 
                               data-id="${item.id}" ${isSelected ? 'checked' : ''}>
                    </td>
                    <td>${item.id}</td>
                    <td>${item.employee_name || '-'}</td>
                    <td>${this.formatDate(item.date)}</td>
                    <td>${item.time_in || '-'}</td>
                    <td>${item.time_out || '-'}</td>
                    <td>${this.getStatusBadge(item.status)}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="app.viewDetails(${item.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        // Add event listeners to checkboxes
        this.attachCheckboxListeners();
    }

    updateCardView(dataToShow) {
        const cardContainer = document.getElementById('data-cards-container');
        const tableView = document.getElementById('table-view');
        const cardView = document.getElementById('card-view');
        
        if (tableView) tableView.style.display = 'none';
        if (cardView) cardView.style.display = 'block';
        
        if (!cardContainer) return;
        
        if (!dataToShow || dataToShow.length === 0) {
            cardContainer.innerHTML = '<div class="text-center">No data available</div>';
            return;
        }

        cardContainer.innerHTML = dataToShow.map(item => {
            const isSelected = this.selectedIds.has(item.id);
            return `
                <div class="data-card ${isSelected ? 'selected' : ''}">
                    <div class="card-header">
                        <input type="checkbox" 
                               class="form-check-input row-checkbox" 
                               data-id="${item.id}" 
                               ${isSelected ? 'checked' : ''}>
                        <span class="card-id">#${item.id}</span>
                        ${this.getStatusBadge(item.status)}
                    </div>
                    <div class="card-body">
                        <h4>${item.employee_name || 'N/A'}</h4>
                        <div class="card-details">
                            <div><strong>Date:</strong> ${this.formatDate(item.date)}</div>
                            <div><strong>Time In:</strong> ${item.time_in || 'N/A'}</div>
                            <div><strong>Time Out:</strong> ${item.time_out || 'N/A'}</div>
                        </div>
                    </div>
                    <div class="card-actions">
                        <button class="btn btn-sm btn-primary" onclick="app.viewDetails(${item.id})">
                            View Details
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // Add event listeners to checkboxes
        this.attachCheckboxListeners();
    }

    attachCheckboxListeners() {
        document.querySelectorAll('.row-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const id = parseInt(e.target.dataset.id);
                if (e.target.checked) {
                    this.selectedIds.add(id);
                } else {
                    this.selectedIds.delete(id);
                }
                this.updateSelectionStats();
                this.updateMasterCheckbox();
                
                // Update card selection visual state
                const card = e.target.closest('.data-card');
                if (card) {
                    card.classList.toggle('selected', e.target.checked);
                }
                
                // Update row selection visual state
                const row = e.target.closest('tr');
                if (row) {
                    row.classList.toggle('selected', e.target.checked);
                }
            });
        });
    }

    updateStats() {
        document.getElementById('total-records').textContent = this.stagingData.length;
        this.updateSelectionStats();
        
        // Calculate success rate
        const processed = this.stagingData.filter(item => item.status === 'processed').length;
        const failed = this.stagingData.filter(item => item.status === 'failed').length;
        const total = processed + failed;
        const successRate = total > 0 ? Math.round((processed / total) * 100) : 0;
        
        document.getElementById('processed-count').textContent = processed;
        document.getElementById('success-rate').textContent = `${successRate}%`;
    }

    updateSelectionStats() {
        const selectedCount = this.selectedIds.size;
        const visibleData = this.filteredData || this.stagingData;
        const visibleCount = visibleData.length;
        
        // Update selection count display
        const selectionInfo = document.getElementById('selection-info');
        if (selectionInfo) {
            selectionInfo.textContent = `${selectedCount} selected`;
        }
        
        // Update selected count in stats
        const selectedCountElement = document.getElementById('selected-count');
        if (selectedCountElement) {
            selectedCountElement.textContent = selectedCount;
        }
        
        // Update automation button state
        this.updateAutomationButtons();
    }

    formatDate(dateString) {
        if (!dateString) return '-';
        try {
            return new Date(dateString).toLocaleDateString();
        } catch {
            return dateString;
        }
    }

    getStatusBadge(status) {
        const statusMap = {
            'pending': '<span class="badge bg-warning">Pending</span>',
            'processed': '<span class="badge bg-success">Processed</span>',
            'failed': '<span class="badge bg-danger">Failed</span>',
            'processing': '<span class="badge bg-info">Processing</span>'
        };
        return statusMap[status] || `<span class="badge bg-secondary">${status}</span>`;
    }

    selectAll() {
        const visibleData = this.filteredData || this.stagingData;
        visibleData.forEach(item => this.selectedIds.add(item.id));
        this.updateDataTable();
        this.updateSelectionStats();
        document.getElementById('master-checkbox').checked = true;
    }

    clearSelection() {
        this.selectedIds.clear();
        this.updateDataTable();
        this.updateSelectionStats();
        document.getElementById('master-checkbox').checked = false;
    }

    toggleAllSelection(checked) {
        if (checked) {
            this.selectAll();
        } else {
            this.clearSelection();
        }
    }

    async initializeBrowser() {
        if (this.browserStatus.isInitializing) {
            return;
        }
        
        this.browserStatus.isInitializing = true;
        this.updateAutomationButtons();
        
        // Show initialization loading overlay
        this.showBrowserInitializationLoading();
        
        try {
            this.updateBrowserStatus('initializing', 'Starting browser initialization...');
            this.showAlert('info', 'Initializing browser and performing login...');
            
            // Call the backend to initialize browser and login
            const result = await window.electronAPI.initializeBrowser();
            
            if (result.success) {
                this.browserStatus.isInitialized = true;
                this.updateBrowserStatus('ready', 'Browser ready - Logged in and positioned at task register');
                this.showAlert('success', 'Browser initialized and login successful! You can now process selected records.');
            } else {
                this.browserStatus.isInitialized = false;
                this.updateBrowserStatus('error', `Browser initialization failed: ${result.error}`);
                this.showAlert('danger', `Browser initialization failed: ${result.error}`);
            }
        } catch (error) {
            this.browserStatus.isInitialized = false;
            this.updateBrowserStatus('error', `Browser initialization error: ${error.message}`);
            this.showAlert('danger', `Error initializing browser: ${error.message}`);
        } finally {
            this.browserStatus.isInitializing = false;
            this.hideBrowserInitializationLoading();
            this.updateAutomationButtons();
        }
    }

    async startAutomation() {
        if (!this.browserStatus.isInitialized) {
            this.showAlert('warning', 'Please initialize the browser first by clicking "Initialize Browser & Login".');
            return;
        }
        
        if (this.selectedIds.size === 0) {
            this.showAlert('warning', 'Please select at least one record to process.');
            return;
        }
        
        try {
            const selectedData = this.getSelectedRecords();
            
            // Use enhanced processing endpoint
            const result = await window.electronAPI.processSelectedData(selectedData);
            
            if (result.success) {
                this.automationStatus.isRunning = true;
                this.showProgressCard();
                this.startStatusMonitoring();
                this.updateAutomationButtons();
                this.showAlert('success', `Started automation for ${selectedData.length} records`);
            } else {
                this.showAlert('danger', `Failed to start automation: ${result.error}`);
            }
        } catch (error) {
            this.showAlert('danger', `Error starting automation: ${error.message}`);
        }
    }

    getSelectedRecords() {
        const selectedRecords = [];
        
        this.selectedIds.forEach(id => {
            const record = this.stagingData.find(item => item.id === id);
            if (record) {
                selectedRecords.push(record);
            }
        });
        
        return selectedRecords;
    }

    async stopAutomation() {
        try {
            // Try enhanced stop processing first
            const stopResult = await window.electronAPI.stopProcessing();
            
            if (stopResult.success) {
                this.automationStatus.isRunning = false;
                this.stopStatusMonitoring();
                this.hideProgressCard();
                this.updateAutomationButtons();
                this.showAlert('success', 'Processing stopped successfully!');
                return;
            }
            
            // Fallback to original stop automation
            const result = await window.electronAPI.stopAutomation();
            
            if (result.success) {
                this.automationStatus.isRunning = false;
                this.hideProgressCard();
                this.stopStatusMonitoring();
                this.updateAutomationButtons();
                this.showAlert('info', 'Automation stopped.');
                await this.refreshData();
            } else {
                this.showAlert('danger', `Failed to stop automation: ${result.error}`);
            }
        } catch (error) {
            this.showAlert('danger', `Error stopping automation: ${error.message}`);
        }
    }

    showProgressCard() {
        document.getElementById('progress-card').style.display = 'block';
    }

    hideProgressCard() {
        document.getElementById('progress-card').style.display = 'none';
    }

    updateAutomationButtons() {
        const initButton = document.getElementById('init-browser');
        const startButton = document.getElementById('start-automation');
        const stopButton = document.getElementById('stop-automation');
        
        // Browser initialization button
        initButton.disabled = this.browserStatus.isInitializing || this.automationStatus.isRunning;
        
        // Update button text and icon based on browser status
        const initIcon = initButton.querySelector('i');
        const initSpinner = initButton.querySelector('.init-spinner');
        const initText = initButton.childNodes[initButton.childNodes.length - 1];
        
        if (this.browserStatus.isInitializing) {
            initIcon.style.display = 'none';
            initSpinner.style.display = 'inline-block';
            initText.textContent = ' Initializing...';
            initButton.classList.remove('btn-info', 'btn-success');
            initButton.classList.add('btn-warning');
        } else if (this.browserStatus.isInitialized) {
            initIcon.className = 'fas fa-check me-2';
            initIcon.style.display = 'inline-block';
            initSpinner.style.display = 'none';
            initText.textContent = ' Browser Ready';
            initButton.classList.remove('btn-info', 'btn-warning');
            initButton.classList.add('btn-success');
        } else {
            initIcon.className = 'fas fa-globe me-2';
            initIcon.style.display = 'inline-block';
            initSpinner.style.display = 'none';
            initText.textContent = ' Initialize Browser & Login';
            initButton.classList.remove('btn-warning', 'btn-success');
            initButton.classList.add('btn-info');
        }
        
        // Start automation button - only enabled if browser is initialized, records are selected, and automation is not running
        startButton.disabled = !this.browserStatus.isInitialized || this.selectedIds.size === 0 || this.automationStatus.isRunning;
        
        // Stop automation button
        stopButton.disabled = !this.automationStatus.isRunning;
    }

    startStatusMonitoring() {
        this.statusTimer = setInterval(async () => {
            await this.updateAutomationStatus();
        }, 2000);
    }

    stopStatusMonitoring() {
        if (this.statusTimer) {
            clearInterval(this.statusTimer);
            this.statusTimer = null;
        }
    }

    async updateAutomationStatus() {
        try {
            // Try enhanced processing progress first
            const progressResult = await window.electronAPI.getProcessingProgress();
            
            if (progressResult.success && progressResult.data) {
                const progress = progressResult.data;
                
                // Update automation status with enhanced progress data
                this.automationStatus = {
                    isRunning: progress.status === 'processing',
                    progress: progress.total > 0 ? Math.round((progress.processed / progress.total) * 100) : 0,
                    processed: progress.processed || 0,
                    total: progress.total || 0,
                    success: progress.success || 0,
                    failed: progress.failed || 0,
                    currentItem: progress.current_employee || '-',
                    status: progress.status || 'idle'
                };
                
                // Update progress UI
                const progressBar = document.getElementById('progress-bar');
                const progressText = document.getElementById('progress-text');
                const currentItem = document.getElementById('current-item');
                const progressStatus = document.getElementById('progress-status');
                
                if (progressBar) progressBar.style.width = `${this.automationStatus.progress}%`;
                if (progressText) progressText.textContent = `${this.automationStatus.processed} / ${this.automationStatus.total}`;
                if (currentItem) currentItem.textContent = this.automationStatus.currentItem;
                if (progressStatus) progressStatus.textContent = this.getStatusText(this.automationStatus.status);
                
                // If automation completed or stopped, stop monitoring
                if (!this.automationStatus.isRunning) {
                    this.stopStatusMonitoring();
                    this.hideProgressCard();
                    this.updateAutomationButtons();
                    await this.refreshData();
                    await this.refreshProcessedData();
                }
            } else {
                // Fallback to original automation status
                const result = await window.electronAPI.getAutomationStatus();
                
                if (result.success) {
                    const status = result.data;
                    this.automationStatus = { ...this.automationStatus, ...status };
                    
                    // Update progress UI with fallback data
                    const progressBar = document.getElementById('progress-bar');
                    const progressText = document.getElementById('progress-text');
                    const currentItem = document.getElementById('current-item');
                    const progressStatus = document.getElementById('progress-status');
                    
                    if (progressBar) progressBar.style.width = `${this.automationStatus.progress || 0}%`;
                    if (progressText) progressText.textContent = `${this.automationStatus.processed || 0} / ${this.automationStatus.total || 0}`;
                    if (currentItem) currentItem.textContent = this.automationStatus.currentItem || '-';
                    if (progressStatus) progressStatus.textContent = this.automationStatus.isRunning ? 'Running' : 'Completed';
                    
                    // If automation completed, stop monitoring
                    if (!this.automationStatus.isRunning) {
                        this.stopStatusMonitoring();
                        this.hideProgressCard();
                        this.updateAutomationButtons();
                        await this.refreshData();
                        await this.refreshCrosscheckResults();
                    }
                }
            }
        } catch (error) {
            console.error('Error updating automation status:', error);
        }
    }

    getStatusText(status) {
        switch (status) {
            case 'processing': return 'Processing...';
            case 'completed': return 'Completed';
            case 'stopped': return 'Stopped';
            case 'error': return 'Error';
            default: return 'Idle';
        }
    }

    async refreshProcessedData() {
        try {
            // This could fetch processed data results if needed
            console.log('Refreshing processed data...');
        } catch (error) {
            console.error('Error refreshing processed data:', error);
        }
    }

    async refreshCrosscheckResults() {
        try {
            const result = await window.electronAPI.getCrosscheckResults();
            
            if (result.success) {
                this.displayCrosscheckResults(result.data);
                document.getElementById('crosscheck-card').style.display = 'block';
            } else {
                console.error('Failed to get crosscheck results:', result.error);
            }
        } catch (error) {
            console.error('Error getting crosscheck results:', error);
        }
    }

    displayCrosscheckResults(results) {
        const container = document.getElementById('crosscheck-results');
        
        if (!results || results.length === 0) {
            container.innerHTML = '<p class="text-muted">No crosscheck results available</p>';
            return;
        }
        
        container.innerHTML = results.map(result => `
            <div class="crosscheck-result ${result.status === 'success' ? 'crosscheck-success' : 'crosscheck-failed'}">
                <div>
                    <strong>${result.employee_name}</strong>
                    <small class="d-block text-muted">${result.date}</small>
                </div>
                <div>
                    <span class="badge ${result.status === 'success' ? 'bg-success' : 'bg-danger'}">
                        ${result.status === 'success' ? 'Match' : 'Mismatch'}
                    </span>
                </div>
            </div>
        `).join('');
    }

    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        this.refreshTimer = setInterval(() => {
            if (!this.automationStatus.isRunning) {
                this.refreshData();
            }
        }, this.settings.refreshInterval);
    }

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    openSettings() {
        // Populate settings form
        document.getElementById('flask-server-url').value = this.settings.flaskServerUrl;
        document.getElementById('auto-refresh').checked = this.settings.autoRefresh;
        document.getElementById('auto-launch-browser').checked = this.settings.autoLaunchBrowser;
        document.getElementById('refresh-interval').value = this.settings.refreshInterval / 1000;
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('settingsModal'));
        modal.show();
    }

    async saveSettings() {
        const newSettings = {
            flaskServerUrl: document.getElementById('flask-server-url').value,
            autoRefresh: document.getElementById('auto-refresh').checked,
            autoLaunchBrowser: document.getElementById('auto-launch-browser').checked,
            refreshInterval: parseInt(document.getElementById('refresh-interval').value) * 1000
        };
        
        try {
            const result = await window.electronAPI.saveSettings(newSettings);
            
            if (result.success) {
                this.settings = { ...this.settings, ...newSettings };
                
                // Update auto-refresh
                if (this.settings.autoRefresh) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
                modal.hide();
                
                this.showAlert('success', 'Settings saved successfully!');
                
                // Reconnect to server if URL changed
                await this.checkConnection();
            } else {
                this.showAlert('danger', `Failed to save settings: ${result.error}`);
            }
        } catch (error) {
            this.showAlert('danger', `Error saving settings: ${error.message}`);
        }
    }

    viewDetails(id) {
        const item = this.stagingData.find(item => item.id === id);
        if (item) {
            const details = Object.entries(item)
                .map(([key, value]) => `<strong>${key}:</strong> ${value || '-'}`)
                .join('<br>');
            
            window.electronAPI.showInfoDialog('Record Details', details);
        }
    }

    switchView(viewType) {
        this.currentView = viewType;
        
        // Update button states
        const tableBtn = document.getElementById('view-table');
        const cardsBtn = document.getElementById('view-cards');
        
        if (tableBtn && cardsBtn) {
            tableBtn.classList.toggle('active', viewType === 'table');
            cardsBtn.classList.toggle('active', viewType === 'cards');
        }
        
        // Update data display
        this.updateDataTable();
    }

    updateDataInfo(dataToShow) {
        const totalCount = document.getElementById('total-records');
        const filteredInfo = document.getElementById('filtered-info');
        
        if (totalCount) {
            totalCount.textContent = dataToShow.length;
        }
        
        if (filteredInfo) {
            if (dataToShow.length !== this.stagingData.length) {
                filteredInfo.textContent = `(filtered from ${this.stagingData.length} total)`;
                filteredInfo.style.display = 'inline';
            } else {
                filteredInfo.style.display = 'none';
            }
        }
    }

    updateMasterCheckbox() {
        const masterCheckbox = document.getElementById('master-checkbox');
        if (!masterCheckbox) return;
        
        const visibleData = this.filteredData || this.stagingData;
        const visibleIds = visibleData.map(item => item.id);
        const selectedVisibleIds = visibleIds.filter(id => this.selectedIds.has(id));
        
        if (selectedVisibleIds.length === 0) {
            masterCheckbox.checked = false;
            masterCheckbox.indeterminate = false;
        } else if (selectedVisibleIds.length === visibleIds.length) {
            masterCheckbox.checked = true;
            masterCheckbox.indeterminate = false;
        } else {
            masterCheckbox.checked = false;
            masterCheckbox.indeterminate = true;
        }
    }

    showAlert(type, message) {
        const alert = document.getElementById('status-alert');
        const messageSpan = document.getElementById('status-message');
        
        if (alert && messageSpan) {
            alert.className = `alert alert-${type}`;
            messageSpan.textContent = message;
            alert.classList.remove('d-none');
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                alert.classList.add('d-none');
            }, 5000);
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VenusAutoFillApp();
});

// Handle app errors
window.addEventListener('error', (event) => {
    console.error('Application error:', event.error);
    if (window.app) {
        window.app.showAlert('danger', `Application error: ${event.error.message}`);
    }
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    if (window.app) {
        window.app.showAlert('danger', `Promise rejection: ${event.reason}`);
    }
});