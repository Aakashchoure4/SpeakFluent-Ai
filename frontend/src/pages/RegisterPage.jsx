/**
 * Registration page component.
 */

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { register, login, getMe } from '../services/api.js';
import { useAuth } from '../context/AuthContext.jsx';

export default function RegisterPage() {
    const navigate = useNavigate();
    const { setUser } = useAuth();
    const [form, setForm] = useState({
        username: '',
        email: '',
        password: '',
        full_name: '',
        preferred_language: 'en',
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await register(form);
            await login(form.username, form.password);
            const me = await getMe();
            setUser(me);
            navigate('/dashboard');
        } catch (err) {
            setError(err.message || 'Registration failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card glass-card">
                <h1>Create Account</h1>
                <p className="subtitle">Join SpeakFluent AI and break language barriers</p>

                {error && <div className="auth-error">{error}</div>}

                <form className="auth-form" onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label htmlFor="reg-fullname">Full Name</label>
                        <input
                            id="reg-fullname"
                            className="input"
                            type="text"
                            placeholder="Your full name"
                            value={form.full_name}
                            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                        />
                    </div>

                    <div className="input-group">
                        <label htmlFor="reg-username">Username</label>
                        <input
                            id="reg-username"
                            className="input"
                            type="text"
                            placeholder="Choose a username"
                            value={form.username}
                            onChange={(e) => setForm({ ...form, username: e.target.value })}
                            required
                            minLength={3}
                        />
                    </div>

                    <div className="input-group">
                        <label htmlFor="reg-email">Email</label>
                        <input
                            id="reg-email"
                            className="input"
                            type="email"
                            placeholder="you@example.com"
                            value={form.email}
                            onChange={(e) => setForm({ ...form, email: e.target.value })}
                            required
                        />
                    </div>

                    <div className="input-group">
                        <label htmlFor="reg-password">Password</label>
                        <input
                            id="reg-password"
                            className="input"
                            type="password"
                            placeholder="Minimum 6 characters"
                            value={form.password}
                            onChange={(e) => setForm({ ...form, password: e.target.value })}
                            required
                            minLength={6}
                        />
                    </div>

                    <div className="input-group">
                        <label htmlFor="reg-language">Preferred Language</label>
                        <select
                            id="reg-language"
                            className="input"
                            value={form.preferred_language}
                            onChange={(e) => setForm({ ...form, preferred_language: e.target.value })}
                        >
                            <option value="en">English</option>
                            <option value="hi">Hindi (हिन्दी)</option>
                        </select>
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary btn-lg"
                        disabled={loading}
                        id="register-submit"
                    >
                        {loading ? <span className="spinner" /> : 'Create Account'}
                    </button>
                </form>

                <div className="auth-footer">
                    Already have an account? <Link to="/login">Sign in here</Link>
                </div>
            </div>
        </div>
    );
}
