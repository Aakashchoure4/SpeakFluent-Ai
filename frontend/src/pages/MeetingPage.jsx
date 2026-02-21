/**
 * Meeting Room page — real-time audio translation with WebSocket.
 *
 * Features:
 *  - Live audio recording and streaming
 *  - Transcript display (original + translated)
 *  - Audio playback for translations
 *  - Participant sidebar
 *  - Language mode switching
 *  - Connection status indicator
 */

import React, { useEffect, useRef, useCallback, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { useWebSocket } from '../hooks/useWebSocket.js';
import { useAudioRecorder } from '../hooks/useAudioRecorder.js';
import { getRoomDetail, leaveRoom as apiLeaveRoom } from '../services/api.js';

export default function MeetingPage() {
    const { roomCode } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const transcriptEndRef = useRef(null);

    const [room, setRoom] = useState(null);
    const [mode, setMode] = useState('hi_to_en');
    const [autoPlay, setAutoPlay] = useState(true);

    const {
        status,
        participants,
        messages,
        connect,
        disconnect,
        sendAudio,
        changeMode,
    } = useWebSocket(roomCode);

    const onAudioReady = useCallback(
        (blob) => {
            sendAudio(blob);
        },
        [sendAudio]
    );

    const { recording, startRecording, stopRecording } = useAudioRecorder({
        onAudioReady,
        chunkDurationMs: 5000,
    });

    // Fetch room details
    useEffect(() => {
        async function fetchRoom() {
            try {
                const data = await getRoomDetail(roomCode);
                setRoom(data);
            } catch {
                navigate('/dashboard');
            }
        }
        fetchRoom();
    }, [roomCode, navigate]);

    // Connect WebSocket
    useEffect(() => {
        connect();
        return () => {
            disconnect();
            stopRecording();
        };
    }, [connect, disconnect, stopRecording]);

    // Auto-scroll transcript
    useEffect(() => {
        if (transcriptEndRef.current) {
            transcriptEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    // Auto-play latest audio
    useEffect(() => {
        if (!autoPlay || messages.length === 0) return;
        const last = messages[messages.length - 1];
        if (last.audioUrl) {
            const audio = new Audio(last.audioUrl);
            audio.volume = 0.8;
            audio.play().catch(() => { });
        }
    }, [messages, autoPlay]);

    const handleModeChange = (newMode) => {
        setMode(newMode);
        changeMode(newMode);
    };

    const handleLeave = async () => {
        stopRecording();
        disconnect();
        try {
            await apiLeaveRoom(roomCode);
        } catch { }
        navigate('/dashboard');
    };

    const toggleRecording = () => {
        if (recording) {
            stopRecording();
        } else {
            startRecording().catch((err) => {
                alert('Microphone access denied. Please allow microphone permissions.');
            });
        }
    };

    const getStatusText = () => {
        switch (status) {
            case 'connected': return 'Connected';
            case 'connecting': return 'Connecting…';
            default: return 'Disconnected';
        }
    };

    const getStatusClass = () => {
        switch (status) {
            case 'connected': return 'connected';
            case 'connecting': return 'connecting';
            default: return 'disconnected';
        }
    };

    const formatTime = (date) => {
        return new Date(date).toLocaleTimeString('en-IN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        });
    };

    const getLangLabel = (code) => {
        const map = { hi: 'Hindi', en: 'English' };
        return map[code] || code;
    };

    return (
        <>
            {/* Navbar */}
            <nav className="navbar">
                <a href="/dashboard" className="navbar-brand">
                    <div className="logo-icon">🎙️</div>
                    SpeakFluent AI
                </a>
                <div className="navbar-actions">
                    <div className={`connection-status ${getStatusClass()}`}>
                        <span
                            style={{
                                width: 8,
                                height: 8,
                                borderRadius: '50%',
                                background: status === 'connected' ? 'var(--success)' : status === 'connecting' ? 'var(--warning)' : 'var(--error)',
                                display: 'inline-block',
                            }}
                        />
                        {getStatusText()}
                    </div>
                    <button className="btn btn-danger" onClick={handleLeave} id="leave-meeting-btn">
                        Leave Meeting
                    </button>
                </div>
            </nav>

            {/* Meeting layout */}
            <div className="meeting-container">
                {/* Main content */}
                <div className="meeting-main">
                    {/* Header */}
                    <div className="meeting-header glass-card">
                        <div className="meeting-title">
                            <h2>{room?.name || 'Meeting Room'}</h2>
                            <span className="room-code-display">Room: {roomCode}</span>
                        </div>
                        <div className="meeting-controls">
                            {/* Mode selector */}
                            <div className="mode-selector">
                                <button
                                    className={`mode-option ${mode === 'hi_to_en' ? 'active' : ''}`}
                                    onClick={() => handleModeChange('hi_to_en')}
                                    id="mode-hi-en"
                                >
                                    हिन्दी → English
                                </button>
                                <button
                                    className={`mode-option ${mode === 'en_to_hi' ? 'active' : ''}`}
                                    onClick={() => handleModeChange('en_to_hi')}
                                    id="mode-en-hi"
                                >
                                    English → हिन्दी
                                </button>
                            </div>

                            {/* Auto-play toggle */}
                            <button
                                className={`btn btn-ghost`}
                                onClick={() => setAutoPlay(!autoPlay)}
                                title={autoPlay ? 'Auto-play ON' : 'Auto-play OFF'}
                                id="autoplay-toggle"
                            >
                                {autoPlay ? '🔊' : '🔇'}
                            </button>
                        </div>
                    </div>

                    {/* Transcript area */}
                    <div className="transcript-area glass-card">
                        {messages.length === 0 ? (
                            <div className="empty-state" style={{ padding: '40px 20px' }}>
                                <div className="empty-icon">💬</div>
                                <h3>No translations yet</h3>
                                <p>Press the record button and start speaking to see live translations.</p>
                            </div>
                        ) : (
                            messages.map((msg) => (
                                <div key={msg.id} className="transcript-item">
                                    <div className="transcript-item-header">
                                        <span className="transcript-item-user">
                                            {msg.username}
                                        </span>
                                        <div className="transcript-item-meta">
                                            <span className="badge badge-info">
                                                {getLangLabel(msg.sourceLang)} → {getLangLabel(msg.targetLang)}
                                            </span>
                                            <span>{formatTime(msg.timestamp)}</span>
                                        </div>
                                    </div>

                                    <div className="transcript-original">
                                        <strong>Original:</strong> {msg.originalText}
                                    </div>

                                    <div className="transcript-translated">
                                        {msg.translatedText}
                                    </div>

                                    {msg.audioUrl && (
                                        <div className="transcript-audio">
                                            <audio controls preload="none" src={msg.audioUrl}>
                                                Your browser does not support audio playback.
                                            </audio>
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                        <div ref={transcriptEndRef} />
                    </div>

                    {/* Recording bar */}
                    <div className="recording-bar glass-card">
                        <span className={`recording-status ${recording ? 'active' : ''}`}>
                            {recording ? '● Recording…' : 'Ready to record'}
                        </span>

                        <button
                            className={`record-btn ${recording ? 'recording' : ''}`}
                            onClick={toggleRecording}
                            disabled={status !== 'connected'}
                            title={recording ? 'Stop recording' : 'Start recording'}
                            id="record-btn"
                        />

                        <span className="recording-status" style={{ color: 'var(--text-muted)' }}>
                            {mode === 'hi_to_en' ? 'Speak Hindi' : 'Speak English'}
                        </span>
                    </div>
                </div>

                {/* Sidebar */}
                <div className="meeting-sidebar">
                    {/* Participants */}
                    <div className="sidebar-section glass-card">
                        <h3>Participants ({participants.length})</h3>
                        <div className="participant-list">
                            {participants.length === 0 ? (
                                <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
                                    No participants yet
                                </p>
                            ) : (
                                participants.map((p) => (
                                    <div key={p.user_id} className="participant-item">
                                        <div className="participant-avatar">
                                            {p.username.charAt(0).toUpperCase()}
                                        </div>
                                        <div className="participant-info">
                                            <div className="participant-name">
                                                {p.username}
                                                {p.user_id === user?.id && ' (You)'}
                                            </div>
                                            <div className="participant-mode">
                                                {p.language_mode === 'hi_to_en' ? 'Hindi → English' : 'English → Hindi'}
                                            </div>
                                        </div>
                                        <div className="online-dot" />
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Stats */}
                    <div className="sidebar-section glass-card">
                        <h3>Session Info</h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span>Messages</span>
                                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{messages.length}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span>Mode</span>
                                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                                    {mode === 'hi_to_en' ? 'HI → EN' : 'EN → HI'}
                                </span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span>Status</span>
                                <span className={`badge ${status === 'connected' ? 'badge-success' : 'badge-error'}`}>
                                    {status}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}
