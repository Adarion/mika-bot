import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function ConfigLLM() {
    const [llmConfig, setLlmConfig] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadConfig();
    }, []);

    const loadConfig = async () => {
        try {
            const data = await api.getConfig();
            setLlmConfig(data.llm || { providers: {} });
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const saveConfig = async () => {
        try {
            const config = await api.getConfig();
            config.llm = llmConfig;
            await api.saveConfig(config);
            alert('Saved successfully');
        } catch (error) {
            alert('Error saving: ' + error.message);
        }
    };

    const updateProvider = (name, field, value) => {
        setLlmConfig(prev => ({
            ...prev,
            providers: {
                ...prev.providers,
                [name]: {
                    ...prev.providers[name],
                    [field]: value
                }
            }
        }));
    };

    const addProvider = () => {
        const name = prompt('Provider name (e.g. openai):');
        if (!name) return;
        setLlmConfig(prev => ({
            ...prev,
            providers: {
                ...prev.providers,
                [name]: { model: '', api_key: '' }
            }
        }));
    };

    if (loading) return <div className="spinner" style={{ margin: '50px auto' }} />;

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 600 }}>LLM Configuration</h2>
                <button className="btn btn-primary" onClick={saveConfig}>Save Changes</button>
            </div>

            <div style={{ marginBottom: '1rem' }}>
                <button className="btn" style={{ background: 'var(--bg-hover)', color: 'white' }} onClick={addProvider}>
                    + Add Provider
                </button>
            </div>

            <div style={{ display: 'grid', gap: '1.5rem' }}>
                {Object.entries(llmConfig.providers || {}).map(([name, config]) => (
                    <div key={name} className="card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                            <h3 style={{ fontSize: '1.1rem', fontWeight: 500, textTransform: 'capitalize' }}>{name}</h3>
                            <button
                                className="btn btn-danger"
                                style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                                onClick={() => {
                                    if (confirm('Delete ' + name + '?')) {
                                        const newProviders = { ...llmConfig.providers };
                                        delete newProviders[name];
                                        setLlmConfig({ ...llmConfig, providers: newProviders });
                                    }
                                }}
                            >
                                Delete
                            </button>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Model</label>
                                <input
                                    className="input"
                                    value={config.model || ''}
                                    onChange={e => updateProvider(name, 'model', e.target.value)}
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>API Key</label>
                                <input
                                    type="password"
                                    className="input"
                                    value={config.api_key || ''}
                                    onChange={e => updateProvider(name, 'api_key', e.target.value)}
                                />
                            </div>

                            <div style={{ gridColumn: 'span 2' }}>
                                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Base URL (Optional)</label>
                                <input
                                    className="input"
                                    value={config.base_url || ''}
                                    onChange={e => updateProvider(name, 'base_url', e.target.value)}
                                />
                            </div>
                        </div>
                    </div>
                ))}

                {Object.keys(llmConfig.providers || {}).length === 0 && (
                    <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem' }}>
                        No providers configured. Click "Add Provider" to start.
                    </div>
                )}
            </div>
        </div>
    );
}
