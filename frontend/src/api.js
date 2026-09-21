/**
 * Multi-Branch Restaurant AI Agent API Client
 * Zero external client dependencies (native fetch).
 * Handles customer and staff authentication tokens, error handling, and API endpoints.
 */

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

// Token Management
export const getCustomerToken = () => localStorage.getItem('customer_token');
export const setCustomerToken = (token) => localStorage.setItem('customer_token', token);
export const removeCustomerToken = () => {
  localStorage.removeItem('customer_token');
  localStorage.removeItem('customer_user');
};

export const getStaffToken = () => localStorage.getItem('staff_token');
export const setStaffToken = (token) => localStorage.setItem('staff_token', token);
export const removeStaffToken = () => {
  localStorage.removeItem('staff_token');
  localStorage.removeItem('staff_user');
};

export const getStoredCustomer = () => {
  try {
    const raw = localStorage.getItem('customer_user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};
export const setStoredCustomer = (user) => localStorage.setItem('customer_user', JSON.stringify(user));

export const getStoredStaff = () => {
  try {
    const raw = localStorage.getItem('staff_user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};
export const setStoredStaff = (user) => localStorage.setItem('staff_user', JSON.stringify(user));

/**
 * Generic Fetch Helper
 */
async function request(endpoint, options = {}, authType = null) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (authType === 'customer') {
    const token = getCustomerToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  } else if (authType === 'staff') {
    const token = getStaffToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  let data = null;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const errMsg = (data && data.detail) || response.statusText || 'An error occurred';
    const error = new Error(errMsg);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

// Public / Customer API
export const api = {
  // Customer Auth
  customerLogin: async (email, password) => {
    const res = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setCustomerToken(res.access_token);
    setStoredCustomer(res.user);
    return res;
  },

  customerRegister: async (payload) => {
    const res = await request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    setCustomerToken(res.access_token);
    setStoredCustomer(res.user);
    return res;
  },

  customerMe: async () => {
    const user = await request('/auth/me', { method: 'GET' }, 'customer');
    setStoredCustomer(user);
    return user;
  },

  // Branches & Menu Explorer
  getBranches: () => request('/branches', { method: 'GET' }),
  getBranchMenu: (branchId) => request(`/branches/${branchId}/menu`, { method: 'GET' }),
  getBranchFaq: (branchId) => request(`/branches/${branchId}/faq`, { method: 'GET' }),

  // Chat Agent
  sendMessage: (message, branchId = null) =>
    request(
      '/chat',
      {
        method: 'POST',
        body: JSON.stringify({ message, branch_id: branchId }),
      },
      'customer'
    ),

  // Customer Orders & Reservations
  getMyOrders: () => request('/orders/me', { method: 'GET' }, 'customer'),
  getMyReservations: () => request('/reservations/me', { method: 'GET' }, 'customer'),

  // Staff Auth
  staffLogin: async (username, password) => {
    const res = await request('/staff/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    setStaffToken(res.access_token);
    setStoredStaff(res.user);
    return res;
  },

  staffMe: async () => {
    const user = await request('/staff/me', { method: 'GET' }, 'staff');
    setStoredStaff(user);
    return user;
  },

  // Staff Orders
  getStaffOrders: (branchId = null, status = null) => {
    const params = new URLSearchParams();
    if (branchId) params.append('branch_id', branchId);
    if (status) params.append('status', status);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request(`/staff/orders${qs}`, { method: 'GET' }, 'staff');
  },

  updateOrderStatus: (orderId, status) =>
    request(
      `/staff/orders/${orderId}/status`,
      {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      },
      'staff'
    ),

  // Staff Reservations
  getStaffReservations: (branchId = null, status = null, date = null) => {
    const params = new URLSearchParams();
    if (branchId) params.append('branch_id', branchId);
    if (status) params.append('status', status);
    if (date) params.append('date', date);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request(`/staff/reservations${qs}`, { method: 'GET' }, 'staff');
  },

  updateReservation: (resId, payload) =>
    request(
      `/staff/reservations/${resId}`,
      {
        method: 'PATCH',
        body: JSON.stringify(payload),
      },
      'staff'
    ),

  // Staff Menu & Stock
  getStaffCategories: (branchId = null) => {
    const qs = branchId ? `?branch_id=${branchId}` : '';
    return request(`/staff/menu/categories${qs}`, { method: 'GET' }, 'staff');
  },

  createCategory: (payload) =>
    request(
      '/staff/menu/categories',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      'staff'
    ),

  createMenuItem: (payload) =>
    request(
      '/staff/menu/items',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      'staff'
    ),

  updateMenuItem: (itemId, payload) =>
    request(
      `/staff/menu/items/${itemId}`,
      {
        method: 'PATCH',
        body: JSON.stringify(payload),
      },
      'staff'
    ),

  updateItemStock: (menuItemId, branchId, stockQuantity) =>
    request(
      '/staff/menu/stock',
      {
        method: 'PUT',
        body: JSON.stringify({
          menu_item_id: menuItemId,
          branch_id: branchId,
          stock_quantity: stockQuantity,
        }),
      },
      'staff'
    ),

  // Staff Branches & Tables
  getStaffBranches: () => request('/staff/branches', { method: 'GET' }, 'staff'),

  createBranch: (payload) =>
    request(
      '/staff/branches',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      'staff'
    ),

  updateBranch: (branchId, payload) =>
    request(
      `/staff/branches/${branchId}`,
      {
        method: 'PATCH',
        body: JSON.stringify(payload),
      },
      'staff'
    ),

  getStaffTables: (branchId = null) => {
    const qs = branchId ? `?branch_id=${branchId}` : '';
    return request(`/staff/branches/tables${qs}`, { method: 'GET' }, 'staff');
  },

  createTable: (payload) =>
    request(
      '/staff/branches/tables',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      'staff'
    ),

  updateTable: (tableId, payload) =>
    request(
      `/staff/branches/tables/${tableId}`,
      {
        method: 'PATCH',
        body: JSON.stringify(payload),
      },
      'staff'
    ),
};
