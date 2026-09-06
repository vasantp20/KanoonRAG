import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import Login from './pages/Login';
import Signup from './pages/Signup';
import GeneralResearch from './pages/GeneralResearch';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        
        {/* Protected Route for General Research */}
        <Route path="/dashboard" element={<Navigate to="/general-research" replace />} />
        <Route path="/general-research" element={<GeneralResearch />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
