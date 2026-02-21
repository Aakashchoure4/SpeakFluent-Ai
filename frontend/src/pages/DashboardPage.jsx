/**
 * Dashboard page — list rooms, create room, join room.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { listRooms, createRoom, joinRoom } from '../services/api.js';

export default function DashboardPage() {
    const navigate = useNavigate();
    const { user, logout } = useAuth();
    const [rooms, setRooms] = useState([]);
    const [loading, setLoading] = useState(true);

    // Modal states
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showJoinModal, setShowJoinModal] = useState(false);
    const [createForm, setCreateForm] = useState({ name: '', max_participants: 10 });
    const [joinForm, setJoinForm] = useState({ room_code: '', language_mode: 'hi_to_en' });
    const [modalError, setModalError] = useState('');
    const [modalLoading, setModalLoading] = useState(false);

    const fetchRooms = useCallback(async () => {
        try {
            const data = await listRooms();
            setRooms(data);
        } catch (err) {
            console.error('Failed to fetch rooms:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchRooms();
    }, [fetchRooms]);

    const handleCreate = async (e) => {
        e.preventDefault();
        setModalError('');
        setModalLoading(true);
        try {
            const room = await createRoom(createForm.name, createForm.max_participants);
            setShowCreateModal(false);
            setCreateForm({ name: '', max_participants: 10 });
            navigate(`/meeting/${room.room_code}`);
        } catch (err) {
            setModalError(err.message);
        } finally {
            setModalLoading(false);
        }
    };

    const handleJoin = async (e) => {
        e.preventDefault();
        setModalError('');
        setModalLoading(true);
        try {
            const room = await joinRoom(joinForm.room_code, joinForm.language_mode);
            setShowJoinModal(false);
            setJoinForm({ room_code: '', language_mode: 'hi_to_en' });
            navigate(`/meeting/${room.room_code}`);
        } catch (err) {
            setModalError(err.message);
        } finally {
            setModalLoading(false);
        }
    };

    const formatDate = (dateStr) => {
        return new Date(dateStr).toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    return (
        <>
            {/* Navbar */}
            <nav className="navbar">
                <a href="/" className="navbar-brand">
                    <div className="logo-icon">🎙️</div>
                    SpeakFluent AI
                </a>
                <div className="navbar-actions">
                    <div className="navbar-user">
                        <div className="avatar">
                            {user?.username?.charAt(0).toUpperCase() || 'U'}
                        </div>
                        <span>{user?.username}</span>
                    </div>
                    <button className="btn btn-ghost" onClick={logout} id="logout-btn">
                        Logout
                    </button>
                </div>
            </nav>

            {/* Dashboard */}
            <div className="dashboard">
                <div className="dashboard-header">
                    <h1>Your Meetings</h1>
                    <div className="dashboard-actions">
                        <button
                            className="btn btn-secondary"
                            onClick={() => { setShowJoinModal(true); setModalError(''); }}
                            id="join-room-btn"
                        >
                            Join Room
                        </button>
                        <button
                            className="btn btn-primary"
                            onClick={() => { setShowCreateModal(true); setModalError(''); }}
                            id="create-room-btn"
                        >
                            + Create Room
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div style={{ textAlign: 'center', padding: '60px 0' }}>
                        <div className="spinner" style={{ margin: '0 auto' }} />
                    </div>
                ) : rooms.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-icon">🎤</div>
                        <h3>No meetings yet</h3>
                        <p>Create a new room or join an existing one to get started.</p>
                        <button
                            className="btn btn-primary"
                            onClick={() => setShowCreateModal(true)}
                        >
                            Create Your First Room
                        </button>
                    </div>
                ) : (
                    <div className="room-grid">
                        {rooms.map((room) => (
                            <div
                                key={room.id}
                                className="room-card glass-card"
                                onClick={() => navigate(`/meeting/${room.room_code}`)}
                            >
                                <div className="room-card-header">
                                    <h3>{room.name}</h3>
                                    <span className={`badge ${room.status === 'active' ? 'badge-success' : 'badge-error'}`}>
                                        {room.status}
                                    </span>
                                </div>
                                <div className="room-card-info">
                                    <span className="room-code">{room.room_code}</span>
                                    <span>📅 {formatDate(room.created_at)}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Create Room Modal */}
            {showCreateModal && (
                <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
                    <div className="modal-content glass-card" onClick={(e) => e.stopPropagation()}>
                        <h2>Create Meeting Room</h2>
                        {modalError && <div className="auth-error" style={{ marginBottom: 16 }}>{modalError}</div>}
                        <form onSubmit={handleCreate}>
                            <div className="input-group" style={{ marginBottom: 16 }}>
                                <label htmlFor="create-name">Room Name</label>
                                <input
                                    id="create-name"
                                    className="input"
                                    type="text"
                                    placeholder="e.g. Weekly Standup"
                                    value={createForm.name}
                                    onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                                    required
                                    autoFocus
                                />
                            </div>
                            <div className="input-group">
                                <label htmlFor="create-max">Max Participants</label>
                                <input
                                    id="create-max"
                                    className="input"
                                    type="number"
                                    min="2"
                                    max="100"
                                    value={createForm.max_participants}
                                    onChange={(e) => setCreateForm({ ...createForm, max_participants: parseInt(e.target.value) || 10 })}
                                />
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn btn-primary" disabled={modalLoading} id="create-room-submit">
                                    {modalLoading ? <span className="spinner" /> : 'Create Room'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Join Room Modal */}
            {showJoinModal && (
                <div className="modal-overlay" onClick={() => setShowJoinModal(false)}>
                    <div className="modal-content glass-card" onClick={(e) => e.stopPropagation()}>
                        <h2>Join Meeting Room</h2>
                        {modalError && <div className="auth-error" style={{ marginBottom: 16 }}>{modalError}</div>}
                        <form onSubmit={handleJoin}>
                            <div className="input-group" style={{ marginBottom: 16 }}>
                                <label htmlFor="join-code">Room Code</label>
                                <input
                                    id="join-code"
                                    className="input"
                                    type="text"
                                    placeholder="e.g. MX7K-A2QP"
                                    value={joinForm.room_code}
                                    onChange={(e) => setJoinForm({ ...joinForm, room_code: e.target.value.toUpperCase() })}
                                    required
                                    autoFocus
                                    style={{ fontFamily: 'var(--font-mono)', letterSpacing: '2px' }}
                                />
                            </div>
                            <div className="input-group">
                                <label htmlFor="join-mode">Translation Mode</label>
                                <select
                                    id="join-mode"
                                    className="input"
                                    value={joinForm.language_mode}
                                    onChange={(e) => setJoinForm({ ...joinForm, language_mode: e.target.value })}
                                >
                                    <option value="hi_to_en">Hindi → English</option>
                                    <option value="en_to_hi">English → Hindi</option>
                                </select>
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowJoinModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn btn-primary" disabled={modalLoading} id="join-room-submit">
                                    {modalLoading ? <span className="spinner" /> : 'Join Room'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </>
    );
}
