
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import SearchBuilder from './pages/SearchBuilder';
import DeepExplore from './pages/DeepExplore';
import LiteratureToolkit from './pages/LiteratureToolkit';
import ResearchSuggestions from './pages/ResearchSuggestions';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/literature-toolkit" element={<LiteratureToolkit />} />
              <Route path="/research-suggestions" element={<ResearchSuggestions />} />
              <Route path="/search-builder" element={<SearchBuilder />} />
              <Route path="/deep-explore" element={<DeepExplore />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
