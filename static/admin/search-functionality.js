// ==================== SEARCH FUNCTIONALITY ====================

// Setup search for all tables
function setupSearch() {
    // Drivers search
    const searchDrivers = document.getElementById('searchDrivers');
    if (searchDrivers) {
        searchDrivers.addEventListener('input', (e) => {
            filterTable('driversTableBody', e.target.value, driversData);
        });
    }

    // Clients search
    const searchClients = document.getElementById('searchClients');
    if (searchClients) {
        searchClients.addEventListener('input', (e) => {
            filterTable('clientsTableBody', e.target.value, clientsData);
        });
    }

    // Trips search
    const searchTrips = document.getElementById('searchTrips');
    if (searchTrips) {
        searchTrips.addEventListener('input', (e) => {
            filterTable('tripsTableBody', e.target.value, tripsData);
        });
    }

    // Alerts search
    const searchAlerts = document.getElementById('searchAlerts');
    if (searchAlerts) {
        searchAlerts.addEventListener('input', (e) => {
            filterTable('alertsTableBody', e.target.value, alertsData);
        });
    }

    // Antecedents search
    const searchAntecedents = document.getElementById('searchAntecedents');
    if (searchAntecedents) {
        searchAntecedents.addEventListener('input', (e) => {
            filterTable('antecedentsTableBody', e.target.value, antecedentsData);
        });
    }
}

function filterTable(tableBodyId, searchTerm, data) {
    const term = searchTerm.toLowerCase().trim();

    if (!term) {
        // If search is empty, render all data
        switch (tableBodyId) {
            case 'driversTableBody':
                renderDriversTable(data);
                break;
            case 'clientsTableBody':
                renderClientsTable(data);
                break;
            case 'tripsTableBody':
                renderTripsTable(data);
                break;
            case 'alertsTableBody':
                renderAlertsTable(data);
                break;
            case 'antecedentsTableBody':
                renderAntecedentsTable(data);
                break;
        }
        return;
    }

    // Filter data based on search term
    const filtered = data.filter(item => {
        // Convert all values to string and search
        const searchableText = Object.values(item).join(' ').toLowerCase();
        return searchableText.includes(term);
    });

    // Render filtered data
    switch (tableBodyId) {
        case 'driversTableBody':
            renderDriversTable(filtered);
            break;
        case 'clientsTableBody':
            renderClientsTable(filtered);
            break;
        case 'tripsTableBody':
            renderTripsTable(filtered);
            break;
        case 'alertsTableBody':
            renderAlertsTable(filtered);
            break;
        case 'antecedentsTableBody':
            renderAntecedentsTable(filtered);
            break;
    }
}

// ==================== REFRESH BUTTONS ====================

// Dashboard refresh button
document.getElementById('refreshDashboardBtn')?.addEventListener('click', () => {
    loadDashboardData();
});

// Initialize search on page load
document.addEventListener('DOMContentLoaded', () => {
    setupSearch();
});
