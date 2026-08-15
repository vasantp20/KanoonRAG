import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import Clients from './pages/Clients';
import Drafting from './pages/Drafting';
import Layout from './components/Layout';
import ResearchAssistant from './pages/ResearchAssistant';
import GeneralResearch from './pages/GeneralResearch';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        
        {/* Protected Routes inside Layout */}
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/case-research" element={<ResearchAssistant />} />
          <Route path="/general-research" element={<GeneralResearch />} />

          <Route path="/clients" element={<Clients />} />
          <Route path="/drafting" element={<Drafting />} />
          <Route path="/documents" element={<Dashboard />} />
          <Route path="/search" element={<Dashboard />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
