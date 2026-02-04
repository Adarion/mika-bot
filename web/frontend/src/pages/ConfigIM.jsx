import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function ConfigIM() {
    const [imConfig, setImConfig] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadConfig();
    }, []);

    const loadConfig = async () => {
        try {
            const data = await api.getConfig();
            setImConfig(data.im || []);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const saveConfig = async () => {
        try {
            const config = await api.getConfig();
            config.im = imConfig;
            await api.saveConfig(config);
            alert('Saved successfully');
        } catch (error) {
            alert('Error saving: ' + error.message);
        }
    };

    const updatePlatform = (index, field, value) => {
        const newConfig = [...imConfig];
        newConfig[index] = { ...newConfig[index], [field]: value };
        setImConfig(newConfig);
    };

    const addPlatform = () => {
        setImConfig([...imConfig, { type: 'qq', app_id: '', secret: '' }]);
    };

    if (loading) return <div className="spinner" style={{ margin: '50px auto' }} />;

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 600 }}>IM Configuration</h2>
                <button className="btn btn-primary" onClick={saveConfig}>Save Changes</button>
            </div>

            <div style={{ marginBottom: '1rem' }}>
                <button className="btn" style={{ background: 'var(--bg-hover)', color: 'white' }} onClick={addPlatform}>
                    + Add Platform
                </button>
            </div>

            <div style={{ display: 'grid', gap: '1.5rem' }}>
                {imConfig.map((platform, idx) => (
                    <div key={idx} className="card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                            <h3 style={{ fontSize: '1.1rem', fontWeight: 500 }}>
                                {platform.type === 'qq' ? 'QQ Bot' : platform.type}
                            </h3>
                            <button
                                className="btn btn-danger"
                                style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                                onClick={() => {
                                    if (confirm('Delete platform?')) {
                                        const newConfig = [...imConfig];
                                        newConfig.splice(idx, 1);
                                        setImConfig(newConfig);
                                    }
                                }}
                            >
                                Delete
                            </button>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Type</label>
                                <select
                                    className="input"
                                    value={platform.type}
                                    onChange={e => updatePlatform(idx, 'type', e.target.value)}
                                >
                                    <option value="qq">QQ</option>
                                    <option value="web">Web</option>
                                </select>
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>App ID</label>
                                <input
                                    className="input"
                                    value={platform.app_id || ''}
                                    onChange={e => updatePlatform(idx, 'app_id', e.target.value)}
                                />
                            </div>

                            <div>
                                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Secret</label>
                                <input
                                    type="password"
                                    className="input"
                                    value={platform.secret || ''}
                                    onChange={e => updatePlatform(idx, 'secret', e.target.value)}
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Token</label>
                                <input
                                    type="password"
                                    className="input"
                                    value={platform.token || ''}
                                    onChange={e => updatePlatform(idx, 'token', e.target.value)}
                                />
                            </div>
                        </div>
                    </div>
                ))}

                {imConfig.length === 0 && (
                    <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem' }}>
                        No platforms configured.
                    </div>
                )}
            </div>
        </div>
    );
}
