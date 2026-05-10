import { useState, useCallback, useEffect, useRef } from 'react';
import * as api from '../services/api';

const PLACEHOLDER_TITLE = "New Conversation"

export function useChat() {
  const [sessions, setSessions] = useState(null);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const creatingSession = useRef(false);

  const activeSession = sessions?.find(s => s.id === activeSessionId) || null;

  useEffect(() => {
    const fetchSessions = async () => {
      const raw = await api.getSessions();
      const normalized = raw.map(s => ({
        id: s.id,
        title: s.title,
        createdAt: s.created_at,
        updatedAt: s.updated_at,
        messages: null,
        completed: s.completed,
      }));
      setSessions(normalized);
    };
    fetchSessions();
  }, [])

  const createNewSession = useCallback(async () => {
    const { session } = await api.createSession();

    const newSession = {
      id: session.id,
      title: session.title,
      createdAt: session.created_at,
      updatedAt: session.updated_at,
      messages: null,
      completed: session.completed,
    };
    
    setSessions(prev => {
      if (prev === null) {
        return [newSession]
      }

      const updated = [newSession, ...prev];
      return updated;
    });

    setActiveSessionId(session.id);
    setError(null);
    return session.id;
  }, []);

  const selectSession = useCallback(async (id) => {
    if (sessions === null) {
      return
    }

    const current_session = sessions.find(s => s.id === id);

    if (!current_session) {
      setError('Session not found');
      return;
    }

    if (current_session.messages === null) {
      const rawMessages = await api.getSession(id)
      const messages = rawMessages.map(m => ({ ...m, timestamp: m.created_at }))

      setSessions(prev => {
        const updated = prev.map(s => {
          if (s.id !== id) {
            return s
          }

          return {...s, messages: messages}
        })

        return updated
      })
    }


    setActiveSessionId(id);
    setError(null);
  }, [sessions]);

  const deleteSession = useCallback((id) => {
    setSessions(prev => {
      const updated = prev.filter(s => s.id !== id);
      return updated;
    });

    api.deleteSession(id)

    setActiveSessionId(prev => prev === id ? null : prev);
  }, []);

  function capitalizeFirstLetter(val) {
      return String(val).charAt(0).toUpperCase() + String(val).slice(1);
  }

  const sendMessage = useCallback(async (text) => {
    if (!text.trim()) return;

    let sessionId = activeSessionId;
    if (!sessionId) {
      if (creatingSession.current) return;
      creatingSession.current = true;
      const { session } = await api.createSession();
      const { id, title, app_type, completed, schema_, created_at, updated_at } = session
      sessionId = id;

      let newTitle = null
      if (title == PLACEHOLDER_TITLE) {
        if (app_type !== null) {
          newTitle = `${capitalizeFirstLetter(app_type)} app${schema_?.context.app_name ? `: ${schema_.context.app_name}` : ""}`
        }
      }

      const newSession = {
        id: sessionId,
        title: newTitle || title,
        createdAt: created_at,
        updatedAt: updated_at,
        messages: [],
        completed: completed,
      };

      setSessions(prev => {
        if (prev === null) {
          return [newSession]
        }

        const updated = [newSession, ...prev];
        return updated;
      });

      setActiveSessionId(sessionId);
      creatingSession.current = false;
    }

    setIsLoading(true);
    setError(null);
    
    const tempUserMsg = {
      id: null,
      role: "user",
      content: text,
      timestamp: null
    }

    setSessions(prev => {
      const updated = prev?.map(s => {
        if (s.id !== sessionId) return s;

        if (s.messages === null) {
          return {
            ...s,
            messages: [tempUserMsg],
          };
        }

        return {
          ...s,
          messages: [...s.messages, tempUserMsg],
        };
      });

      return updated;
      });

    try {
      const { status, user_message, reply_message, completed} = await api.sendMessage(sessionId, text);


      const userMsg = {
        id: user_message.id,
        role: user_message.role,
        content: user_message.content,
        timestamp: user_message.created_at
      }

      setSessions(prev => {
        const updated = prev?.map(s => {
          if (s.id !== sessionId) return s;
          return {
            ...s,
            updatedAt: userMsg.timestamp,
            messages: s.messages.map(m => m === tempUserMsg ? userMsg : m),
          };
        });

        return updated;
       });
      
      const aiMsg = {
        id: reply_message.id,
        role: reply_message.role,
        content: reply_message.content,
        timestamp: reply_message.created_at,
      };

      setSessions(prev => {
        const updated = prev.map(s => {
          if (s.id !== sessionId) return s;
          return {
            ...s,
            updatedAt: aiMsg.timestamp,
            completed: completed,
            messages: [...s.messages, aiMsg],
          };
        });

        return updated;
      });

    } catch (err) {
      setError(err.message);

    } finally {
      setIsLoading(false);
    }


  }, [activeSessionId]);

  const sendHintMessage = useCallback(async (hint) => {
    sendMessage(hint)
  }, [sendMessage]);

  return {
    sessions,
    activeSession,
    activeSessionId,
    isLoading,
    error,
    createNewSession,
    selectSession,
    deleteSession,
    sendMessage,
    sendHintMessage,
  };
}
