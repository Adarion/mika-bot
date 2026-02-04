import { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';

function ProgressBar({ percent }) {
    let color = 'var(--accent)'; // Green
    if (percent >= 80) color = 'var(--danger)'; // Red
    else if (percent >= 60) color = '#eab308'; // Yellow

    return (
        <div style={{
            width: '100%',
            height: '8px',
            backgroundColor: 'var(--bg-hover)',
            borderRadius: '4px',
            marginTop: '12px',
            overflow: 'hidden'
        }}>
            <div style={{
                width: `${percent}%`,
                height: '100%',
                backgroundColor: color,
                borderRadius: '4px',
                transition: 'all 0.5s ease'
            }} />
        </div>
    );
}

function StatCard({ title, value, subtext, percent }) {
    return (
        <div className="card">
            <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.5rem' }}>
                {title}
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 600 }}>
                {value}
            </div>
            <ProgressBar percent={percent} />
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                {subtext}
            </div>
        </div>
    );
}

export default function Dashboard() {
    const [stats, setStats] = useState(null);
    const [error, setError] = useState(null);
    const timerRef = useRef(null);

    const fetchStats = async () => {
        try {
            const data = await api.getSystemStats();
            setStats(data);
        } catch (err) {
            console.error('Failed to fetch stats:', err);
            // Don't show full error UI on poll fail, maybe toast
        }
    };

    useEffect(() => {
        fetchStats();
        timerRef.current = setInterval(fetchStats, 5000);
        return () => clearInterval(timerRef.current);
    }, []);

    if (!stats) return <div className="spinner" style={{ margin: '50px auto' }} />;

    const formatBytes = (mb) => {
        if (mb >= 1024) return (mb / 1024).toFixed(1) + ' GB';
        return Math.round(mb) + ' MB';
    };

    const formatGB = (gb) => gb.toFixed(1) + ' GB';

    return (
        <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '2rem' }}>System Monitor</h2>

            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                gap: '1.5rem'
            }}>
                <StatCard
                    title="CPU Usage"
                    value={`${stats.cpu_percent.toFixed(1)}%`}
                    percent={stats.cpu_percent}
                    subtext={`Load Avg: ${stats.load_avg.map(x => x.toFixed(2)).join(', ')}`}
                />

                <StatCard
                    title="Memory"
                    value={`${formatBytes(stats.memory.used)} / ${formatBytes(stats.memory.total)}`}
                    percent={stats.memory.percent}
                    subtext={`Free: ${formatBytes(stats.memory.free)}`}
                />

                <StatCard
                    title="Swap"
                    value={`${formatBytes(stats.swap.used)} / ${formatBytes(stats.swap.total)}`}
                    percent={stats.swap.percent}
                    subtext={`Free: ${formatBytes(stats.swap.free)}`}
                />

                <StatCard
                    title="Disk (/)"
                    value={`${formatGB(stats.disk.used)} / ${formatGB(stats.disk.total)}`}
                    percent={stats.disk.percent}
                    subtext={`Free: ${formatGB(stats.disk.free)}`}
                />
            </div>
        </div>
    );
}
