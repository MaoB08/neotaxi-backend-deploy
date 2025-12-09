// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';
let authToken = null;
let userData = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setupEventListeners();
});

// Check authentication
function checkAuth() {
    authToken = localStorage.getItem('authToken');
    const userDataStr = localStorage.getItem('userData');

    if (!authToken || !userDataStr) {
        window.location.href = '/login.html';
        return;
    }

    userData = JSON.parse(userDataStr);

    // Verificar que sea usuario tipo "user" (admin)
    if (userData.user_type !== 'user') {
        alert('Acceso denegado. Solo administradores pueden acceder a este panel.');
        logout();
        return;
    }

    updateUserInfo();
    loadDashboardData();
}

// Update user info in sidebar
function updateUserInfo() {
    const userName = document.getElementById('userName');
    const userEmail = document.getElementById('userEmail');
    const userInitials = document.getElementById('userInitials');

    if (userData) {
        userName.textContent = userData.name || 'Administrador';
        userEmail.textContent = userData.email || '';

        // Get initials
        const nameParts = (userData.name || 'AD').split(' ');
        const initials = nameParts.length >= 2
            ? nameParts[0][0] + nameParts[1][0]
            : nameParts[0].substring(0, 2);
        userInitials.textContent = initials.toUpperCase();
    }
}

// Setup event listeners
function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            navigateToSection(section);
        });
    });

    // Logout button
    document.getElementById('logoutBtn').addEventListener('click', logout);

    // Refresh buttons
    document.getElementById('refreshDriversBtn')?.addEventListener('click', loadDrivers);
    document.getElementById('refreshClientsBtn')?.addEventListener('click', loadClients);
    document.getElementById('refreshTripsBtn')?.addEventListener('click', loadTrips);
    document.getElementById('refreshAlertsBtn')?.addEventListener('click', loadAlerts);
}

// Navigate to section
function navigateToSection(section) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-section="${section}"]`).classList.add('active');

    // Update content
    document.querySelectorAll('.content-section').forEach(sec => {
        sec.classList.remove('active');
    });
    document.getElementById(section).classList.add('active');

    // Update page title
    const titles = {
        dashboard: 'Dashboard',
        drivers: 'Gestión de Conductores',
        clients: 'Gestión de Clientes',
        trips: 'Gestión de Viajes',
        alerts: 'Gestión de Alertas'
    };
    document.getElementById('pageTitle').textContent = titles[section] || 'Dashboard';

    // Load data for section
    switch (section) {
        case 'drivers':
            loadDrivers();
            break;
        case 'clients':
            loadClients();
            break;
        case 'trips':
            loadTrips();
            break;
        case 'alerts':
            loadAlerts();
            break;
    }
}

// Logout
function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    window.location.href = '/login.html';
}

// API Helper
async function apiRequest(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(authToken && { 'Authorization': `Bearer ${authToken}` })
        }
    };

    console.log(`🌐 API Request: ${endpoint}`, { authToken: authToken ? 'Present' : 'Missing' });

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    });

    console.log(`📡 API Response: ${endpoint}`, { status: response.status, ok: response.ok });

    if (response.status === 401) {
        console.error('❌ Unauthorized - logging out');
        logout();
        throw new Error('No autorizado');
    }

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
        console.error(`❌ API Error: ${endpoint}`, errorData);
        throw new Error(errorData.detail || `Error ${response.status}`);
    }

    return response.json();
}

// Load Dashboard Data
// Load Dashboard Data
// Load Dashboard Data
async function loadDashboardData() {
    let driversData = [], clientsData = [], tripsData = [];

    // Cargar datos individualmente para evitar fallos en cascada
    try { driversData = await apiRequest('/drivers'); } catch (e) { console.error('Error loading drivers for dashboard:', e); }
    try { clientsData = await apiRequest('/clients'); } catch (e) { console.error('Error loading clients for dashboard:', e); }
    try { tripsData = await apiRequest('/trips'); } catch (e) { console.error('Error loading trips for dashboard:', e); }

    try {
        // ===== CONDUCTORES =====
        const activeDrivers = driversData ? driversData.filter(d => d.status === 'A' || d.status === 'APPROVED').length : 0;
        const pendingDrivers = driversData ? driversData.filter(d => d.status === 'P' || d.status === 'PENDING').length : 0;
        document.getElementById('activeDrivers').textContent = activeDrivers;

        const driversChangeEl = document.querySelector('#activeDrivers').parentElement.querySelector('.stat-change');
        if (pendingDrivers > 0) {
            driversChangeEl.textContent = `${pendingDrivers} pendiente${pendingDrivers > 1 ? 's' : ''} de aprobación`;
            driversChangeEl.className = 'stat-change warning';
        } else {
            driversChangeEl.textContent = 'Todos aprobados';
            driversChangeEl.className = 'stat-change positive';
        }

        // ===== CLIENTES =====
        const totalClients = clientsData ? clientsData.length : 0;
        document.getElementById('totalClients').textContent = totalClients;
        const clientsChangeEl = document.querySelector('#totalClients').parentElement.querySelector('.stat-change');
        if (clientsData && clientsData.length > 0) {
            clientsChangeEl.textContent = 'Total registrados';
            clientsChangeEl.className = 'stat-change positive';
        } else {
            clientsChangeEl.textContent = 'Sin registros';
            clientsChangeEl.className = 'stat-change';
        }


        // ===== VIAJES DE HOY =====
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const today = `${year}-${month}-${day}`;
        const todayTrips = tripsData ? tripsData.filter(t => t.start_time?.startsWith(today)) : [];
        document.getElementById('todayTrips').textContent = todayTrips.length;

        // Viajes activos (en curso) - Filtrar "zombies" (>24h)
        const oneDayAgo = new Date(now - 24 * 60 * 60 * 1000);
        const activeTrips = tripsData ? tripsData.filter(t => {
            const isStatusActive = t.status === 'N' || t.status === 'ACTIVE';
            const tripDate = new Date(t.start_time);
            return isStatusActive && tripDate > oneDayAgo;
        }) : [];

        const todayTripsChangeEl = document.querySelector('#todayTrips').parentElement.querySelector('.stat-change');
        if (activeTrips.length > 0) {
            todayTripsChangeEl.textContent = `${activeTrips.length} en curso ahora`;
            todayTripsChangeEl.className = 'stat-change positive';
        } else {
            todayTripsChangeEl.textContent = 'Ninguno en curso';
            todayTripsChangeEl.className = 'stat-change';
        }

        // ===== TOTAL VIAJES =====
        const totalTrips = tripsData ? tripsData.length : 0;
        const completedTrips = tripsData ? tripsData.filter(t => t.status === 'F' || t.status === 'COMPLETED').length : 0;
        document.getElementById('totalTrips').textContent = totalTrips;

        const totalTripsChangeEl = document.querySelector('#totalTrips').parentElement.querySelector('.stat-change');
        if (totalTrips > 0) {
            const completionRate = ((completedTrips / totalTrips) * 100).toFixed(1);
            totalTripsChangeEl.textContent = `${completionRate}% completados`;
            totalTripsChangeEl.className = 'stat-change positive';
        } else {
            totalTripsChangeEl.textContent = 'Sin viajes aún';
            totalTripsChangeEl.className = 'stat-change';
        }

        // ===== ACTIVIDAD RECIENTE =====
        await loadRecentActivity(driversData || [], clientsData || [], tripsData || []);

    } catch (error) {
        console.error('Error processing dashboard data:', error);
        // No mostramos notificación de error aquí para no saturar, ya que los datos parciales podrían haberse cargado
    }
}

// Load Recent Activity
async function loadRecentActivity(drivers, clients, trips) {
    const activityList = document.getElementById('activityList');
    const activities = [];

    // Cargar alertas recientes
    let alerts = [];
    try {
        alerts = await apiRequest('/alerts');
    } catch (e) {
        console.error('Error loading alerts for dashboard:', e);
    }

    // Alertas recientes (últimas 24 horas, nivel alto)
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    const recentAlerts = alerts
        .filter(a => {
            const alertDate = new Date(a.datetime);
            return alertDate > oneDayAgo && a.level >= 4; // Solo nivel 4 y 5
        })
        .sort((a, b) => new Date(b.datetime) - new Date(a.datetime))
        .slice(0, 2);

    recentAlerts.forEach(alert => {
        const levelText = alert.level === 5 ? 'Crítica' : 'Alta';
        activities.push({
            icon: '🚨',
            title: `Alerta ${levelText}: ${alert.description || 'Sin descripción'}`,
            time: formatTimeAgo(alert.datetime),
            type: 'warning'
        });
    });

    // Clientes nuevos (últimos 7 días)
    const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    const newClients = clients
        .filter(c => {
            // Asumimos que tienen un campo created_at o registration_date
            // Si no existe, los mostramos todos como "nuevos"
            if (c.created_at) {
                const clientDate = new Date(c.created_at);
                return clientDate > oneWeekAgo;
            }
            return false; // Si no hay fecha, no lo mostramos como nuevo
        })
        .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
        .slice(0, 2);

    newClients.forEach(client => {
        activities.push({
            icon: '👥',
            title: `Nuevo cliente: ${client.first_name} ${client.last_name}`,
            time: formatTimeAgo(client.created_at),
            type: 'success'
        });
    });

    // Conductores pendientes
    const pendingDrivers = drivers.filter(d => d.status === 'P' || d.status === 'PENDING');
    pendingDrivers.slice(0, 2).forEach(driver => {
        activities.push({
            icon: '👤',
            title: `Conductor pendiente: ${driver.first_name} ${driver.last_name}`,
            time: 'Requiere aprobación',
            type: 'warning'
        });
    });

    // Viajes activos
    const activeTrips = trips.filter(t => t.status === 'N' || t.status === 'ACTIVE');
    activeTrips.slice(0, 2).forEach(trip => {
        activities.push({
            icon: '🚗',
            title: `Viaje en curso: ${trip.origin_neighborhood || 'Origen'} → ${trip.destination_neighborhood || 'Destino'}`,
            time: formatTimeAgo(trip.start_time),
            type: 'active'
        });
    });

    // Viajes recientes completados
    const recentCompleted = trips
        .filter(t => t.status === 'F' || t.status === 'COMPLETED')
        .sort((a, b) => new Date(b.end_time || b.start_time) - new Date(a.end_time || a.start_time))
        .slice(0, 2);

    recentCompleted.forEach(trip => {
        activities.push({
            icon: '✅',
            title: `Viaje completado: ${trip.origin_neighborhood || 'Origen'} → ${trip.destination_neighborhood || 'Destino'}`,
            time: formatTimeAgo(trip.end_time || trip.start_time),
            type: 'success'
        });
    });

    // Si no hay actividades
    if (activities.length === 0) {
        activityList.innerHTML = `
            <div class="activity-item">
                <div class="activity-icon">📊</div>
                <div class="activity-content">
                    <div class="activity-title">No hay actividad reciente</div>
                    <div class="activity-time">El sistema está listo para operar</div>
                </div>
            </div>
        `;
        return;
    }

    // Ordenar por prioridad: alertas críticas primero, luego por tiempo
    activities.sort((a, b) => {
        // Alertas críticas primero
        if (a.type === 'warning' && a.icon === '🚨' && b.type !== 'warning') return -1;
        if (b.type === 'warning' && b.icon === '🚨' && a.type !== 'warning') return 1;
        return 0;
    });

    // Renderizar actividades (máximo 8)
    activityList.innerHTML = activities.slice(0, 8).map(activity => `
        <div class="activity-item ${activity.type || ''}">
            <div class="activity-icon">${activity.icon}</div>
            <div class="activity-content">
                <div class="activity-title">${activity.title}</div>
                <div class="activity-time">${activity.time}</div>
            </div>
        </div>
    `).join('');
}

// Format time ago
function formatTimeAgo(dateString) {
    if (!dateString) return 'Hace un momento';

    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Hace un momento';
        if (diffMins < 60) return `Hace ${diffMins} minuto${diffMins > 1 ? 's' : ''}`;
        if (diffHours < 24) return `Hace ${diffHours} hora${diffHours > 1 ? 's' : ''}`;
        if (diffDays < 7) return `Hace ${diffDays} día${diffDays > 1 ? 's' : ''}`;
        return formatDate(dateString);
    } catch (e) {
        return 'Recientemente';
    }
}

// Load Drivers
async function loadDrivers() {
    const tbody = document.getElementById('driversTableBody');
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Cargando conductores...</td></tr>';

    try {
        const drivers = await apiRequest('/drivers');

        // Store data globally for sorting
        driversData = drivers;

        // Render using the new render function
        renderDriversTable(drivers);

    } catch (error) {
        console.error('Error loading drivers:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="loading">Error al cargar conductores</td></tr>';
        showNotification('Error al cargar conductores', 'error');
    }
}

// Load Clients
async function loadClients() {
    const tbody = document.getElementById('clientsTableBody');
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Cargando clientes...</td></tr>';

    try {
        const clients = await apiRequest('/clients');

        // Store data globally for sorting
        clientsData = clients;

        // Render using the new render function
        renderClientsTable(clients);

    } catch (error) {
        console.error('Error loading clients:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="loading">Error al cargar clientes</td></tr>';
        showNotification('Error al cargar clientes', 'error');
    }
}

// Load Trips
async function loadTrips() {
    const tbody = document.getElementById('tripsTableBody');
    tbody.innerHTML = '<tr><td colspan="7" class="loading">Cargando viajes...</td></tr>';

    try {
        const trips = await apiRequest('/trips');

        // Store data globally for sorting
        tripsData = trips;

        // Render using the new render function
        renderTripsTable(trips);

    } catch (error) {
        console.error('Error loading trips:', error);
        tbody.innerHTML = '<tr><td colspan="7" class="loading">Error al cargar viajes</td></tr>';
        showNotification('Error al cargar viajes', 'error');
    }
}

// Approve Driver
async function approveDriver(document) {
    if (!confirm('¿Estás seguro de aprobar este conductor?')) return;

    try {
        await apiRequest(`/drivers/${document}/approve`, {
            method: 'POST',
            body: JSON.stringify({ status: 'APPROVED' })
        });

        showNotification('Conductor aprobado exitosamente', 'success');
        loadDrivers();
        loadDashboardData();
    } catch (error) {
        console.error('Error approving driver:', error);
        showNotification('Error al aprobar conductor: ' + error.message, 'error');
    }
}

// Reject Driver
async function rejectDriver(document) {
    if (!confirm('¿Estás seguro de rechazar este conductor?')) return;

    try {
        await apiRequest(`/drivers/${document}`, {
            method: 'DELETE'
        });

        showNotification('Conductor rechazado', 'success');
        loadDrivers();
        loadDashboardData();
    } catch (error) {
        console.error('Error rejecting driver:', error);
        showNotification('Error al rechazar conductor', 'error');
    }
}

// View Driver
function viewDriver(document) {
    alert(`Ver detalles del conductor: ${document}\n(Funcionalidad por implementar)`);
}

// View Client
function viewClient(document) {
    alert(`Ver detalles del cliente: ${document}\n(Funcionalidad por implementar)`);
}

// Get Status Badge
function getStatusBadge(status) {
    const statusMap = {
        'A': { text: 'Aprobado', class: 'approved' },
        'APPROVED': { text: 'Aprobado', class: 'approved' },
        'P': { text: 'Pendiente', class: 'pending' },
        'PENDING': { text: 'Pendiente', class: 'pending' },
        'I': { text: 'Inactivo', class: 'inactive' },
        'INACTIVE': { text: 'Inactivo', class: 'inactive' }
    };

    const statusInfo = statusMap[status] || { text: status, class: 'pending' };
    return `<span class="status-badge ${statusInfo.class}">${statusInfo.text}</span>`;
}

// Get Trip Status Badge
function getTripStatusBadge(status) {
    const statusMap = {
        'ACTIVE': { text: 'Activo', class: 'active' },
        'COMPLETED': { text: 'Completado', class: 'completed' },
        'CANCELLED': { text: 'Cancelado', class: 'inactive' }
    };

    const statusInfo = statusMap[status] || { text: status, class: 'pending' };
    return `<span class="status-badge ${statusInfo.class}">${statusInfo.text}</span>`;
}

// Format Date
function formatDate(dateString) {
    if (!dateString) return 'N/A';

    const date = new Date(dateString);
    return date.toLocaleString('es-CO', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Show Notification
function showNotification(message, type = 'info') {
    // Simple alert for now - can be enhanced with a toast library
    if (type === 'error') {
        alert('❌ ' + message);
    } else if (type === 'success') {
        alert('✅ ' + message);
    } else {
        alert('ℹ️ ' + message);
    }
}

// ==================== TABLE SORTING ====================

// Store original data for sorting
let driversData = [];
let clientsData = [];
let tripsData = [];
let alertsData = [];

// Setup sorting for all tables
function setupTableSorting() {
    // Setup sorting for each table
    setupSortingForTable('driversTableBody', 'drivers');
    setupSortingForTable('clientsTableBody', 'clients');
    setupSortingForTable('tripsTableBody', 'trips');
    setupSortingForTable('alertsTableBody', 'alerts');
}

function setupSortingForTable(tableBodyId, dataType) {
    const tbody = document.getElementById(tableBodyId);
    if (!tbody) return;

    const table = tbody.closest('table');
    const headers = table.querySelectorAll('th.sortable');

    headers.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.dataset.column;
            const currentSort = header.classList.contains('sort-asc') ? 'asc' :
                header.classList.contains('sort-desc') ? 'desc' : 'none';

            // Remove sort classes from all headers
            headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));

            // Determine new sort direction
            let newSort = 'asc';
            if (currentSort === 'asc') {
                newSort = 'desc';
            }

            // Add appropriate class
            header.classList.add(`sort-${newSort}`);

            // Sort the data
            sortTable(dataType, column, newSort);
        });
    });
}

function sortTable(dataType, column, direction) {
    let data;
    let renderFunction;

    // Get the appropriate data and render function
    switch (dataType) {
        case 'drivers':
            data = [...driversData];
            renderFunction = renderDriversTable;
            break;
        case 'clients':
            data = [...clientsData];
            renderFunction = renderClientsTable;
            break;
        case 'trips':
            data = [...tripsData];
            renderFunction = renderTripsTable;
            break;
        case 'alerts':
            data = [...alertsData];
            renderFunction = renderAlertsTable;
            break;
        default:
            return;
    }

    // Sort the data
    data.sort((a, b) => {
        let aVal = getNestedValue(a, column);
        let bVal = getNestedValue(b, column);

        // Handle null/undefined
        if (aVal === null || aVal === undefined) aVal = '';
        if (bVal === null || bVal === undefined) bVal = '';

        // Convert to string for comparison
        aVal = String(aVal).toLowerCase();
        bVal = String(bVal).toLowerCase();

        // Compare
        if (aVal < bVal) return direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return direction === 'asc' ? 1 : -1;
        return 0;
    });

    // Render the sorted data
    renderFunction(data);
}

function getNestedValue(obj, path) {
    // Handle special cases for combined fields
    if (path === 'name') {
        return `${obj.first_name || ''} ${obj.last_name || ''}`.trim();
    }
    if (path === 'license') {
        return obj.license_number || obj.license || '';
    }

    return obj[path];
}

function renderDriversTable(drivers) {
    const tbody = document.getElementById('driversTableBody');

    if (drivers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No hay conductores registrados</td></tr>';
        return;
    }

    tbody.innerHTML = drivers.map(driver => `
        <tr>
            <td>${driver.document}</td>
            <td>${driver.first_name} ${driver.last_name}</td>
            <td>${driver.email}</td>
            <td>${driver.license_number || driver.license || 'N/A'}</td>
            <td>${getStatusBadge(driver.status)}</td>
            <td>
                <div class="action-btns">
                    ${(driver.status === 'P' || driver.status === 'PENDING') ? `
                        <button class="btn-action btn-approve" onclick="approveDriver('${driver.document}')">
                            Aprobar
                        </button>
                        <button class="btn-action btn-reject" onclick="rejectDriver('${driver.document}')">
                            Rechazar
                        </button>
                    ` : `
                        ${(driver.status === 'A' || driver.status === 'APPROVED' || driver.status === 'ACTIVE') ? `
                            <button class="btn-action btn-reject" onclick="toggleDriverStatus('${driver.document}', 'INACTIVE', 'INACTIVO')">
                                Desactivar
                            </button>
                        ` : `
                            <button class="btn-action btn-approve" onclick="toggleDriverStatus('${driver.document}', 'ACTIVE', 'ACTIVO')">
                                Activar
                            </button>
                        `}
                        <button class="btn-action btn-view" onclick="viewDriver('${driver.document}')">
                            Ver
                        </button>
                    `}
                </div>
            </td>
        </tr>
    `).join('');
}

function renderClientsTable(clients) {
    const tbody = document.getElementById('clientsTableBody');

    if (clients.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No hay clientes registrados</td></tr>';
        return;
    }

    tbody.innerHTML = clients.map(client => `
        <tr>
            <td>${client.document}</td>
            <td>${client.first_name} ${client.last_name}</td>
            <td>${client.email}</td>
            <td>${client.phone || 'N/A'}</td>
            <td>
                <div class="action-btns">
                    <button class="btn-action btn-view" onclick="viewClient('${client.document}')">
                        Ver
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function renderTripsTable(trips) {
    const tbody = document.getElementById('tripsTableBody');

    if (trips.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No hay viajes registrados</td></tr>';
        return;
    }

    tbody.innerHTML = trips.map(trip => `
    <tr>
        <td>${trip.trip_id || trip.id || 'N/A'}</td>
        <td>${trip.client_document || 'N/A'}</td>
        <td>${trip.driver_document || 'N/A'}</td>
        <td>${trip.origin_neighborhood || 'N/A'}</td>
        <td>${trip.destination_neighborhood || 'N/A'}</td>
        <td>${getTripStatusBadge(trip.status)}</td>
        <td>${formatDate(trip.start_time)}</td>
        <td>
            <div class="action-btns">
                ${(trip.status === 'N' || trip.status === 'ACTIVE') ? `
                        <button class="btn-action btn-approve" title="Finalizar Viaje" onclick="endTrip(${trip.trip_id || trip.id})">
                            🏁
                        </button>
                    ` : ''}
                <button class="btn-action btn-reject" title="Eliminar Viaje" onclick="deleteTrip(${trip.trip_id || trip.id})">
                    🗑️
                </button>
            </div>
        </td>
    </tr>
    `).join('');
}

// End Trip (Manually)
async function endTrip(tripId) {
    if (!confirm('¿Estás seguro de finalizar este viaje manualmente?')) return;

    try {
        await apiRequest(`/trips/${tripId}/finish`, {
            method: 'PUT'
        });

        showNotification('Viaje finalizado exitosamente', 'success');
        loadTrips();
        loadDashboardData();
    } catch (error) {
        console.error('Error ending trip:', error);
        showNotification('Error al finalizar viaje: ' + error.message, 'error');
    }
}

// Delete Trip
async function deleteTrip(tripId) {
    if (!confirm('¿Estás SEGURO de eliminar este viaje? Esta acción no se puede deshacer.')) return;

    try {
        await apiRequest(`/trips/${tripId}`, {
            method: 'DELETE'
        });

        showNotification('Viaje eliminado exitosamente', 'success');
        loadTrips();
        loadDashboardData();
    } catch (error) {
        console.error('Error deleting trip:', error);
        showNotification('Error al eliminar viaje: ' + error.message, 'error');
    }
}

// Toggle Driver Status Active/Inactive
async function toggleDriverStatus(document, newStatus, actionName) {
    if (!confirm(`¿Estás seguro de cambiar el estado del conductor a ${actionName}?`)) return;

    try {
        await apiRequest(`/drivers/${document}/approve`, {
            method: 'POST',
            body: JSON.stringify({ status: newStatus })
        });

        showNotification('Estado del conductor actualizado correctamente', 'success');
        loadDrivers();
        loadDashboardData();
    } catch (error) {
        console.error('Error updating driver status:', error);
        showNotification('Error al actualizar estado: ' + error.message, 'error');
    }
}

// Initialize sorting when page loads
document.addEventListener('DOMContentLoaded', () => {
    setupTableSorting();
});

// Make functions globally available
window.approveDriver = approveDriver;
window.rejectDriver = rejectDriver;
window.viewDriver = viewDriver;
window.viewClient = viewClient;
window.endTrip = endTrip;
window.deleteTrip = deleteTrip;
window.toggleDriverStatus = toggleDriverStatus;

// Load Alerts
async function loadAlerts() {
    const tbody = document.getElementById('alertsTableBody');
    tbody.innerHTML = '<tr><td colspan="7" class="loading">Cargando alertas...</td></tr>';

    try {
        // Ensure we have reference data for resolving names
        const promises = [apiRequest('/alerts')];

        if (clientsData.length === 0) {
            promises.push(apiRequest('/clients').then(data => { clientsData = data; return data; }));
        }

        if (driversData.length === 0) {
            promises.push(apiRequest('/drivers').then(data => { driversData = data; return data; }));
        }

        const results = await Promise.all(promises);
        const alerts = results[0];

        // Store data globally for sorting
        alertsData = alerts;

        renderAlertsTable(alerts);
    } catch (error) {
        console.error('Error loading alerts:', error);
        tbody.innerHTML = '<tr><td colspan="7" class="loading">Error al cargar alertas</td></tr>';
        showNotification('Error al cargar alertas', 'error');
    }
}

// Render Alerts Table
function renderAlertsTable(alerts) {
    const tbody = document.getElementById('alertsTableBody');

    if (alerts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">No hay alertas registradas</td></tr>';
        return;
    }

    tbody.innerHTML = alerts.map(alert => {
        // Log para debugging
        console.log('Alert data:', alert);
        console.log('Trip ID:', alert.trip_id);

        // Resolve User Name
        let userName = 'No registrado';
        let userDoc = alert.facial_encodings?.user_document || alert.user_document || 'N/A';

        if (alert.facial_encodings) {
            // Fix: biometric_record uses 'client_document', not 'user_document'
            // We use the property that actually exists
            const doc = alert.facial_encodings.client_document || alert.facial_encodings.user_document;
            const type = alert.facial_encodings.user_type || 'client';

            if (doc) {
                if (type === 'client' || type === 'CLIENT') {
                    const client = clientsData.find(c => c.document === doc);
                    if (client) userName = `${client.first_name} ${client.last_name}`;
                } else {
                    const driver = driversData.find(d => d.document === doc);
                    if (driver) userName = `${driver.first_name} ${driver.last_name}`;
                }
            }
        } else if (alert.user_document) {
            // Fallback if direct user_document exists (legacy or direct alert)
            const client = clientsData.find(c => c.document === alert.user_document);
            const driver = driversData.find(d => d.document === alert.user_document);
            if (client) userName = `${client.first_name} ${client.last_name} (C)`;
            else if (driver) userName = `${driver.first_name} ${driver.last_name} (D)`;
        }

        // Resolve Alert Type
        let alertType = 'No registrado';
        if (alert.antecedent?.type?.name) {
            alertType = alert.antecedent.type.name;
        } else if (alert.alert_type) {
            alertType = alert.alert_type; // Fallback if exists directly
        }

        return `
        <tr>
            <td>${alert.alert_id || alert.id || 'N/A'}</td>
            <td>${alert.trip_id || 'N/A'}</td>
            <td>${userDoc}</td>
            <td>${alertType}</td>
            <td>${alert.description || 'N/A'}</td>
            <td>${getAlertLevelBadge(alert.level)}</td>
            <td>${formatDate(alert.datetime)}</td>
        </tr>
        `;
    }).join('');
}

// Get Alert Level Badge
function getAlertLevelBadge(level) {
    const levelInt = parseInt(level);

    // Scale 1-5
    if (levelInt === 1) return `<span class="status-badge success">Baja (1)</span>`;
    if (levelInt === 2) return `<span class="status-badge success" style="background-color: #86efac; color: #14532d;">Leve (2)</span>`; // Light Green
    if (levelInt === 3) return `<span class="status-badge pending">Media (3)</span>`;
    if (levelInt === 4) return `<span class="status-badge warning" style="background-color: #fdba74; color: #7c2d12;">Alta (4)</span>`; // Orange
    if (levelInt === 5) return `<span class="status-badge inactive">Crítica (5)</span>`;

    // Fallback for legacy data
    if (String(level).toLowerCase() === 'high') return `<span class="status-badge inactive">Alta</span>`;
    if (String(level).toLowerCase() === 'medium') return `<span class="status-badge pending">Media</span>`;
    if (String(level).toLowerCase() === 'low') return `<span class="status-badge success">Baja</span>`;

    return `<span class="status-badge pending">Nivel ${level}</span>`;
}
