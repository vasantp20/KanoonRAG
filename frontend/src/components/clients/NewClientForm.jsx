import React, { useState } from 'react';
import { clientService } from '../../api/clientService';

const NewClientForm = () => {
  const [formData, setFormData] = useState({
    name: '',
    place_of_stay: '',
    age: '',
    gender: '',
    contact_info: '',
    initial_notes: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [message, setMessage] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setSuccess(false);
    setMessage(null);

    try {
      const payload = {
        ...formData,
        age: formData.age ? parseInt(formData.age, 10) : null
      };
      await clientService.createClient(payload);
      setSuccess(true);
      setMessage({ type: 'success', text: 'Client registered successfully.' });
      setFormData({
        name: '',
        place_of_stay: '',
        age: '',
        gender: '',
        contact_info: '',
        initial_notes: ''
      });
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccess(false);
        setMessage(null);
      }, 3000);
    } catch (error) {
      console.error('Error creating client:', error);
      setMessage({ type: 'error', text: 'Failed to register client: ' + error.message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bento-grid">
      <div className="bento-main">
        <div className="form-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '8px', background: 'rgba(196, 162, 101, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-primary)' }}>
              <span className="material-symbols-outlined">person_add</span>
            </div>
            <div>
              <h3 style={{ fontSize: '20px', fontWeight: '600' }}>Entity Intake Form</h3>
              <p className="form-label" style={{ marginBottom: 0 }}>Confidential Record</p>
            </div>
          </div>
          
          {message && (
            <div style={{ 
              padding: '12px 16px', 
              borderRadius: '8px', 
              marginBottom: '24px',
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

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label className="form-label">FULL NAME</label>
                <input required name="name" value={formData.name} onChange={handleChange} className="form-input" placeholder="e.g. Rajesh Kumar" type="text" />
              </div>
              <div>
                <label className="form-label">PLACE OF STAY (CITY/STATE)</label>
                <input name="place_of_stay" value={formData.place_of_stay} onChange={handleChange} className="form-input" placeholder="e.g. New Delhi, DL" type="text" />
              </div>
              <div>
                <label className="form-label">AGE</label>
                <input name="age" value={formData.age} onChange={handleChange} className="form-input" placeholder="Enter age" type="number" min="0" max="150" />
              </div>
              <div>
                <label className="form-label">GENDER</label>
                <select name="gender" value={formData.gender} onChange={handleChange} className="form-select">
                  <option disabled value="">Select Gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Non-Binary / Other</option>
                  <option value="prefer_not_to_say">Prefer not to say</option>
                </select>
              </div>
              <div style={{ gridColumn: 'span 2' }}>
                <label className="form-label">CONTACT INFO (EMAIL / PHONE)</label>
                <input name="contact_info" value={formData.contact_info} onChange={handleChange} className="form-input" placeholder="e.g. contact@domain.com or +91 98765 43210" type="text" />
              </div>
            </div>

            <div>
              <label className="form-label">INITIAL NOTES (OPTIONAL)</label>
              <textarea name="initial_notes" value={formData.initial_notes} onChange={handleChange} className="form-textarea" placeholder="Describe the preliminary context of the legal inquiry..." rows="4"></textarea>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '16px', borderTop: '1px solid var(--color-outline-variant)' }}>
              <p style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', color: 'var(--color-on-surface-variant)' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>info</span>
                Data is encrypted and compliant with legal privilege standards.
              </p>
              
              <button 
                type="submit" 
                disabled={isLoading}
                style={{
                  padding: '12px 32px',
                  backgroundColor: success ? '#16a34a' : 'var(--color-primary)',
                  color: success ? '#ffffff' : 'var(--color-on-primary)',
                  fontWeight: '700',
                  borderRadius: '8px',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'all 0.2s',
                  boxShadow: '0 0 20px rgba(230,193,129,0.15)'
                }}
              >
                {isLoading ? (
                  <><span className="material-symbols-outlined" style={{ animation: 'spin 1s linear infinite' }}>sync</span> Registering...</>
                ) : success ? (
                  <><span className="material-symbols-outlined">check_circle</span> Registered</>
                ) : (
                  <><span className="material-symbols-outlined">how_to_reg</span> REGISTER CLIENT</>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
      
      <div className="bento-side" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="form-panel" style={{ borderLeft: '4px solid var(--color-primary)' }}>
          <h4 style={{ color: 'var(--color-primary)', fontWeight: '600', marginBottom: '12px' }}>Guidelines</h4>
          <ul style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '14px', color: 'var(--color-on-surface-variant)' }}>
            <li style={{ display: 'flex', gap: '12px' }}>
              <span className="material-symbols-outlined" style={{ color: 'var(--color-primary)', fontSize: '20px' }}>check_circle</span>
              Ensure ID proof matches the entered full name.
            </li>
            <li style={{ display: 'flex', gap: '12px' }}>
              <span className="material-symbols-outlined" style={{ color: 'var(--color-primary)', fontSize: '20px' }}>check_circle</span>
              Contact info is mandatory for automated notifications.
            </li>
            <li style={{ display: 'flex', gap: '12px' }}>
              <span className="material-symbols-outlined" style={{ color: 'var(--color-primary)', fontSize: '20px' }}>check_circle</span>
              Verify the current place of stay for jurisdictional checks.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default NewClientForm;
