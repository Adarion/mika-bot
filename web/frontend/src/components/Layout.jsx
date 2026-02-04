import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Layout({ children }) {
    const { logout } = useAuth();
    const location = useLocation();

    const navItems = [
        { label: 'Dashboard', path: '/' },
        { label: 'LLM Config', path: '/llm' },
        { label: 'IM Config', path: '/im' },
        { label: 'Chat Test', path: '/chat' },
    ];

    return (
        <div style={{ display: 'flex', minHeight: '100vh' }}>
            <nav style={{
                width: '240px',
                backgroundColor: 'var(--bg-surface)',
                borderRight: '1px solid var(--border)',
                padding: '2rem 0',
                display: 'flex',
                flexDirection: 'column'
            }}>
                <div style={{ padding: '0 2rem 2rem', borderBottom: '1px solid var(--border)', marginBottom: '1rem' }}>
                    <h1 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Mika Bot</h1>
                    <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Admin Panel</span>
                </div>

                <div style={{ flex: 1 }}>
                    {navItems.map(item => (
                        <Link
                            key={item.path}
                            to={item.path}
                            style={{
                                display: 'block',
                                padding: '0.75rem 2rem',
                                color: location.pathname === item.path ? 'var(--text-primary)' : 'var(--text-secondary)',
                                backgroundColor: location.pathname === item.path ? 'var(--bg-hover)' : 'transparent',
                                borderLeft: location.pathname === item.path ? '3px solid var(--accent)' : '3px solid transparent',
                                transition: 'all 0.2s'
                            }}
                        >
                            {item.label}
                        </Link>
                    ))}
                </div>

                <div style={{ padding: '2rem' }}>
                    <button
                        onClick={logout}
                        style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--text-secondary)',
                            fontSize: '0.875rem',
                            cursor: 'pointer'
                        }}
                    >
                        Logout
                    </button>
                </div>
            </nav>

            <main style={{ flex: 1, padding: '3rem', overflowY: 'auto' }}>
                {children}
            </main>
        </div>
    );
}
