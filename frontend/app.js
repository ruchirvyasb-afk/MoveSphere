/* ============================================
   MoveSphere — Cloud Bus Pass System
   Application Logic & API Integration
   ============================================ */

// ============ CONFIGURATION ============
const API_BASE_URL = 'https://movesphere.onrender.com';

// ============ ROUTES & PRICING ============
const ROUTES = [
    { source: 'Mumbai', destination: 'Pune', fare: 250, busName: 'MS Express 101', duration: '3h 30m' },
    { source: 'Pune', destination: 'Mumbai', fare: 250, busName: 'MS Express 102', duration: '3h 30m' },
    { source: 'Mumbai', destination: 'Nashik', fare: 180, busName: 'MS Express 201', duration: '4h 00m' },
    { source: 'Nashik', destination: 'Mumbai', fare: 180, busName: 'MS Express 202', duration: '4h 00m' },
    { source: 'Pune', destination: 'Nashik', fare: 150, busName: 'MS Express 301', duration: '3h 00m' },
    { source: 'Nashik', destination: 'Pune', fare: 150, busName: 'MS Express 302', duration: '3h 00m' },
    { source: 'Mumbai', destination: 'Thane', fare: 50, busName: 'MS Local 401', duration: '0h 45m' },
    { source: 'Thane', destination: 'Mumbai', fare: 50, busName: 'MS Local 402', duration: '0h 45m' },
];

const PASS_FARES = {
    daily: { amount: 50, label: 'Daily Pass', duration: 'Valid for 1 day' },
    weekly: { amount: 250, label: 'Weekly Pass', duration: 'Valid for 7 days' },
    monthly: { amount: 800, label: 'Monthly Pass', duration: 'Valid for 30 days' }
};

// ============ STATE ============
let currentUser = null;
let appState = {
    passes: [],
    tickets: [],
    payments: [],
    isLoading: false
};

// Pending items waiting for payment
let pendingTicket = null;  // { source, destination, fare }
let pendingPass = null;    // { passType, fare }

// ============ INITIALIZATION ============
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    // Check for stored login
    const storedUser = localStorage.getItem('movesphere_user');
    if (storedUser) {
        try {
            currentUser = JSON.parse(storedUser);
            showDashboard();
        } catch (e) {
            localStorage.removeItem('movesphere_user');
            showPage('landing');
        }
    } else {
        showPage('landing');
    }

    // Setup navbar scroll effect
    window.addEventListener('scroll', () => {
        const navbar = document.getElementById('navbar');
        if (navbar) {
            navbar.classList.toggle('scrolled', window.scrollY > 10);
        }
    });

    // Animate stats counters on landing page
    animateCounters();

    // Remove page loader
    setTimeout(() => {
        const loader = document.getElementById('pageLoader');
        if (loader) {
            loader.classList.add('fade-out');
            setTimeout(() => loader.remove(), 300);
        }
    }, 600);

    // Setup bus search filter listeners
    setupBusFilters();

    // Setup pass type change listener
    setupPassFareListener();
}

// ============ PAGE NAVIGATION ============
function showPage(pageId) {
    // Hide all page views
    document.querySelectorAll('.page-view').forEach(p => p.classList.remove('active'));

    // Show target page
    const target = document.getElementById(`page-${pageId}`);
    if (target) target.classList.add('active');

    // Toggle navbar buttons
    updateNavbar(pageId);

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showLanding() {
    showPage('landing');
}

function showLogin() {
    showPage('login');
    clearForm('loginForm');
}

function showRegister() {
    showPage('register');
    clearForm('registerForm');
}

function showDashboard() {
    showPage('dashboard');
    updateDashboardUI();
    switchDashTab('overview');
}

function updateNavbar(pageId) {
    const navBtns = document.getElementById('navButtons');
    const navUser = document.getElementById('navUser');

    if (pageId === 'dashboard') {
        if (navBtns) navBtns.classList.add('hidden');
        if (navUser) {
            navUser.classList.remove('hidden');
            if (currentUser) {
                document.getElementById('navUserName').textContent = currentUser.name;
                document.getElementById('navAvatarLetter').textContent = currentUser.name.charAt(0).toUpperCase();
            }
        }
    } else {
        if (navBtns) navBtns.classList.remove('hidden');
        if (navUser) navUser.classList.add('hidden');
    }
}

// ============ DASHBOARD TAB NAVIGATION ============
function switchDashTab(tabId) {
    // Update sidebar links
    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.classList.remove('active');
    });
    const activeLink = document.querySelector(`[data-tab="${tabId}"]`);
    if (activeLink) activeLink.classList.add('active');

    // Toggle tab content
    document.querySelectorAll('.dash-page').forEach(page => {
        page.classList.remove('active');
    });
    const targetPage = document.getElementById(`dash-${tabId}`);
    if (targetPage) targetPage.classList.add('active');

    // Render bus list when ticket tab is shown
    if (tabId === 'ticket') {
        renderBusList();
    }

    // Update payment context when payment tab is shown
    if (tabId === 'payment') {
        updatePaymentContext();
    }

    // Update pass fare display when pass tab is shown
    if (tabId === 'pass') {
        updatePassFare();
    }

    // Auto-populate user IDs
    if (currentUser && currentUser.user_id) {
        const fields = ['paymentUserId', 'passUserId', 'ticketUserId'];
        fields.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = currentUser.user_id;
        });
    }

    // Close mobile sidebar
    closeMobileSidebar();
}

// ============ MOBILE SIDEBAR ============
function toggleMobileSidebar() {
    const sidebar = document.getElementById('dashSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    sidebar.classList.toggle('mobile-open');
    overlay.classList.toggle('show');
}

function closeMobileSidebar() {
    const sidebar = document.getElementById('dashSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (sidebar) sidebar.classList.remove('mobile-open');
    if (overlay) overlay.classList.remove('show');
}

// ============ TOAST SYSTEM ============
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: `<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:var(--success);flex-shrink:0;"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`,
        error: `<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:var(--error);flex-shrink:0;"><path stroke-linecap="round" stroke-linejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`,
        warning: `<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:var(--warning);flex-shrink:0;"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>`,
        info: `<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:var(--primary);flex-shrink:0;"><path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`
    };

    toast.innerHTML = `
        <div class="toast-content">
            ${icons[type] || icons.info}
            <span class="toast-message">${message}</span>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    container.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 4500);
}

// ============ FORM UTILITIES ============
function clearForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.querySelectorAll('input').forEach(input => input.value = '');
        form.querySelectorAll('.form-error').forEach(err => err.classList.remove('show'));
    }
}

function showFieldError(fieldId, message) {
    const errEl = document.getElementById(`${fieldId}-error`);
    if (errEl) {
        errEl.textContent = message;
        errEl.classList.add('show');
    }
}

function clearFieldErrors(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.querySelectorAll('.form-error').forEach(err => err.classList.remove('show'));
    }
}

function togglePassword(inputId) {
    const el = document.getElementById(inputId);
    el.type = el.type === 'password' ? 'text' : 'password';
}

function setButtonLoading(btnId, loading) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    if (loading) {
        btn.dataset.originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner"></span>`;
    } else {
        btn.disabled = false;
        btn.innerHTML = btn.dataset.originalHtml || btn.innerHTML;
    }
}

// ============ API HELPERS ============
async function apiRequest(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };

    if (body) options.body = JSON.stringify(body);

    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || data.message || 'Request failed');
    }

    return data;
}

// ============ REGISTRATION ============
async function registerUser() {
    clearFieldErrors('registerForm');

    const name = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const phone = document.getElementById('regPhone').value.trim();
    const password = document.getElementById('regPassword').value;

    // Validation
    let hasError = false;
    if (!name) { showFieldError('regName', 'Full name is required'); hasError = true; }
    if (!email) { showFieldError('regEmail', 'Email address is required'); hasError = true; }
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { showFieldError('regEmail', 'Enter a valid email address'); hasError = true; }
    if (!phone) { showFieldError('regPhone', 'Phone number is required'); hasError = true; }
    if (!password) { showFieldError('regPassword', 'Password is required'); hasError = true; }
    else if (password.length < 6) { showFieldError('regPassword', 'Password must be at least 6 characters'); hasError = true; }

    if (hasError) return;

    setButtonLoading('btnRegister', true);

    try {
        const data = await apiRequest('/register', 'POST', { name, email, password, phone });
        showToast(data.message || 'Registration successful! You can now log in.', 'success');
        showLogin();
    } catch (error) {
        showToast(error.message || 'Registration failed. Please try again.', 'error');
    } finally {
        setButtonLoading('btnRegister', false);
    }
}

// ============ LOGIN ============
async function loginUser() {
    clearFieldErrors('loginForm');

    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;

    let hasError = false;
    if (!email) { showFieldError('loginEmail', 'Email is required'); hasError = true; }
    if (!password) { showFieldError('loginPassword', 'Password is required'); hasError = true; }
    if (hasError) return;

    setButtonLoading('btnLogin', true);

    try {
        const data = await apiRequest('/login', 'POST', { email, password });

        currentUser = {
            user_id: data.user_id,
            name: data.name || email.split('@')[0],
            email: email
        };

        localStorage.setItem('movesphere_user', JSON.stringify(currentUser));
        showToast('Login successful! Welcome aboard.', 'success');
        showDashboard();
    } catch (error) {
        showToast(error.message || 'Invalid credentials. Please try again.', 'error');
    } finally {
        setButtonLoading('btnLogin', false);
    }
}

// ============ LOGOUT ============
function logout() {
    currentUser = null;
    appState = { passes: [], tickets: [], payments: [], isLoading: false };
    pendingTicket = null;
    pendingPass = null;
    localStorage.removeItem('movesphere_user');
    showToast('You have been signed out.', 'info');
    showLanding();
}

// ============ BUS LIST RENDERING ============
function renderBusList(filterSource = '', filterDest = '') {
    const container = document.getElementById('busListContainer');
    if (!container) return;

    const srcFilter = filterSource.toLowerCase().trim();
    const destFilter = filterDest.toLowerCase().trim();

    // Filter routes — show unique routes (deduplicate by showing only one direction)
    let filtered = ROUTES.filter(route => {
        const matchSource = !srcFilter || route.source.toLowerCase().includes(srcFilter);
        const matchDest = !destFilter || route.destination.toLowerCase().includes(destFilter);
        return matchSource && matchDest;
    });

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="bus-no-results">
                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/>
                </svg>
                <p>No buses found for this route. Try different cities.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map(route => {
        const isSelected = pendingTicket &&
            pendingTicket.source === route.source &&
            pendingTicket.destination === route.destination;

        return `
            <div class="bus-card ${isSelected ? 'selected' : ''}"
                 onclick="selectBus('${route.source}', '${route.destination}', ${route.fare}, '${route.busName}')"
                 id="bus-${route.source}-${route.destination}">
                <div class="bus-card-route">
                    <div class="bus-card-icon">
                        ${getBusSVG()}
                    </div>
                    <div class="bus-card-info">
                        <h5>${route.source} → ${route.destination}</h5>
                        <p>${route.busName} • ${route.duration}</p>
                    </div>
                </div>
                <div style="display:flex;align-items:center;">
                    <div class="bus-card-fare">
                        <div class="fare-amount">₹${route.fare}</div>
                        <div class="fare-label">per seat</div>
                    </div>
                    <div class="bus-card-check">
                        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                        </svg>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function selectBus(source, destination, fare, busName) {
    // Set pending ticket state
    pendingTicket = { source, destination, fare, busName };

    // Auto-fill the source/destination fields
    const srcField = document.getElementById('ticketSource');
    const destField = document.getElementById('ticketDest');
    if (srcField) srcField.value = source;
    if (destField) destField.value = destination;

    // Show fare summary
    const fareSummary = document.getElementById('ticketFareSummary');
    if (fareSummary) {
        fareSummary.classList.remove('hidden');
        fareSummary.innerHTML = `
            <div class="fare-summary-left">
                <div class="fare-summary-icon">
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                </div>
                <div class="fare-summary-text">
                    <h5>${source} → ${destination}</h5>
                    <p>${busName} selected</p>
                </div>
            </div>
            <div class="fare-summary-amount">₹${fare}</div>
        `;
    }

    // Re-render bus list to update selected state
    renderBusList(
        document.getElementById('ticketSource')?.value || '',
        document.getElementById('ticketDest')?.value || ''
    );

    showToast(`Selected: ${source} → ${destination} (₹${fare})`, 'success');
}

function setupBusFilters() {
    // Setup debounced filter on source/destination inputs
    const srcField = document.getElementById('ticketSource');
    const destField = document.getElementById('ticketDest');

    let filterTimeout;
    const debounceFilter = () => {
        clearTimeout(filterTimeout);
        filterTimeout = setTimeout(() => {
            renderBusList(
                srcField?.value || '',
                destField?.value || ''
            );
        }, 200);
    };

    if (srcField) srcField.addEventListener('input', debounceFilter);
    if (destField) destField.addEventListener('input', debounceFilter);
}

// ============ PASS FARE DISPLAY ============
function setupPassFareListener() {
    const passTypeSelect = document.getElementById('passType');
    if (passTypeSelect) {
        passTypeSelect.addEventListener('change', updatePassFare);
    }
}

function updatePassFare() {
    const passType = document.getElementById('passType')?.value;
    const fareDisplay = document.getElementById('passFareDisplay');

    if (!fareDisplay) return;

    if (passType && PASS_FARES[passType]) {
        const fareInfo = PASS_FARES[passType];
        fareDisplay.classList.remove('hidden');
        fareDisplay.innerHTML = `
            <div class="pass-fare-label">Pass Fare</div>
            <div class="pass-fare-amount">₹${fareInfo.amount}</div>
            <div class="pass-fare-duration">${fareInfo.duration}</div>
        `;
    } else {
        fareDisplay.classList.add('hidden');
    }
}

// ============ PAYMENT CONTEXT ============
function updatePaymentContext() {
    const banner = document.getElementById('paymentContextBanner');
    const amountField = document.getElementById('paymentAmount');

    if (!banner) return;

    if (pendingTicket) {
        banner.classList.remove('hidden');
        banner.innerHTML = `
            <div class="payment-context-left">
                <div class="payment-context-icon">
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                    </svg>
                </div>
                <div class="payment-context-info">
                    <h4>🎫 Ticket Booking</h4>
                    <p>${pendingTicket.source} → ${pendingTicket.destination} • ${pendingTicket.busName || ''}</p>
                </div>
            </div>
            <div class="payment-context-right">
                <div class="payment-context-amount">₹${pendingTicket.fare}</div>
                <button class="payment-context-cancel" onclick="cancelPendingPayment()">Cancel</button>
            </div>
        `;
        if (amountField) {
            amountField.value = pendingTicket.fare;
            amountField.readOnly = true;
        }
    } else if (pendingPass) {
        banner.classList.remove('hidden');
        const fareInfo = PASS_FARES[pendingPass.passType];
        banner.innerHTML = `
            <div class="payment-context-left">
                <div class="payment-context-icon">
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"/>
                    </svg>
                </div>
                <div class="payment-context-info">
                    <h4>🎟️ Bus Pass Purchase</h4>
                    <p>${fareInfo ? fareInfo.label : pendingPass.passType} • ${fareInfo ? fareInfo.duration : ''}</p>
                </div>
            </div>
            <div class="payment-context-right">
                <div class="payment-context-amount">₹${pendingPass.fare}</div>
                <button class="payment-context-cancel" onclick="cancelPendingPayment()">Cancel</button>
            </div>
        `;
        if (amountField) {
            amountField.value = pendingPass.fare;
            amountField.readOnly = true;
        }
    } else {
        banner.classList.add('hidden');
        if (amountField) {
            amountField.readOnly = false;
        }
    }
}

function cancelPendingPayment() {
    const returnTab = pendingTicket ? 'ticket' : (pendingPass ? 'pass' : 'overview');
    pendingTicket = null;
    pendingPass = null;
    const amountField = document.getElementById('paymentAmount');
    if (amountField) {
        amountField.value = '';
        amountField.readOnly = false;
    }
    switchDashTab(returnTab);
    showToast('Payment cancelled', 'info');
}

// ============ PAYMENT ============
async function makePayment() {
    if (!currentUser) { showToast('Please login first', 'error'); return; }

    const amount = document.getElementById('paymentAmount').value;

    if (!amount || parseFloat(amount) <= 0) {
        showFieldError('paymentAmount', 'Please enter a valid amount');
        return;
    }

    setButtonLoading('btnPayment', true);
    showModal('paymentProcessingModal');

    try {
        const data = await apiRequest('/make-payment', 'POST', {
            user_id: currentUser.user_id,
            amount: parseFloat(amount)
        });

        // Hide processing, show success
        document.getElementById('paymentProcessing').classList.add('hidden');
        document.getElementById('paymentSuccess').classList.remove('hidden');

        // Update transaction details
        document.getElementById('txnPaymentId').textContent = `#TXN-${data.payment_id}`;
        document.getElementById('txnAmount').textContent = `₹${parseFloat(data.amount).toFixed(2)}`;
        document.getElementById('txnStatus').textContent = data.status;
        document.getElementById('txnDate').textContent = new Date().toLocaleString();

        // Add to local state
        appState.payments.push({
            payment_id: data.payment_id,
            amount: data.amount,
            status: data.status,
            date: new Date().toISOString()
        });

        updateDashboardOverview();
        showToast('Payment completed successfully!', 'success');

        // Handle pending ticket or pass
        if (pendingTicket) {
            await completePendingTicket();
        } else if (pendingPass) {
            await completePendingPass();
        }
    } catch (error) {
        closeModal('paymentProcessingModal');
        showToast(error.message || 'Payment failed. Please try again.', 'error');
    } finally {
        setButtonLoading('btnPayment', false);
    }
}

async function completePendingTicket() {
    if (!pendingTicket) return;

    const ticketData = { ...pendingTicket };

    try {
        const data = await apiRequest('/book-ticket', 'POST', {
            user_id: currentUser.user_id,
            source: ticketData.source,
            destination: ticketData.destination
        });

        appState.tickets.push(data);
        updateDashboardOverview();

        showToast(`Ticket booked: ${ticketData.source} → ${ticketData.destination}!`, 'success');

        // Clear pending state
        pendingTicket = null;
        const amountField = document.getElementById('paymentAmount');
        if (amountField) {
            amountField.value = '';
            amountField.readOnly = false;
        }

        // Override the Done button to show ticket
        const doneBtn = document.querySelector('#paymentSuccess .btn-primary');
        if (doneBtn) {
            doneBtn.dataset.pendingAction = 'showTicket';
            doneBtn.dataset.ticketData = JSON.stringify(data);
            doneBtn.dataset.source = ticketData.source;
            doneBtn.dataset.destination = ticketData.destination;
        }
    } catch (error) {
        showToast('Payment succeeded but ticket booking failed: ' + error.message, 'warning');
        pendingTicket = null;
    }
}

async function completePendingPass() {
    if (!pendingPass) return;

    const passData = { ...pendingPass };

    try {
        const data = await apiRequest('/apply-pass', 'POST', {
            user_id: currentUser.user_id,
            pass_type: passData.passType
        });

        appState.passes.push(data);
        updateDashboardOverview();

        showToast(`${PASS_FARES[passData.passType]?.label || 'Bus Pass'} generated successfully!`, 'success');

        // Clear pending state
        pendingPass = null;
        const amountField = document.getElementById('paymentAmount');
        if (amountField) {
            amountField.value = '';
            amountField.readOnly = false;
        }

        // Override the Done button to show pass
        const doneBtn = document.querySelector('#paymentSuccess .btn-primary');
        if (doneBtn) {
            doneBtn.dataset.pendingAction = 'showPass';
            doneBtn.dataset.passData = JSON.stringify(data);
            doneBtn.dataset.passType = passData.passType;
        }
    } catch (error) {
        showToast('Payment succeeded but pass generation failed: ' + error.message, 'warning');
        pendingPass = null;
    }
}

function resetPaymentModal() {
    // Check if there's a pending action
    const doneBtn = document.querySelector('#paymentSuccess .btn-primary');
    const pendingAction = doneBtn?.dataset.pendingAction;

    if (pendingAction === 'showTicket') {
        const ticketData = JSON.parse(doneBtn.dataset.ticketData || '{}');
        const source = doneBtn.dataset.source;
        const destination = doneBtn.dataset.destination;

        // Clean up
        delete doneBtn.dataset.pendingAction;
        delete doneBtn.dataset.ticketData;
        delete doneBtn.dataset.source;
        delete doneBtn.dataset.destination;

        document.getElementById('paymentProcessing').classList.remove('hidden');
        document.getElementById('paymentSuccess').classList.add('hidden');
        closeModal('paymentProcessingModal');
        document.getElementById('paymentAmount').value = '';

        // Switch to ticket tab and show the booked ticket
        switchDashTab('ticket');
        displayBookedTicket(ticketData, source, destination);
        return;
    }

    if (pendingAction === 'showPass') {
        const passData = JSON.parse(doneBtn.dataset.passData || '{}');
        const passType = doneBtn.dataset.passType;

        // Clean up
        delete doneBtn.dataset.pendingAction;
        delete doneBtn.dataset.passData;
        delete doneBtn.dataset.passType;

        document.getElementById('paymentProcessing').classList.remove('hidden');
        document.getElementById('paymentSuccess').classList.add('hidden');
        closeModal('paymentProcessingModal');
        document.getElementById('paymentAmount').value = '';

        // Switch to pass tab and show the generated pass
        switchDashTab('pass');
        displayGeneratedPass(passData, passType);
        return;
    }

    // Default reset
    document.getElementById('paymentProcessing').classList.remove('hidden');
    document.getElementById('paymentSuccess').classList.add('hidden');
    closeModal('paymentProcessingModal');
    document.getElementById('paymentAmount').value = '';
}

// ============ BUS PASS GENERATION ============
async function generatePass() {
    if (!currentUser) { showToast('Please login first', 'error'); return; }

    const passType = document.getElementById('passType').value;

    if (!passType) {
        showToast('Please select a pass type', 'warning');
        return;
    }

    const fareInfo = PASS_FARES[passType];
    if (!fareInfo) {
        showToast('Invalid pass type', 'error');
        return;
    }

    // Set pending pass and redirect to payment
    pendingPass = { passType, fare: fareInfo.amount };
    showToast(`Redirecting to payment for ${fareInfo.label} (₹${fareInfo.amount})...`, 'info');

    // Switch to payment tab — context will be auto-updated
    switchDashTab('payment');
}

function displayGeneratedPass(data, passType) {
    const container = document.getElementById('generatedPassContainer');
    container.classList.remove('hidden');

    const typeLabels = {
        'daily': 'Daily Pass',
        'weekly': 'Weekly Pass',
        'monthly': 'Monthly Pass'
    };

    document.getElementById('genPassType').textContent = typeLabels[passType] || passType;
    document.getElementById('genPassId').textContent = `#PASS-${data.pass_id}`;
    document.getElementById('genPassHolder').textContent = currentUser.name;
    document.getElementById('genPassIssue').textContent = data.issue_date;
    document.getElementById('genPassExpiry').textContent = data.expiry_date;

    // Set QR code
    const qrImg = document.getElementById('genPassQR');
    if (data.qr_url) {
        qrImg.innerHTML = `<img src="${data.qr_url}" alt="QR Code">`;
    } else {
        qrImg.innerHTML = generateSVGQR();
    }

    // Set download link
    const downloadBtn = document.getElementById('btnDownloadPass');
    if (data.pdf_url) {
        downloadBtn.onclick = () => window.open(data.pdf_url, '_blank');
    } else {
        downloadBtn.onclick = () => window.open(`${API_BASE_URL}/download-pass/${data.pass_id}`, '_blank');
    }

    // Scroll to result
    container.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// ============ TICKET BOOKING ============
async function bookTicket() {
    if (!currentUser) { showToast('Please login first', 'error'); return; }

    const source = document.getElementById('ticketSource').value.trim();
    const destination = document.getElementById('ticketDest').value.trim();

    let hasError = false;
    if (!source) { showFieldError('ticketSource', 'Source is required'); hasError = true; }
    if (!destination) { showFieldError('ticketDest', 'Destination is required'); hasError = true; }
    if (source && destination && source.toLowerCase() === destination.toLowerCase()) {
        showFieldError('ticketDest', 'Destination must differ from source');
        hasError = true;
    }
    if (hasError) return;

    // Find the fare for this route
    const route = ROUTES.find(r =>
        r.source.toLowerCase() === source.toLowerCase() &&
        r.destination.toLowerCase() === destination.toLowerCase()
    );

    if (!route) {
        showToast('Route not available. Please select a bus from the list.', 'error');
        return;
    }

    // Set pending ticket and redirect to payment
    pendingTicket = {
        source: route.source,
        destination: route.destination,
        fare: route.fare,
        busName: route.busName
    };

    showToast(`Redirecting to payment for ${route.source} → ${route.destination} (₹${route.fare})...`, 'info');

    // Switch to payment tab — context will be auto-updated
    switchDashTab('payment');
}

function displayBookedTicket(data, source, destination) {
    const container = document.getElementById('bookedTicketContainer');
    container.classList.remove('hidden');

    document.getElementById('genTicketId').textContent = `#TKT-${data.ticket_id}`;
    document.getElementById('genTicketSource').textContent = source;
    document.getElementById('genTicketDest').textContent = destination;
    document.getElementById('genTicketFare').textContent = `₹${data.fare}`;
    document.getElementById('genTicketDate').textContent = new Date().toLocaleDateString('en-IN', {
        year: 'numeric', month: 'short', day: 'numeric'
    });

    // Set QR code
    const qrImg = document.getElementById('genTicketQR');
    if (data.qr_url) {
        qrImg.innerHTML = `<img src="${data.qr_url}" alt="QR Code">`;
    } else {
        qrImg.innerHTML = generateSVGQR();
    }

    // Download
    const downloadBtn = document.getElementById('btnDownloadTicket');
    if (data.pdf_url) {
        downloadBtn.onclick = () => window.open(data.pdf_url, '_blank');
    } else {
        downloadBtn.onclick = () => window.open(`${API_BASE_URL}/download-ticket/${data.ticket_id}`, '_blank');
    }

    // Clear the fare summary since ticket is booked
    const fareSummary = document.getElementById('ticketFareSummary');
    if (fareSummary) fareSummary.classList.add('hidden');

    container.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// ============ DASHBOARD UI UPDATES ============
function updateDashboardUI() {
    if (!currentUser) return;

    // Sidebar user info
    document.getElementById('sidebarUserName').textContent = currentUser.name;
    document.getElementById('sidebarUserEmail').textContent = currentUser.email;
    document.getElementById('sidebarAvatarLetter').textContent = currentUser.name.charAt(0).toUpperCase();

    updateDashboardOverview();
    loadRecentActivity();
}

function updateDashboardOverview() {
    document.getElementById('totalPasses').textContent = appState.passes.length;
    document.getElementById('totalTickets').textContent = appState.tickets.length;
    document.getElementById('totalPayments').textContent = appState.payments.length;
}

function loadRecentActivity() {
    const list = document.getElementById('activityList');
    if (!list) return;

    if (appState.passes.length === 0 && appState.tickets.length === 0 && appState.payments.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <p>No recent activity yet. Start by making a payment or booking a pass!</p>
            </div>
        `;
        return;
    }

    list.innerHTML = '';

    // Combine and show recent items
    const allItems = [];

    appState.passes.forEach(p => {
        allItems.push({
            type: 'pass',
            title: `Bus Pass #${p.pass_id}`,
            subtitle: `${p.pass_type || 'Standard'} • Issue: ${p.issue_date || 'Today'}`,
            amount: p.pass_type || 'Pass',
            status: 'Active',
            icon: 'blue'
        });
    });

    appState.tickets.forEach(t => {
        allItems.push({
            type: 'ticket',
            title: `Ticket ${t.source || ''} → ${t.destination || ''}`,
            subtitle: `Ticket #${t.ticket_id} • Fare: ₹${t.fare || '0'}`,
            amount: `₹${t.fare || '0'}`,
            status: 'Booked',
            icon: 'green'
        });
    });

    appState.payments.forEach(p => {
        allItems.push({
            type: 'payment',
            title: `Payment #${p.payment_id}`,
            subtitle: `Amount: ₹${parseFloat(p.amount).toFixed(2)}`,
            amount: `₹${parseFloat(p.amount).toFixed(2)}`,
            status: p.status || 'Success',
            icon: 'purple'
        });
    });

    // Show last 5 items (reversed for newest first)
    allItems.reverse().slice(0, 5).forEach(item => {
        const iconSvgs = {
            blue: `<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"/></svg>`,
            green: `<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`,
            purple: `<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`
        };

        list.innerHTML += `
            <div class="activity-item">
                <div class="activity-left">
                    <div class="activity-icon ${item.icon}">${iconSvgs[item.icon]}</div>
                    <div class="activity-details">
                        <h4>${item.title}</h4>
                        <p>${item.subtitle}</p>
                    </div>
                </div>
                <div class="activity-right">
                    <div class="activity-amount">${item.amount}</div>
                    <div class="activity-status success">${item.status}</div>
                </div>
            </div>
        `;
    });
}

// ============ MODAL ============
function showModal(modalId) {
    document.getElementById(modalId).classList.add('open');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('open');
}

// ============ UTILITIES ============
function generateSVGQR() {
    return `<svg viewBox="0 0 100 100" shape-rendering="crispEdges">
        <path fill="#0f172a" d="M0 0h30v30H0zm40 0h20v10H40zm30 0h30v30H70zM10 10h10v10H10zm60 0h10v10H70zM0 40h10v20H0zm20 0h20v10H20zm30 0h10v10H30zm20 0h20v20H70zm-40 20h20v10H30zm40 10h20v30H80zM0 70h30v30H0zm10 10h10v10H10zm40 0h20v20H50zm10-30h10v10H60z"/>
        <path fill="#2563eb" d="M30 30h10v10H30zm30 30h10v10H60zm-30 20h10v10H30zM0 30h10v10H0zm90 0h10v10H90zm-10 10h10v10H80zM30 0h10v10H30z"/>
    </svg>`;
}

function animateCounters() {
    const counters = document.querySelectorAll('.counter');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = parseInt(entry.target.dataset.target);
                const suffix = entry.target.dataset.suffix || '';
                animateValue(entry.target, 0, target, 2000, suffix);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.3 });

    counters.forEach(counter => observer.observe(counter));
}

function animateValue(element, start, end, duration, suffix) {
    const startTime = performance.now();
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // Ease out cubic
        const current = Math.floor(start + (end - start) * eased);
        element.textContent = current.toLocaleString() + suffix;
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ============ BUS SVG ICON (reusable) ============
function getBusSVG() {
    return `<svg viewBox="0 0 24 24"><path d="M18 11H6V6h12v5zm1.5-7h-15C3.67 4 3 4.67 3 5.5v12c0 .83.67 1.5 1.5 1.5h1.22c-.41.69-.72 1.57-.72 2.5 0 .28.22.5.5.5h1.5c.28 0 .5-.22.5-.5 0-1.66 1.34-3 3-3h6c1.66 0 3 1.34 3 3 0 .28.22.5.5.5h1.5c.28 0 .5-.22.5-.5 0-.93-.31-1.81-.72-2.5h1.22c.83 0 1.5-.67 1.5-1.5v-12c0-.83-.67-1.5-1.5-1.5zM17 16H7v-2h10v2zm0-4H7V9h10v3z"/></svg>`;
}
