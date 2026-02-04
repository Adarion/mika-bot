import { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [setupNeeded, setSetupNeeded] = useState(false);

    const checkAuth = async () => {
        try {
            const data = await api.checkAuth();
            if (data.authenticated) {
                setUser({ authenticated: true });
            } else {
                setUser(null);
            }
            setSetupNeeded(data.setup_needed);
        } catch (error) {
            console.error('Auth check failed:', error);
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        checkAuth();
    }, []);

    const login = async (password) => {
        await api.login(password);
        await checkAuth();
    };

    const setup = async (password) => {
        await api.setup(password);
        await checkAuth();
    };

    const logout = async () => {
        await api.logout();
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, loading, setupNeeded, login, logout, setup, checkAuth }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
