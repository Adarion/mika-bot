import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function Login({ mode = 'login' }) {
    const [password, setPassword] = useState('');
    const [confirm, setConfirm] = useState('');
    const [error, setError] = useState('');
    const { login, setup } = useAuth();
    const navigate = useNavigate();
    const isSetup = mode === 'setup';

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (isSetup && password !== confirm) {
            return setError('Passwords do not match');
        }

        try {
            if (isSetup) {
                await setup(password);
            } else {
                await login(password);
            }
            navigate('/');
        } catch (err) {
            setError(err.message || 'Failed to authenticate');
        }
    };

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'var(--bg-app)'
        }}>
            <div className="card" style={{ width: '100%', maxWidth: '400px' }}>
                <h1 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>
                    {isSetup ? 'Initial Setup' : 'Login'}
                </h1>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
                    {isSetup ? 'Create your admin password' : 'Enter password to access admin panel'}
                </p>

                {error && (
                    <div style={{
                        color: 'var(--danger)',
                        marginBottom: '1rem',
                        fontSize: '0.875rem'
                    }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <input
                        type="password"
                        className="input"
                        placeholder="Password"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        required
                        autoFocus
                    />

                    {isSetup && (
                        <input
                            type="password"
                            className="input"
                            placeholder="Confirm Password"
                            value={confirm}
                            onChange={e => setConfirm(e.target.value)}
                            required
                        />
                    )}

                    <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                        {isSetup ? 'Create Account' : 'Login'}
                    </button>
                </form>
            </div>
        </div>
    );
}
