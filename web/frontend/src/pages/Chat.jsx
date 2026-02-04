import { useState, useEffect, useRef } from 'react';

export default function Chat() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [status, setStatus] = useState('Connecting...');
    const wsRef = useRef(null);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        connect();
        return () => {
            if (wsRef.current) wsRef.current.close();
        };
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const connect = () => {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Use /ws path directly, vite proxy will handle it in dev, direct in prod
        const wsUrl = `${protocol}//${location.host}/ws`;

        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            setStatus('Connected');
        };

        ws.onclose = () => {
            setStatus('Disconnected');
            setTimeout(connect, 2000);
        };

        ws.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                if (data.content) {
                    setMessages(prev => [...prev, { text: data.content, sender: data.sender || 'bot' }]);
                }
            } catch (err) {
                console.error('WS Error:', err);
            }
        };

        wsRef.current = ws;
    };

    const sendMessage = (e) => {
        e.preventDefault();
        if (!input.trim() || !wsRef.current || wsRef.current.readyState !== 1) return;

        const text = input.trim();
        setMessages(prev => [...prev, { text, sender: 'user' }]);
        wsRef.current.send(JSON.stringify({ type: 'message', content: text }));
        setInput('');
    };

    return (
        <div style={{ height: 'calc(100vh - 6rem)', display: 'flex', flexDirection: 'column' }}>
            <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Chat Test</h2>
                <span style={{
                    fontSize: '0.875rem',
                    color: status === 'Connected' ? 'var(--accent)' : 'var(--danger)'
                }}>
                    ● {status}
                </span>
            </div>

            <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '0', overflow: 'hidden' }}>
                <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem' }}>
                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            style={{
                                display: 'flex',
                                justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                                marginBottom: '1rem'
                            }}
                        >
                            <div style={{
                                maxWidth: '70%',
                                padding: '0.75rem 1rem',
                                borderRadius: '0.75rem',
                                backgroundColor: msg.sender === 'user' ? 'var(--bg-hover)' : 'var(--bg-app)',
                                border: msg.sender === 'user' ? '1px solid var(--border)' : 'none',
                                whiteSpace: 'pre-wrap'
                            }}>
                                {msg.text}
                            </div>
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>

                <form onSubmit={sendMessage} style={{ padding: '1rem', borderTop: '1px solid var(--border)', display: 'flex', gap: '0.5rem' }}>
                    <input
                        className="input"
                        style={{ marginBottom: 0 }}
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        placeholder="Type a message..."
                    />
                    <button type="submit" className="btn btn-primary">Send</button>
                </form>
            </div>
        </div>
    );
}
