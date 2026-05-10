import { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import AuthPage from './components/AuthPage';
import { useChat } from './hooks/useChat';

function ProtectedRoute({ children }) {
  const { session, loading } = useAuth();

  if (loading) {
    return <div className="flex h-full items-center justify-center">Loading...</div>;
  }

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function MainApp() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const {
    sessions,
    activeSession,
    isLoading,
    error,
    createNewSession,
    selectSession,
    deleteSession,
    sendMessage,
    sendHintMessage,
  } = useChat();

  return (
    <div className="flex h-full bg-slate-50">

      <div
        className={`transition-all duration-200 overflow-hidden shrink-0
          ${sidebarOpen ? 'w-72' : 'w-0'}`}
      >
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSession?.id || null}
          onSelect={selectSession}
          onNew={createNewSession}
          onDelete={deleteSession}
          onClose={() => setSidebarOpen(false)}
        />
      </div>


      <ChatWindow
        session={activeSession}
        isLoading={isLoading}
        error={error}
        onSend={sendMessage}
        onToggleSidebar={() => setSidebarOpen(v => !v)}
        onSendHint={sendHintMessage}
      />
    </div>
  );
}

export default function App() {
  const { session, loading } = useAuth();

  if (loading) {
    return <div className="flex h-full items-center justify-center">Loading...</div>;
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={session ? <Navigate to="/" replace /> : <AuthPage />}
      />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <MainApp />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
