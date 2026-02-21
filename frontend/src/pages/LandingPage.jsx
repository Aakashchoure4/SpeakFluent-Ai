/**
 * Landing page — hero section with feature highlights.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';

export default function LandingPage() {
    const navigate = useNavigate();
    const { user } = useAuth();

    return (
        <div className="landing-hero">
            <h1>Break Language Barriers<br />in Real Time</h1>
            <p className="hero-subtitle">
                AI-powered live meeting interpreter that translates between Hindi and English instantly —
                with real-time voice output, so everyone understands everything.
            </p>
            <div className="landing-actions">
                {user ? (
                    <button className="btn btn-primary btn-lg" onClick={() => navigate('/dashboard')}>
                        Go to Dashboard
                    </button>
                ) : (
                    <>
                        <button className="btn btn-primary btn-lg" onClick={() => navigate('/register')}>
                            Get Started Free
                        </button>
                        <button className="btn btn-secondary btn-lg" onClick={() => navigate('/login')}>
                            Sign In
                        </button>
                    </>
                )}
            </div>

            <div className="features-grid">
                <div className="feature-card glass-card">
                    <div className="feature-icon">🎙️</div>
                    <h3>Live Transcription</h3>
                    <p>
                        Powered by OpenAI Whisper for accurate real-time speech-to-text
                        in both Hindi and English.
                    </p>
                </div>
                <div className="feature-card glass-card">
                    <div className="feature-icon">🌐</div>
                    <h3>Instant Translation</h3>
                    <p>
                        Hindi ↔ English translation with automatic language detection
                        and high accuracy using AI models.
                    </p>
                </div>
                <div className="feature-card glass-card">
                    <div className="feature-icon">🔊</div>
                    <h3>Voice Output</h3>
                    <p>
                        Natural-sounding voice synthesis using Edge-TTS, so you can
                        hear translations spoken aloud.
                    </p>
                </div>
                <div className="feature-card glass-card">
                    <div className="feature-icon">👥</div>
                    <h3>Meeting Rooms</h3>
                    <p>
                        Create private rooms and invite participants. Everyone gets
                        real-time translated captions and audio.
                    </p>
                </div>
                <div className="feature-card glass-card">
                    <div className="feature-icon">⚡</div>
                    <h3>Low Latency</h3>
                    <p>
                        WebSocket streaming for near-instant audio processing
                        and translation delivery to all participants.
                    </p>
                </div>
                <div className="feature-card glass-card">
                    <div className="feature-icon">🔒</div>
                    <h3>Secure & Private</h3>
                    <p>
                        JWT authentication, encrypted connections, and private
                        meeting rooms keep your conversations safe.
                    </p>
                </div>
            </div>
        </div>
    );
}
