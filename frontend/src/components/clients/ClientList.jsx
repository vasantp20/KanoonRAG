import React, { useEffect, useState } from 'react';
import { clientService } from '../../api/clientService';
import ClientDetailsPanel from './ClientDetailsPanel';

const ClientList = () => {
  const [clients, setClients] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedClientId, setSelectedClientId] = useState(null);

  const fetchClients = () => {
    setIsLoading(true);
    clientService.getAllClients()
      .then(data => {
        setClients(data);
        setIsLoading(false);
      })
      .catch(err => {
        console.error('Failed to load clients', err);
        setIsLoading(false);
      });
  };

  useEffect(() => {
    fetchClients();
  }, []);

  return (
    <>
      <div className="form-panel">
        <h3 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '24px' }}>All Registered Clients</h3>
        
        {isLoading && clients.length === 0 ? (
          <div style={{ color: 'var(--color-outline)' }}>Loading clients...</div>
        ) : clients.length === 0 ? (
          <p style={{ color: 'var(--color-outline)' }}>No clients registered yet.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', padding: '16px', color: 'var(--color-outline)', borderBottom: '1px solid var(--color-outline-variant)', fontSize: '12px', textTransform: 'uppercase' }}>ID</th>
                <th style={{ textAlign: 'left', padding: '16px', color: 'var(--color-outline)', borderBottom: '1px solid var(--color-outline-variant)', fontSize: '12px', textTransform: 'uppercase' }}>Name</th>
                <th style={{ textAlign: 'left', padding: '16px', color: 'var(--color-outline)', borderBottom: '1px solid var(--color-outline-variant)', fontSize: '12px', textTransform: 'uppercase' }}>Contact</th>
                <th style={{ textAlign: 'left', padding: '16px', color: 'var(--color-outline)', borderBottom: '1px solid var(--color-outline-variant)', fontSize: '12px', textTransform: 'uppercase' }}>Place of Stay</th>
                <th style={{ textAlign: 'left', padding: '16px', color: 'var(--color-outline)', borderBottom: '1px solid var(--color-outline-variant)', fontSize: '12px', textTransform: 'uppercase' }}>Joined</th>
                <th style={{ textAlign: 'right', padding: '16px', color: 'var(--color-outline)', borderBottom: '1px solid var(--color-outline-variant)', fontSize: '12px', textTransform: 'uppercase' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {clients.map(client => (
                <tr key={client.id} style={{ borderBottom: '1px solid var(--color-outline-variant)', transition: 'background-color 0.2s' }} className="hover:bg-surface-variant/20">
                  <td style={{ padding: '16px', fontSize: '14px', color: 'var(--color-primary)' }}>#{client.id}</td>
                  <td style={{ padding: '16px', fontSize: '14px', fontWeight: '500' }}>{client.name}</td>
                  <td style={{ padding: '16px', fontSize: '14px', color: 'var(--color-on-surface-variant)' }}>{client.contact_info || '-'}</td>
                  <td style={{ padding: '16px', fontSize: '14px', color: 'var(--color-on-surface-variant)' }}>{client.place_of_stay || '-'}</td>
                  <td style={{ padding: '16px', fontSize: '14px', color: 'var(--color-on-surface-variant)' }}>
                    {new Date(client.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: '16px', textAlign: 'right' }}>
                    <button 
                      onClick={() => setSelectedClientId(client.id)}
                      style={{
                        background: 'transparent',
                        border: '1px solid var(--color-outline-variant)',
                        color: 'var(--color-primary)',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: '600',
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        transition: 'all 0.2s'
                      }}
                      onMouseOver={(e) => { e.currentTarget.style.backgroundColor = 'var(--color-surface-variant)'; }}
                      onMouseOut={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                    >
                      <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>visibility</span>
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <ClientDetailsPanel 
        clientId={selectedClientId} 
        onClose={() => setSelectedClientId(null)} 
        onClientUpdated={fetchClients} 
      />
    </>
  );
};

export default ClientList;
