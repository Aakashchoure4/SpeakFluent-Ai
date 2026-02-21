/**
 * Custom hook for WebSocket connection to a meeting room.
 *
 * Handles connection lifecycle, message routing, and reconnection.
 */

import { useRef, useState, useCallback, useEffect } from 'react';
import { getToken } from '../services/api.js';

export function useWebSocket(roomCode) {
    const wsRef = useRef(null);
    const [status, setStatus] = useState('disconnected'); // connected | disconnected | connecting
    const [participants, setParticipants] = useState([]);
    const [messages, setMessages] = useState([]);
    const reconnectTimer = useRef(null);
    const manualClose = useRef(false);

    const connect = useCallback(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

        const token = getToken();
        if (!token || !roomCode) return;

        manualClose.current = false;
        setStatus('connecting');

        // Build WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const url = `${protocol}//${host}/ws/${roomCode}?token=${token}`;

        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
            setStatus('connected');
            console.log('[WS] Connected to room:', roomCode);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                switch (data.type) {
                    case 'connection_established':
                        setParticipants(data.participants || []);
                        break;

                    case 'user_joined':
                        setParticipants(data.participants || []);
                        break;

                    case 'user_left':
                        setParticipants(data.participants || []);
                        break;

                    case 'translation_result':
                        setMessages((prev) => [
                            ...prev,
                            {
                                id: Date.now() + Math.random(),
                                username: data.username,
                                userId: data.user_id,
                                originalText: data.original_text,
                                translatedText: data.translated_text,
                                sourceLang: data.source_language,
                                targetLang: data.target_language,
                                audioUrl: data.audio_url,
                                confidence: data.confidence,
                                timestamp: new Date(),
                            },
                        ]);
                        break;

                    case 'mode_changed':
                        console.log('[WS] Mode changed to:', data.mode);
                        break;

                    case 'pong':
                        break;

                    default:
                        console.log('[WS] Unknown message type:', data.type);
                }
            } catch (err) {
                console.error('[WS] Failed to parse message:', err);
            }
        };

        ws.onerror = (error) => {
            console.error('[WS] Error:', error);
        };

        ws.onclose = (event) => {
            setStatus('disconnected');
            console.log('[WS] Disconnected:', event.code, event.reason);

            // Auto-reconnect unless manually closed
            if (!manualClose.current) {
                reconnectTimer.current = setTimeout(() => {
                    console.log('[WS] Reconnecting...');
                    connect();
                }, 3000);
            }
        };
    }, [roomCode]);

    const disconnect = useCallback(() => {
        manualClose.current = true;
        if (reconnectTimer.current) {
            clearTimeout(reconnectTimer.current);
            reconnectTimer.current = null;
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        setStatus('disconnected');
    }, []);

    const sendAudio = useCallback((audioBlob) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            audioBlob.arrayBuffer().then((buffer) => {
                wsRef.current.send(buffer);
            });
        }
    }, []);

    const changeMode = useCallback((mode) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'change_mode', mode }));
        }
    }, []);

    const sendPing = useCallback(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'ping' }));
        }
    }, []);

    // Ping every 30 seconds to keep connection alive
    useEffect(() => {
        const interval = setInterval(sendPing, 30000);
        return () => clearInterval(interval);
    }, [sendPing]);

    // Cleanup on unmount
    useEffect(() => {
        return () => disconnect();
    }, [disconnect]);

    return {
        status,
        participants,
        messages,
        connect,
        disconnect,
        sendAudio,
        changeMode,
        clearMessages: () => setMessages([]),
    };
}
