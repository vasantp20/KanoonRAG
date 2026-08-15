import React, { useState } from 'react';
import NewClientForm from '../components/clients/NewClientForm';
import NewCaseForm from '../components/clients/NewCaseForm';
import ClientList from '../components/clients/ClientList';
import './Clients.css';

const Clients = () => {
  const [activeTab, setActiveTab] = useState('new-client');

  const renderTabContent = () => {
    switch (activeTab) {
      case 'new-client':
        return <NewClientForm />;
      case 'new-case':
        return <NewCaseForm onGoToNewClient={() => setActiveTab('new-client')} />;
      case 'view-all':
        return <ClientList />;
      default:
        return <ClientList />;
    }
  };

  return (
    <div className="clients-container">
      {/* Header Section */}
      <div className="clients-header">
        <h2 className="clients-title">Client Management</h2>
        <p className="clients-subtitle">Manage and register new entities within the KanoonRAG intelligence ecosystem.</p>
      </div>

      {/* Sub-Tabs Navigation */}
      <div className="clients-tabs">
        <button 
          className={`tab-btn ${activeTab === 'new-client' ? 'active' : ''}`}
          onClick={() => setActiveTab('new-client')}
        >
          New Client Registration
        </button>
        <button 
          className={`tab-btn ${activeTab === 'new-case' ? 'active' : ''}`}
          onClick={() => setActiveTab('new-case')}
        >
          New Case
        </button>
        <button 
          className={`tab-btn ${activeTab === 'view-all' ? 'active' : ''}`}
          onClick={() => setActiveTab('view-all')}
        >
          View All Clients
        </button>
      </div>

      {/* Active Tab Content Area */}
      <div className="tab-content-area">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default Clients;
