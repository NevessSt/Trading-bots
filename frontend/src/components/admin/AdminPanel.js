import React, { useState, useEffect } from 'react';
import { 
  FaUsers, FaKey, FaCrown, FaClock, FaChartBar, FaSearch, 
  FaFilter, FaDownload, FaPlus, FaEdit, FaTrash, FaEye,
  FaUserClock, FaUserCheck, FaUserTimes, FaExclamationTriangle
} from 'react-icons/fa';
import { toast } from 'react-toastify';
import { useAuth } from '../../contexts/AuthContext';
import { adminAPI } from '../../services/api';

const AdminPanel = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [licenses, setLicenses] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [showUserModal, setShowUserModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);

  // Load data on component mount and tab change
  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case 'users':
          await loadUsers();
          break;
        case 'licenses':
          await loadLicenses();
          break;
        case 'stats':
          await loadStats();
          break;
        default:
          break;
      }
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await adminAPI.get('/users');
      setUsers(response.data.users || []);
    } catch (error) {
      console.error('Failed to load users:', error);
      toast.error('Failed to load users');
    }
  };

  const loadLicenses = async () => {
    try {
      const response = await adminAPI.get('/licenses');
      setLicenses(response.data.licenses || []);
    } catch (error) {
      console.error('Failed to load licenses:', error);
      toast.error('Failed to load licenses');
    }
  };

  const loadStats = async () => {
    try {
      const response = await adminAPI.get('/stats');
      setStats(response.data || {});
    } catch (error) {
      console.error('Failed to load stats:', error);
      toast.error('Failed to load statistics');
    }
  };

  const handleUserAction = async (action, userId, data = {}) => {
    try {
      let response;
      switch (action) {
        case 'activate':
          response = await adminAPI.post(`/users/${userId}/activate`);
          break;
        case 'deactivate':
          response = await adminAPI.post(`/users/${userId}/deactivate`);
          break;
        case 'upgrade':
          response = await adminAPI.post(`/users/${userId}/upgrade`, data);
          break;
        case 'extend':
          response = await adminAPI.post(`/users/${userId}/extend`, data);
          break;
        case 'delete':
          if (window.confirm('Are you sure you want to delete this user?')) {
            response = await adminAPI.delete(`/users/${userId}`);
          } else {
            return;
          }
          break;
        default:
          return;
      }
      
      toast.success(response.data.message || 'Action completed successfully');
      await loadUsers();
    } catch (error) {
      console.error(`Failed to ${action} user:`, error);
      toast.error(`Failed to ${action} user`);
    }
  };

  const handleLicenseAction = async (action, licenseId, data = {}) => {
    try {
      let response;
      switch (action) {
        case 'activate':
          response = await adminAPI.post(`/licenses/${licenseId}/activate`);
          break;
        case 'deactivate':
          response = await adminAPI.post(`/licenses/${licenseId}/deactivate`);
          break;
        case 'extend':
          response = await adminAPI.post(`/licenses/${licenseId}/extend`, data);
          break;
        case 'delete':
          if (window.confirm('Are you sure you want to delete this license?')) {
            response = await adminAPI.delete(`/licenses/${licenseId}`);
          } else {
            return;
          }
          break;
        default:
          return;
      }
      
      toast.success(response.data.message || 'Action completed successfully');
      await loadLicenses();
    } catch (error) {
      console.error(`Failed to ${action} license:`, error);
      toast.error(`Failed to ${action} license`);
    }
  };

  const exportData = async (type) => {
    try {
      const response = await adminAPI.get(`/export/${type}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${type}_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success(`${type} data exported successfully`);
    } catch (error) {
      console.error(`Failed to export ${type}:`, error);
      toast.error(`Failed to export ${type} data`);
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filterStatus === 'all' || 
                         (filterStatus === 'active' && user.is_active) ||
                         (filterStatus === 'inactive' && !user.is_active) ||
                         (filterStatus === 'demo' && user.is_demo) ||
                         (filterStatus === 'premium' && !user.is_demo && user.is_active);
    
    return matchesSearch && matchesFilter;
  });

  const filteredLicenses = licenses.filter(license => {
    const matchesSearch = license.user_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         license.license_type?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filterStatus === 'all' || 
                         (filterStatus === 'active' && license.is_active) ||
                         (filterStatus === 'inactive' && !license.is_active) ||
                         (filterStatus === 'expired' && new Date(license.expires_at) < new Date());
    
    return matchesSearch && matchesFilter;
  });

  const renderTabButton = (tabId, label, icon) => (
    <button
      key={tabId}
      onClick={() => setActiveTab(tabId)}
      className={`flex items-center px-4 py-2 rounded-lg font-medium transition-colors ${
        activeTab === tabId
          ? 'bg-blue-600 text-white'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
    >
      {icon}
      <span className="ml-2">{label}</span>
    </button>
  );

  const renderUserRow = (user) => (
    <tr key={user.id} className="border-b border-gray-200 hover:bg-gray-50">
      <td className="px-4 py-3">
        <input
          type="checkbox"
          checked={selectedUsers.includes(user.id)}
          onChange={(e) => {
            if (e.target.checked) {
              setSelectedUsers([...selectedUsers, user.id]);
            } else {
              setSelectedUsers(selectedUsers.filter(id => id !== user.id));
            }
          }}
          className="rounded border-gray-300"
        />
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center">
          <div className={`w-3 h-3 rounded-full mr-3 ${
            user.is_active ? 'bg-green-500' : 'bg-red-500'
          }`}></div>
          <div>
            <div className="font-medium text-gray-900">{user.email}</div>
            <div className="text-sm text-gray-500">{user.name || 'No name'}</div>
          </div>
        </div>
      </td>
      <td className="px-4 py-3">
        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
          user.is_demo 
            ? 'bg-yellow-100 text-yellow-800'
            : user.is_active 
            ? 'bg-green-100 text-green-800'
            : 'bg-red-100 text-red-800'
        }`}>
          {user.is_demo ? 'Demo' : user.is_active ? 'Active' : 'Inactive'}
        </span>
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {user.license_type || 'No License'}
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
      </td>
      <td className="px-4 py-3">
        <div className="flex space-x-2">
          <button
            onClick={() => setEditingUser(user)}
            className="text-blue-600 hover:text-blue-800"
            title="Edit User"
          >
            <FaEdit />
          </button>
          <button
            onClick={() => handleUserAction(user.is_active ? 'deactivate' : 'activate', user.id)}
            className={`${user.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'}`}
            title={user.is_active ? 'Deactivate' : 'Activate'}
          >
            {user.is_active ? <FaUserTimes /> : <FaUserCheck />}
          </button>
          <button
            onClick={() => handleUserAction('delete', user.id)}
            className="text-red-600 hover:text-red-800"
            title="Delete User"
          >
            <FaTrash />
          </button>
        </div>
      </td>
    </tr>
  );

  const renderLicenseRow = (license) => (
    <tr key={license.id} className="border-b border-gray-200 hover:bg-gray-50">
      <td className="px-4 py-3">
        <div className="font-medium text-gray-900">{license.user_email}</div>
      </td>
      <td className="px-4 py-3">
        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
          license.license_type === 'enterprise' 
            ? 'bg-purple-100 text-purple-800'
            : license.license_type === 'professional'
            ? 'bg-blue-100 text-blue-800'
            : 'bg-gray-100 text-gray-800'
        }`}>
          {license.license_type}
        </span>
      </td>
      <td className="px-4 py-3">
        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
          license.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {license.is_active ? 'Active' : 'Inactive'}
        </span>
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {license.created_at ? new Date(license.created_at).toLocaleDateString() : 'N/A'}
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {license.expires_at ? new Date(license.expires_at).toLocaleDateString() : 'Never'}
      </td>
      <td className="px-4 py-3">
        <div className="flex space-x-2">
          <button
            onClick={() => handleLicenseAction(license.is_active ? 'deactivate' : 'activate', license.id)}
            className={`${license.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'}`}
            title={license.is_active ? 'Deactivate' : 'Activate'}
          >
            {license.is_active ? <FaUserTimes /> : <FaUserCheck />}
          </button>
          <button
            onClick={() => handleLicenseAction('extend', license.id, { days: 30 })}
            className="text-blue-600 hover:text-blue-800"
            title="Extend License"
          >
            <FaClock />
          </button>
          <button
            onClick={() => handleLicenseAction('delete', license.id)}
            className="text-red-600 hover:text-red-800"
            title="Delete License"
          >
            <FaTrash />
          </button>
        </div>
      </td>
    </tr>
  );

  const renderStatsCard = (title, value, icon, color = 'blue') => (
    <div className={`bg-white rounded-lg shadow p-6 border-l-4 border-${color}-500`}>
      <div className="flex items-center">
        <div className={`text-${color}-500 text-2xl mr-4`}>
          {icon}
        </div>
        <div>
          <div className="text-2xl font-bold text-gray-900">{value}</div>
          <div className="text-sm text-gray-500">{title}</div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Panel</h1>
          <p className="text-gray-600">Manage users, licenses, and system settings</p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-4 mb-6">
          {renderTabButton('users', 'Users', <FaUsers />)}
          {renderTabButton('licenses', 'Licenses', <FaKey />)}
          {renderTabButton('stats', 'Statistics', <FaChartBar />)}
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg shadow">
          {activeTab === 'users' && (
            <div className="p-6">
              {/* Users Header */}
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900">User Management</h2>
                <div className="flex space-x-3">
                  <button
                    onClick={() => exportData('users')}
                    className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    <FaDownload className="mr-2" />
                    Export
                  </button>
                  <button
                    onClick={() => setShowUserModal(true)}
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    <FaPlus className="mr-2" />
                    Add User
                  </button>
                </div>
              </div>

              {/* Search and Filter */}
              <div className="flex space-x-4 mb-6">
                <div className="flex-1 relative">
                  <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search users..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">All Users</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="demo">Demo</option>
                  <option value="premium">Premium</option>
                </select>
              </div>

              {/* Users Table */}
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <input
                          type="checkbox"
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedUsers(filteredUsers.map(u => u.id));
                            } else {
                              setSelectedUsers([]);
                            }
                          }}
                          className="rounded border-gray-300"
                        />
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">License</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Login</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {loading ? (
                      <tr>
                        <td colSpan="7" className="px-4 py-8 text-center text-gray-500">
                          Loading users...
                        </td>
                      </tr>
                    ) : filteredUsers.length === 0 ? (
                      <tr>
                        <td colSpan="7" className="px-4 py-8 text-center text-gray-500">
                          No users found
                        </td>
                      </tr>
                    ) : (
                      filteredUsers.map(renderUserRow)
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'licenses' && (
            <div className="p-6">
              {/* Licenses Header */}
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900">License Management</h2>
                <button
                  onClick={() => exportData('licenses')}
                  className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  <FaDownload className="mr-2" />
                  Export
                </button>
              </div>

              {/* Search and Filter */}
              <div className="flex space-x-4 mb-6">
                <div className="flex-1 relative">
                  <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search licenses..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">All Licenses</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="expired">Expired</option>
                </select>
              </div>

              {/* Licenses Table */}
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Expires</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {loading ? (
                      <tr>
                        <td colSpan="6" className="px-4 py-8 text-center text-gray-500">
                          Loading licenses...
                        </td>
                      </tr>
                    ) : filteredLicenses.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="px-4 py-8 text-center text-gray-500">
                          No licenses found
                        </td>
                      </tr>
                    ) : (
                      filteredLicenses.map(renderLicenseRow)
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'stats' && (
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">System Statistics</h2>
              
              {loading ? (
                <div className="text-center py-8">
                  <div className="text-gray-500">Loading statistics...</div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {renderStatsCard('Total Users', stats.total_users || 0, <FaUsers />, 'blue')}
                  {renderStatsCard('Active Users', stats.active_users || 0, <FaUserCheck />, 'green')}
                  {renderStatsCard('Demo Users', stats.demo_users || 0, <FaUserClock />, 'yellow')}
                  {renderStatsCard('Premium Users', stats.premium_users || 0, <FaCrown />, 'purple')}
                  {renderStatsCard('Total Licenses', stats.total_licenses || 0, <FaKey />, 'indigo')}
                  {renderStatsCard('Active Licenses', stats.active_licenses || 0, <FaKey />, 'green')}
                  {renderStatsCard('Expired Licenses', stats.expired_licenses || 0, <FaExclamationTriangle />, 'red')}
                  {renderStatsCard('Revenue (Monthly)', `$${stats.monthly_revenue || 0}`, <FaChartBar />, 'green')}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;