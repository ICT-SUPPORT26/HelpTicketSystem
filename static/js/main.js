// Global variables and initialization
document.addEventListener('DOMContentLoaded', function() {
    // Enhanced Theme toggle functionality
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const body = document.body;

    // Get saved theme or default to light
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    // Apply saved theme with animation
    function applyTheme(theme, animate = false) {
        if (animate) {
            // Add transition class for smooth theme change
            body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
            setTimeout(() => {
                body.style.transition = '';
            }, 300);
        }

        if (theme === 'dark') {
            body.setAttribute('data-theme', 'dark');
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
            themeToggle.setAttribute('title', 'Switch to light mode');
        } else {
            body.removeAttribute('data-theme');
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
            themeToggle.setAttribute('title', 'Switch to dark mode');
        }
    }
    
    // Apply saved theme on load
    applyTheme(savedTheme);

    // Theme toggle event listener with enhanced animations
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            // Add button animation
            this.style.transform = 'scale(0.9)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);

            // Apply new theme with animation
            applyTheme(newTheme, true);
            localStorage.setItem('theme', newTheme);
        });
    }

    // Notification system
    const notificationsDropdown = document.getElementById('notificationsDropdown');
    const notificationsList = document.getElementById('notifications-list');
    const notificationBadge = document.getElementById('notification-badge');
    const markAllReadBtn = document.getElementById('mark-all-read');
    const clearAllBtn = document.getElementById('clear-all-notifications');

    // Load notifications
    function loadNotifications() {
        if (!notificationsList) return;

        fetch('/api/notifications')
            .then(response => response.json())
            .then(notifications => {
                if (notifications.length === 0) {
                    notificationsList.innerHTML = '<li class="dropdown-item text-center text-muted">No notifications</li>';
                    return;
                }

                notificationsList.innerHTML = '';
                notifications.forEach(notification => {
                    const notificationElement = document.createElement('li');
                    const isNew = !notification.is_read ? 'notification-new' : '';
                    const iconClass = getNotificationIcon(notification.type);
                    const colorClass = getNotificationColor(notification.type);

                    notificationElement.innerHTML = `
                        <a class="dropdown-item ${isNew} notification-item" 
                           href="#" 
                           data-notification-id="${notification.id}" 
                           data-notification-link="${notification.link || ''}"
                           data-is-read="${notification.is_read}"
                           style="cursor: pointer;">
                            <div class="d-flex align-items-start">
                                <div class="flex-shrink-0 me-3">
                                    <i class="fas fa-${iconClass} ${colorClass}"></i>
                                </div>
                                <div class="flex-grow-1">
                                    <h6 class="mb-1 ${!notification.is_read ? 'fw-bold' : ''}">${notification.title}</h6>
                                    <p class="mb-1 small text-muted">${notification.message.substring(0, 100)}${notification.message.length > 100 ? '...' : ''}</p>
                                    <small class="text-muted">${notification.created_at}</small>
                                    ${!notification.is_read ? '<span class="badge bg-primary ms-2" style="font-size: 0.6rem;">New</span>' : ''}
                                </div>
                            </div>
                        </a>
                    `;

                    // Add click event listener
                    const linkElement = notificationElement.querySelector('.dropdown-item');
                    linkElement.addEventListener('click', function(e) {
                        e.preventDefault();
                        const notificationId = this.getAttribute('data-notification-id');
                        const link = this.getAttribute('data-notification-link');
                        const isRead = this.getAttribute('data-is-read') === 'true';

                        // Visual feedback - mark as read immediately
                        if (!isRead) {
                            this.classList.remove('notification-new');
                            this.querySelector('h6').classList.remove('fw-bold');
                            const badge = this.querySelector('.badge');
                            if (badge) badge.remove();
                        }

                        handleNotificationClick(notificationId, link);
                    });

                    notificationsList.appendChild(notificationElement);
                });
            })
            .catch(error => {
                console.error('Error loading notifications:', error);
                if (notificationsList) {
                    notificationsList.innerHTML = '<li class="dropdown-item text-center text-danger">Error loading notifications</li>';
                }
            });
    }

    // Update unread count
    function updateUnreadCount() {
        fetch('/api/notifications/unread_count')
            .then(response => response.json())
            .then(data => {
                const count = data.count || 0;
                if (count > 0) {
                    notificationBadge.textContent = count > 99 ? '99+' : count;
                    notificationBadge.style.display = 'flex';
                    notificationBadge.classList.add('new-notification');

                    // Remove animation after 3 seconds
                    setTimeout(() => {
                        notificationBadge.classList.remove('new-notification');
                    }, 3000);
                } else {
                    notificationBadge.style.display = 'none';
                    notificationBadge.classList.remove('new-notification');
                }
            })
            .catch(error => {
                console.error('Error updating unread count:', error);
            });
    }

    // Get CSRF token from meta tag or form
    function getCSRFToken() {
        const token = document.querySelector('meta[name=csrf-token]');
        if (token) {
            return token.getAttribute('content');
        }
        // Fallback: get from any form with csrf_token
        const csrfInput = document.querySelector('input[name="csrf_token"]');
        return csrfInput ? csrfInput.value : '';
    }

    // Mark all as read
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const csrfToken = getCSRFToken();

            // Show loading state
            markAllReadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Marking...';
            markAllReadBtn.disabled = true;

            fetch('/api/notifications/mark_all_read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({})
            }).then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Immediately update badge to 0
                    if (notificationBadge) {
                        notificationBadge.style.display = 'none';
                        notificationBadge.textContent = '0';
                        notificationBadge.classList.remove('new-notification');
                    }

                    // Reload notifications and update count
                    updateUnreadCount();
                    loadNotifications();
                    showNotification(`Marked ${data.marked_count} notifications as read`, 'success');
                } else {
                    console.error('Failed to mark notifications as read');
                    showNotification('Failed to mark notifications as read', 'danger');
                }
            }).catch(error => {
                console.error('Error marking notifications as read:', error);
                showNotification('Error marking notifications as read', 'danger');
            }).finally(() => {
                // Restore button state
                markAllReadBtn.innerHTML = 'Mark all read';
                markAllReadBtn.disabled = false;
            });
        });
    }

    // Clear all notifications
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function(e) {
            e.preventDefault();

            if (!confirm('Are you sure you want to clear all notifications? This action cannot be undone.')) {
                return;
            }

            const csrfToken = getCSRFToken();

            // Show loading state
            clearAllBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Clearing...';
            clearAllBtn.disabled = true;

            fetch('/api/notifications/clear_all', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({})
            }).then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Immediately clear the badge
                    if (notificationBadge) {
                        notificationBadge.style.display = 'none';
                        notificationBadge.textContent = '0';
                        notificationBadge.classList.remove('new-notification');
                    }

                    // Clear the notifications list
                    if (notificationsList) {
                        notificationsList.innerHTML = '<li class="dropdown-item text-center text-muted">No notifications</li>';
                    }

                    showNotification(`Cleared ${data.cleared_count} notifications`, 'success');

                    // Update count to ensure consistency
                    updateUnreadCount();
                } else {
                    console.error('Failed to clear notifications');
                    showNotification('Failed to clear notifications', 'danger');
                }
            }).catch(error => {
                console.error('Error clearing notifications:', error);
                showNotification('Error clearing notifications', 'danger');
            }).finally(() => {
                // Restore button state
                clearAllBtn.innerHTML = 'Clear all';
                clearAllBtn.disabled = false;
            });
        });
    }

    if (notificationsDropdown && notificationsList && notificationBadge) {
        // Initial load
        loadNotifications();
        updateUnreadCount();

        // Refresh every 30 seconds
        setInterval(() => {
            updateUnreadCount();
        }, 30000);

        // Load notifications when dropdown is opened
        notificationsDropdown.addEventListener('show.bs.dropdown', loadNotifications);
    }

    // Request notification permission on page load
    if ("Notification" in window && Notification.permission === "default") {
        Notification.requestPermission();
    }

    // Utility functions
    function getNotificationIcon(type) {
        const icons = {
            'new_ticket': 'plus-circle',
            'ticket_updated': 'edit',
            'new_comment': 'comment',
            'ticket_closed': 'check-circle',
            'ticket_overdue': 'exclamation-triangle',
            'user_registered': 'user-plus',
            'account_approved': 'check-circle'
        };
        return icons[type] || 'bell';
    }

    function getNotificationColor(type) {
        const colors = {
            'new_ticket': 'text-success',
            'ticket_updated': 'text-warning',
            'new_comment': 'text-info',
            'ticket_closed': 'text-success',
            'ticket_overdue': 'text-danger',
            'user_registered': 'text-primary',
            'account_approved': 'text-success'
        };
        return colors[type] || 'text-primary';
    }

    // Show notification toast
    function showNotification(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }

    // Handle notification click
    window.handleNotificationClick = function(notificationId, link) {
        const csrfToken = getCSRFToken();

        // Mark as read
        fetch(`/api/notifications/${notificationId}/mark_read`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({})
        }).then(response => {
            if (response.ok) {
                // Immediately update the UI
                updateUnreadCount();
                loadNotifications();

                // Update badge if it exists
                if (notificationBadge) {
                    const currentCount = parseInt(notificationBadge.textContent) || 0;
                    const newCount = Math.max(0, currentCount - 1);
                    if (newCount === 0) {
                        notificationBadge.style.display = 'none';
                        notificationBadge.classList.remove('new-notification');
                    } else {
                        notificationBadge.textContent = newCount > 99 ? '99+' : newCount;
                    }
                }
            }
        }).catch(error => {
            console.error('Error marking notification as read:', error);
        });

        // Navigate to link
        if (link && link !== 'null' && link !== 'None') {
            window.location.href = link;
        }
    };

    // Auto-complete for ticket descriptions
    const descriptionInput = document.getElementById('description');
    if (descriptionInput) {
        let suggestionsCache = [];

        // Load suggestions
        fetch('/api/ticket_descriptions')
            .then(response => response.json())
            .then(data => {
                suggestionsCache = data;
            })
            .catch(error => {
                console.error('Error loading ticket descriptions:', error);
            });

        // Create datalist for suggestions
        const datalist = document.createElement('datalist');
        datalist.id = 'description-suggestions';
        descriptionInput.setAttribute('list', 'description-suggestions');
        descriptionInput.parentNode.appendChild(datalist);

        // Update suggestions on input
        descriptionInput.addEventListener('input', function() {
            const value = this.value.toLowerCase();
            const matches = suggestionsCache.filter(desc => 
                desc.toLowerCase().includes(value)
            ).slice(0, 10);

            datalist.innerHTML = '';
            matches.forEach(match => {
                const option = document.createElement('option');
                option.value = match;
                datalist.appendChild(option);
            });
        });
    }

    // Enhanced form validation
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });

            if (!isValid) {
                e.preventDefault();
                showNotification('Please fill in all required fields', 'danger');
            }
        });
    });

    // Real-time search functionality
    const searchInputs = document.querySelectorAll('[data-search]');
    searchInputs.forEach(input => {
        const targetTable = document.querySelector(input.dataset.search);
        if (targetTable) {
            input.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase();
                const rows = targetTable.querySelectorAll('tbody tr');

                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            });
        }
    });

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Dynamic form handling
    const locationSelect = document.getElementById('location');
    const locationUnitSelect = document.getElementById('location_unit');
    const locationSubunitSelect = document.getElementById('location_subunit');
    const locationDetailSelect = document.getElementById('location_detail');

    if (locationUnitSelect && locationSubunitSelect && locationDetailSelect) {
        const subunits = {
            'SWA': ['LSHR', 'USHR'],
            'UHS': ['Staff clinic', 'Student clinic', 'Account', 'Laboratory', 'ICEC', 'SickBay', 'Theatre', 'Gender Desk', 'CMO'],
            'Confucius': ['Block A', 'Block B', 'Block C', 'Auditorium', 'Library', 'Server Room']
        };

        const locations = {
            'LSHR': ['Hall 1', 'Hall 2', 'Hall 3', 'Hall 10', 'SMU', 'CCU', 'Hall 15', 'Sport Department', 'Hall 11', 'Kitchen 1'],
            'USHR': ['Hall 4', 'Hall 5', 'Hall 6', 'Hall 7', 'Hall 8', 'Hall 9', 'Mamlaka Unit', 'SWA HQ']
        };

        locationUnitSelect.addEventListener('change', function() {
            const selectedUnit = this.value;
            locationSubunitSelect.innerHTML = '<option value="">-- Select Subunit --</option>';
            locationDetailSelect.innerHTML = '<option value="">-- Select Location --</option>';

            if (selectedUnit && subunits[selectedUnit]) {
                subunits[selectedUnit].forEach(subunit => {
                    const option = document.createElement('option');
                    option.value = subunit;
                    option.textContent = subunit;
                    locationSubunitSelect.appendChild(option);
                });
            }
        });

        locationSubunitSelect.addEventListener('change', function() {
            const selectedSubunit = this.value;
            locationDetailSelect.innerHTML = '<option value="">-- Select Location --</option>';

            if (selectedSubunit && locations[selectedSubunit]) {
                locations[selectedSubunit].forEach(location => {
                    const option = document.createElement('option');
                    option.value = location;
                    option.textContent = location;
                    locationDetailSelect.appendChild(option);
                });
            }
        });
    }
});

// Global utility functions
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

function showPasswordModal(userId, userName) {
    const modal = document.getElementById('passwordModal');
    if (modal) {
        document.getElementById('userId').value = userId;
        document.getElementById('userName').textContent = userName;
        new bootstrap.Modal(modal).show();
    }
}

function showInternDetails(id, fullName, email, username, phone, registered) {
    const modal = document.getElementById('internDetailsModal');
    if (modal) {
        document.getElementById('internFullName').textContent = fullName;
        document.getElementById('internUsername').textContent = username;
        document.getElementById('internEmail').textContent = email;
        document.getElementById('internPhone').textContent = phone || 'N/A';
        document.getElementById('internRegistered').textContent = registered;
        new bootstrap.Modal(modal).show();
    }
}

// Enhanced Notification System
class NotificationManager {
    constructor() {
        this.updateInterval = null;
        this.lastUpdate = null;
        this.isUpdating = false;
        this.init();
    }

    init() {
        this.loadNotifications();
        this.setupPeriodicUpdates();
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        // Mark notification as read when clicked
        $(document).on('click', '.notification-item[data-notification-id]', (e) => {
            const notificationId = $(e.currentTarget).data('notification-id');
            if (notificationId) {
                this.markAsRead(notificationId);
            }
        });

        // Mark all as read
        $('#markAllRead').on('click', () => {
            this.markAllAsRead();
        });

        // Clear all notifications
        $('#clearAllNotifications').on('click', () => {
            this.clearAllNotifications();
        });
    }

    async loadNotifications() {
        if (this.isUpdating) return;
        this.isUpdating = true;

        try {
            const response = await fetch('/api/notifications');
            if (!response.ok) throw new Error('Failed to load notifications');

            const notifications = await response.json();
            this.updateNotificationDropdown(notifications);
            await this.updateUnreadCount();
        } catch (error) {
            console.error('Error loading notifications:', error);
        } finally {
            this.isUpdating = false;
        }
    }

    async updateUnreadCount() {
        try {
            const response = await fetch('/api/notifications/unread_count');
            if (!response.ok) throw new Error('Failed to get unread count');

            const data = await response.json();
            const count = data.count || 0;

            const badge = document.querySelector('.notification-badge');
            if (badge) {
                if (count > 0) {
                    badge.textContent = count > 99 ? '99+' : count;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Error updating unread count:', error);
        }
    }

    updateNotificationDropdown(notifications) {
        const container = document.getElementById('notificationList');
        if (!container) return;

        if (notifications.length === 0) {
            container.innerHTML = '<div class="dropdown-item text-center text-muted">No notifications</div>';
            return;
        }

        container.innerHTML = notifications.map(notification => `
            <div class="dropdown-item notification-item ${notification.is_read ? 'read' : 'unread'}" 
                 data-notification-id="${notification.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="dropdown-header">${this.escapeHtml(notification.title)}</h6>
                        <p class="mb-1 small">${this.escapeHtml(notification.message)}</p>
                        <small class="text-muted">${notification.created_at}</small>
                    </div>
                    ${!notification.is_read ? '<span class="badge bg-primary">New</span>' : ''}
                </div>
            </div>
        `).join('');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}/mark_read`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            if (response.ok) {
                await this.updateUnreadCount();
                // Update the notification item visually
                const item = document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (item) {
                    item.classList.remove('unread');
                    item.classList.add('read');
                    const badge = item.querySelector('.badge');
                    if (badge) badge.remove();
                }
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }

    async markAllAsRead() {
        try {
            const response = await fetch('/api/notifications/mark_all_read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            if (response.ok) {
                await this.loadNotifications();
            }
        } catch (error) {
            console.error('Error marking all notifications as read:', error);
        }
    }

    async clearAllNotifications() {
        try {
            const response = await fetch('/api/notifications/clear_all', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            if (response.ok) {
                await this.loadNotifications();
            }
        } catch (error) {
            console.error('Error clearing all notifications:', error);
        }
    }

    setupPeriodicUpdates() {
        // Update every 30 seconds
        this.updateInterval = setInterval(() => {
            this.updateUnreadCount();
        }, 10000);

        // Check for new notifications every 60 seconds
        setInterval(() => {
            this.loadNotifications();
        }, 20000);
    }

    getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}