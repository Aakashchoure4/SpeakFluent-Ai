/**
 * Custom hook for audio recording using MediaRecorder API.
 *
 * Records microphone audio in chunks and provides the recorded blob.
 */

import { useRef, useState, useCallback } from 'react';

export function useAudioRecorder({ onAudioReady, chunkDurationMs = 5000 }) {
    const [recording, setRecording] = useState(false);
    const mediaRecorderRef = useRef(null);
    const streamRef = useRef(null);
    const chunksRef = useRef([]);
    const intervalRef = useRef(null);

    const startRecording = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                },
            });

            streamRef.current = stream;

            // Prefer webm, fallback to other formats
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : MediaRecorder.isTypeSupported('audio/webm')
                    ? 'audio/webm'
                    : 'audio/mp4';

            const recorder = new MediaRecorder(stream, { mimeType });
            mediaRecorderRef.current = recorder;
            chunksRef.current = [];

            recorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    chunksRef.current.push(event.data);
                }
            };

            recorder.onstop = () => {
                if (chunksRef.current.length > 0) {
                    const blob = new Blob(chunksRef.current, { type: mimeType });
                    if (blob.size > 100 && onAudioReady) {
                        onAudioReady(blob);
                    }
                    chunksRef.current = [];
                }
            };

            recorder.start();
            setRecording(true);

            // Auto-stop and restart every chunkDurationMs to send periodic chunks
            intervalRef.current = setInterval(() => {
                if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
                    mediaRecorderRef.current.stop();
                    // Restart recording after a brief pause
                    setTimeout(() => {
                        if (streamRef.current && streamRef.current.active) {
                            try {
                                const newRecorder = new MediaRecorder(streamRef.current, { mimeType });
                                mediaRecorderRef.current = newRecorder;
                                chunksRef.current = [];

                                newRecorder.ondataavailable = (event) => {
                                    if (event.data && event.data.size > 0) {
                                        chunksRef.current.push(event.data);
                                    }
                                };

                                newRecorder.onstop = () => {
                                    if (chunksRef.current.length > 0) {
                                        const blob = new Blob(chunksRef.current, { type: mimeType });
                                        if (blob.size > 100 && onAudioReady) {
                                            onAudioReady(blob);
                                        }
                                        chunksRef.current = [];
                                    }
                                };

                                newRecorder.start();
                            } catch (err) {
                                console.error('Failed to restart recorder:', err);
                            }
                        }
                    }, 100);
                }
            }, chunkDurationMs);

        } catch (err) {
            console.error('Failed to start recording:', err);
            throw err;
        }
    }, [onAudioReady, chunkDurationMs]);

    const stopRecording = useCallback(() => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }

        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
            mediaRecorderRef.current.stop();
        }

        if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
        }

        setRecording(false);
    }, []);

    return { recording, startRecording, stopRecording };
}
