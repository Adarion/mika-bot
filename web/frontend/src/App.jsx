import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ConfigLLM from './pages/ConfigLLM';
import ConfigIM from './pages/ConfigIM';
import Chat from './pages/Chat';
import Layout from './components/Layout';

function PrivateRoute() {
  const { user, loading, setupNeeded } = useAuth();

  if (loading) return <div className="spinner" style={{ margin: '50px auto' }} />;

  if (setupNeeded) return <Navigate to="/setup" />;
  if (!user) return <Navigate to="/login" />;

  return <Layout><Outlet /></Layout>;
}

function PublicRoute() {
  const { user, loading, setupNeeded } = useAuth();

  if (loading) return null;
  if (setupNeeded) return <Outlet />;
  if (user) return <Navigate to="/" />;

  return <Outlet />;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<PublicRoute />}>
            <Route path="/login" element={<Login mode="login" />} />
            <Route path="/setup" element={<Login mode="setup" />} />
          </Route>

          <Route element={<PrivateRoute />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/monitor" element={<Dashboard />} />
            <Route path="/llm" element={<ConfigLLM />} />
            <Route path="/im" element={<ConfigIM />} />
            <Route path="/chat" element={<Chat />} />
          </Route>

          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
