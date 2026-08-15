import React, { useState, useEffect } from 'react';
import { clientService } from '../../api/clientService';
import { caseService } from '../../api/caseService';

const NewCaseForm = ({ onGoToNewClient }) => {
  const [clients, setClients] = useState([]);
  const [formData, setFormData] = useState({
    client_id: '',
    case_type: 'child_custody',
    description: '',
    opposing_party_name: '',
    opposing_legal_rep: '',
    opposing_party_address: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    // Fetch clients on mount to populate dropdown
    clientService.getAllClients()
      .then(data => setClients(data))
      .catch(err => console.error('Failed to load clients', err));
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === 'client_id' && value === 'NEW') {
      onGoToNewClient();
      return;
    }
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.client_id) {
      setMessage({ type: 'error', text: 'Please select a client.' });
      return;
    }

    setIsLoading(true);
    setSuccess(false);
    setMessage(null);

    try {
      const payload = { ...formData, client_id: parseInt(formData.client_id, 10) };
      await caseService.createCase(payload);
      setSuccess(true);
      setMessage({ type: 'success', text: 'Case successfully registered.' });
      setFormData({
        client_id: '',
        case_type: 'child_custody',
        description: '',
        opposing_party_name: '',
        opposing_legal_rep: '',
        opposing_party_address: ''
      });
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccess(false);
        setMessage(null);
      }, 3000);
    } catch (error) {
      console.error('Error creating case:', error);
      setMessage({ type: 'error', text: 'Failed to create case: ' + error.message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bento-grid">
      {/* Left Column: Primary Case Info */}
      <div className="bento-main" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        
        {message && (
          <div style={{ 
            padding: '12px 16px', 
            borderRadius: '8px', 
            backgroundColor: message.type === 'success' ? 'rgba(22, 163, 74, 0.1)' : 'rgba(220, 38, 38, 0.1)',
            border: `1px solid ${message.type === 'success' ? 'rgba(22, 163, 74, 0.3)' : 'rgba(220, 38, 38, 0.3)'}`,
            color: message.type === 'success' ? '#4ade80' : '#f87171',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>
              {message.type === 'success' ? 'check_circle' : 'error'}
            </span>
            {message.text}
          </div>
        )}

        <div className="form-panel">
          <label className="form-label text-primary" style={{ color: 'var(--color-primary)' }}>Select Client</label>
          <div style={{ position: 'relative' }}>
            <select name="client_id" value={formData.client_id} onChange={handleChange} className="form-select" required>
              <option value="" disabled>Select a client...</option>
              {clients.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
              <option value="NEW">+ Register New Client</option>
            </select>
          </div>
        </div>

        <div className="form-panel">
          <label className="form-label text-primary" style={{ color: 'var(--color-primary)' }}>Case Type</label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px' }}>
            {['divorce_cruelty', 'maintenance', 'child_custody', 'domestic_violence', 'dowry_498a', 'other'].map(type => (
              <label key={type} style={{ 
                display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', 
                background: 'var(--color-surface-container)', border: '1px solid var(--color-outline-variant)', 
                borderRadius: '8px', cursor: 'pointer' 
              }}>
                <input 
                  type="radio" 
                  name="case_type" 
                  value={type} 
                  checked={formData.case_type === type} 
                  onChange={handleChange}
                  style={{ accentColor: 'var(--color-primary)' }}
                />
                <span style={{ fontSize: '14px', textTransform: 'capitalize' }}>{type.replace('_', ' ')}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="form-panel">
          <label className="form-label text-primary" style={{ color: 'var(--color-primary)' }}>Case Description & Brief</label>
          <textarea 
            name="description" 
            value={formData.description} 
            onChange={handleChange} 
            className="form-textarea" 
            placeholder="Outline the primary legal grounds, key events, and desired outcomes..." 
            rows="6"
          ></textarea>
        </div>
      </div>

      {/* Right Column: Opposing Party & Actions */}
      <div className="bento-side" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        
        <div className="form-panel" style={{ borderLeft: '4px solid rgba(255, 180, 171, 0.3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
            <span className="material-symbols-outlined" style={{ color: 'var(--color-error)' }}>gavel</span>
            <label className="form-label" style={{ color: 'var(--color-error)', margin: 0 }}>Opposing Party Details</label>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label className="form-label" style={{ textTransform: 'none', color: 'var(--color-on-surface-variant)' }}>Full Legal Name</label>
              <input name="opposing_party_name" value={formData.opposing_party_name} onChange={handleChange} className="form-input" placeholder="e.g., Rajesh Khanna" type="text" />
            </div>
            <div>
              <label className="form-label" style={{ textTransform: 'none', color: 'var(--color-on-surface-variant)' }}>Legal Representative (If known)</label>
              <input name="opposing_legal_rep" value={formData.opposing_legal_rep} onChange={handleChange} className="form-input" placeholder="Name of opposing counsel or firm" type="text" />
            </div>
            <div>
              <label className="form-label" style={{ textTransform: 'none', color: 'var(--color-on-surface-variant)' }}>Permanent/Current Address</label>
              <textarea name="opposing_party_address" value={formData.opposing_party_address} onChange={handleChange} className="form-textarea" placeholder="Enter complete correspondence address..." rows="3"></textarea>
            </div>
          </div>
        </div>

        <div style={{ paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <button 
            type="submit" 
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '16px',
              backgroundColor: success ? '#16a34a' : 'var(--color-primary)',
              color: success ? '#ffffff' : 'var(--color-on-primary)',
              fontWeight: '700',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              transition: 'all 0.2s',
              boxShadow: '0 0 20px rgba(230,193,129,0.15)'
            }}
          >
            {isLoading ? (
              <><span className="material-symbols-outlined" style={{ animation: 'spin 1s linear infinite' }}>sync</span> Initializing...</>
            ) : success ? (
              <><span className="material-symbols-outlined">check_circle</span> Case Registered</>
            ) : (
              <><span className="material-symbols-outlined">save</span> Register & Begin Research</>
            )}
          </button>
        </div>
      </div>
    </form>
  );
};

export default NewCaseForm;
