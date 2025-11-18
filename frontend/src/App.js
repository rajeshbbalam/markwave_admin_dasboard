import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('referrals');
  const [referrals, setReferrals] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [mobile, setMobile] = useState('');

  useEffect(() => {
    fetchReferrals();
    fetchCustomers();
  }, []);

  const fetchReferrals = async () => {
    const response = await fetch('http://localhost:8001/Users/referrals');
    const data = await response.json();
    setReferrals(data);
  };

  const fetchCustomers = async () => {
    const response = await fetch('http://localhost:8001/Users/customers');
    const data = await response.json();
    setCustomers(data);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const response = await fetch('http://localhost:8001/Users/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, mobile, referral_type: 'new_referral' })
    });
    if (response.ok) {
      alert('Referral added successfully');
      setName('');
      setMobile('');
      setShowForm(false);
      fetchReferrals(); // Refresh referrals
    } else {
      alert('Error adding referral');
    }
  };

  return (
    <div className="App">
      <h1>Markwave Users Dashboard</h1>
      <button className="add-button" onClick={() => setShowForm(!showForm)}>
        {showForm ? 'Cancel' : 'Add New Referral'}
      </button>
      {showForm && (
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name:</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Mobile:</label>
            <input type="text" value={mobile} onChange={(e) => setMobile(e.target.value)} required />
          </div>
          <button type="submit" className="submit-button">Add Referral</button>
          <button type="button" className="cancel-button" onClick={() => setShowForm(false)}>Cancel</button>
        </form>
      )}
      <div className="tabs">
        <button onClick={() => setActiveTab('referrals')} className={activeTab === 'referrals' ? 'active' : ''}>
          New Referrals
        </button>
        <button onClick={() => setActiveTab('customers')} className={activeTab === 'customers' ? 'active' : ''}>
          Existing Customers
        </button>
      </div>
      <div className="tab-content">
        {activeTab === 'referrals' && (
          <div>
            <h2>New Referrals</h2>
            <table className="user-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Mobile</th>
                  <th>Verified</th>
                </tr>
              </thead>
              <tbody>
                {referrals.map((user, index) => (
                  <tr key={index}>
                    <td>{user.name}</td>
                    <td>{user.mobile}</td>
                    <td>{user.verified ? 'Yes' : 'No'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {activeTab === 'customers' && (
          <div>
            <h2>Existing Customers</h2>
            <table className="user-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Mobile</th>
                  <th>Verified</th>
                </tr>
              </thead>
              <tbody>
                {customers.map((user, index) => (
                  <tr key={index}>
                    <td>{user.name}</td>
                    <td>{user.mobile}</td>
                    <td>{user.verified ? 'Yes' : 'No'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
