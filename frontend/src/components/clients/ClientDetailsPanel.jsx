import React, { useState, useEffect } from 'react';
import { clientService } from '../../api/clientService';
import './ClientDetailsPanel.css';

const ClientDetailsPanel = ({ clientId, onClose, onClientUpdated }) => {
  const [client, setClient] = useState(null);
  const [cases, setCases] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({});
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!clientId) return;
    
    setIsLoading(true);
    setError(null);
    
    // Fetch client details and their cases
    Promise.all([
      clientService.getClient(clientId),
      clientService.getClientCases(clientId).catch(() => []) // Default to empty array if endpoint fails
    ])
    .then(([clientData, casesData]) => {
      setClient(clientData);
      setFormData({
        name: clientData.name || '',
        place_of_stay: clientData.place_of_stay || '',
        age: clientData.age || '',
        gender: clientData.gender || '',
        contact_info: clientData.contact_info || '',
        initial_notes: clientData.initial_notes || ''
      });
      setCases(casesData || []);
      setIsLoading(false);
    })
    .catch(err => {
      console.error("Failed to load client details:", err);
      setError("Failed to load client information.");
      setIsLoading(false);
    });
  }, [clientId]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const payload = {
        ...formData,
        age: formData.age ? parseInt(formData.age, 10) : null
      };
      const updatedClient = await clientService.updateClient(clientId, payload);
      setClient(updatedClient);
      setIsEditing(false);
      if (onClientUpdated) {
        onClientUpdated();
      }
    } catch (err) {
      console.error("Failed to update client:", err);
      alert("Failed to update client. " + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  if (!clientId) return null;

  return (
    <>
      <div className="panel-overlay" onClick={onClose}></div>
      <div className="client-details-panel">
        <div className="panel-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div className="panel-avatar">
              {client ? client.name.substring(0, 2).toUpperCase() : '..'}
            </div>
            <div>
              <h2 className="panel-title">{client ? client.name : 'Loading...'}</h2>
              <p className="panel-subtitle">ID: #{clientId}</p>
            </div>
          </div>
          <button className="panel-close-btn" onClick={onClose}>
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <div className="panel-content custom-scrollbar">
          {isLoading ? (
            <div className="panel-loading">
              <span className="material-symbols-outlined spin">sync</span>
              <p>Loading profile...</p>
            </div>
          ) : error ? (
            <div className="panel-error">{error}</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              
              {/* Profile Details Section */}
              <div className="panel-section">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 className="section-title">Profile Information</h3>
                  {!isEditing ? (
                    <button className="panel-action-btn" onClick={() => setIsEditing(true)}>
                      <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>edit</span> Edit
                    </button>
                  ) : (
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button className="panel-action-btn cancel" onClick={() => setIsEditing(false)} disabled={isSaving}>Cancel</button>
                      <button className="panel-action-btn save" onClick={handleSave} disabled={isSaving}>
                        {isSaving ? 'Saving...' : 'Save'}
                      </button>
                    </div>
                  )}
                </div>

                <div className="profile-grid">
                  <div className="profile-field">
                    <label>Full Name</label>
                    {isEditing ? (
                      <input name="name" value={formData.name} onChange={handleChange} className="panel-input" />
                    ) : (
                      <p>{client.name}</p>
                    )}
                  </div>
                  
                  <div className="profile-field">
                    <label>Contact Info</label>
                    {isEditing ? (
                      <input name="contact_info" value={formData.contact_info} onChange={handleChange} className="panel-input" />
                    ) : (
                      <p>{client.contact_info || '-'}</p>
                    )}
                  </div>

                  <div className="profile-field">
                    <label>Place of Stay</label>
                    {isEditing ? (
                      <input name="place_of_stay" value={formData.place_of_stay} onChange={handleChange} className="panel-input" />
                    ) : (
                      <p>{client.place_of_stay || '-'}</p>
                    )}
                  </div>

                  <div className="profile-field" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <div>
                      <label>Age</label>
                      {isEditing ? (
                        <input name="age" type="number" value={formData.age} onChange={handleChange} className="panel-input" />
                      ) : (
                        <p>{client.age || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label>Gender</label>
                      {isEditing ? (
                        <select name="gender" value={formData.gender} onChange={handleChange} className="panel-input">
                          <option value="">Select</option>
                          <option value="male">Male</option>
                          <option value="female">Female</option>
                          <option value="other">Other</option>
                        </select>
                      ) : (
                        <p style={{ textTransform: 'capitalize' }}>{client.gender || '-'}</p>
                      )}
                    </div>
                  </div>

                  <div className="profile-field">
                    <label>Initial Notes</label>
                    {isEditing ? (
                      <textarea name="initial_notes" value={formData.initial_notes} onChange={handleChange} className="panel-textarea" rows="3"></textarea>
                    ) : (
                      <p className="notes-text">{client.initial_notes || 'No initial notes provided.'}</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Associated Cases Section */}
              <div className="panel-section">
                <h3 className="section-title" style={{ marginBottom: '16px' }}>Associated Cases</h3>
                
                {cases.length === 0 ? (
                  <div className="empty-cases">
                    <span className="material-symbols-outlined">folder_open</span>
                    <p>No active cases for this client.</p>
                  </div>
                ) : (
                  <div className="cases-list">
                    {cases.map(caseItem => (
                      <div key={caseItem.id} className="case-card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                          <span className="case-type">{caseItem.case_type.replace('_', ' ')}</span>
                          <span className={`case-status ${caseItem.status || 'active'}`}>{caseItem.status || 'Active'}</span>
                        </div>
                        <p className="case-desc">{caseItem.description || 'No description provided.'}</p>
                        {caseItem.court_name && <p className="case-court">{caseItem.court_name}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default ClientDetailsPanel;
