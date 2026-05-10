import { useEffect, useRef, useState } from 'react';
import { Menu, CheckCircle, ClipboardList, Bot, Download } from 'lucide-react';
import MessageBubble from './MessageBubble';
import MessageInput from './MessageInput';
import { exportChecklist } from '../services/api';

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center shrink-0">
        <Bot size={14} className="text-slate-600" />
      </div>
      <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <div className="flex gap-1 items-center h-5">
          <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}

function EmptyState({ onNew }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-6 px-4 text-center">
      <div className="w-16 h-16 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center">
        <ClipboardList size={28} className="text-indigo-500" />
      </div>
      <div>
        <h2 className="text-xl font-semibold text-slate-800 mb-2">
          Testing Checklist Assistant
        </h2>
        <p className="text-slate-500 text-sm max-w-sm">
          Tell me about your project and I'll help you generate a comprehensive testing checklist.
          Works with web apps, mobile, desktop, and APIs.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-3 max-w-sm w-full">
        {[
          'I\'m building a web app',
          'I\'m building a mobile app',
          'I\'m building a desktop app',
          'I\'m building an API',
        ].map(hint => (
          <button
            key={hint}
            onClick={() => onNew(hint)}
            className="text-left p-3 rounded-xl border border-slate-200 bg-white hover:border-indigo-300
                       hover:bg-indigo-50 transition-colors text-xs text-slate-600 hover:text-indigo-700 cursor-pointer"
          >
            "{hint}"
          </button>
        ))}
      </div>
    </div>
  );
}

function CompletedBanner({ sessionId }) {
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    try {
      await exportChecklist(sessionId);
    } catch (e) {
      console.error('Export failed:', e);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="mx-4 mb-4 flex items-center gap-3 bg-green-50 border border-green-200 rounded-xl px-4 py-3">
      <CheckCircle size={18} className="text-green-500 shrink-0" />
      <div className="flex-1">
        <p className="text-sm font-medium text-green-800">Checklist generated!</p>
        <p className="text-xs text-green-600">Your testing checklist is ready. Start a new conversation to test another project.</p>
      </div>
      <button
        onClick={handleExport}
        disabled={exporting}
        className="shrink-0 flex items-center gap-1.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
      >
        <Download size={14} />
        {exporting ? 'Exporting...' : 'Export to Excel'}
      </button>
    </div>
  );
}

export default function ChatWindow({ session, isLoading, error, onSend, onToggleSidebar, onSendHint }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [session?.messages, isLoading]);

  const messages = session?.messages || [];
  const isEmpty = !session || messages.length === 0;
  const isCompleted = session?.completed;

  return (
    <div className="flex flex-col flex-1 min-w-0 bg-slate-50">
      {/* Top bar */}
      <header className="flex items-center gap-3 px-4 py-3 bg-white border-b border-slate-200 shrink-0">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          title="Toggle sidebar"
        >
          <Menu size={18} />
        </button>
        <div className="flex-1 min-w-0">
          {session ? (
            <div className="flex items-center gap-2 min-w-0">
              <h1 className="font-semibold text-sm text-slate-800 truncate">
                {session.title}
              </h1>
              {isCompleted && (
                <span className="shrink-0 flex items-center gap-1 bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full font-medium">
                  <CheckCircle size={10} />
                  Done
                </span>
              )}
            </div>
          ) : (
            <h1 className="font-semibold text-sm text-slate-400">No conversation selected</h1>
          )}
        </div>
      </header>

      {/* Messages */}
      {isEmpty ? (
        <EmptyState onNew={onSendHint} />
      ) : (
        <div className="flex-1 overflow-y-auto chat-scrollbar px-4 py-6">
          <div className="max-w-3xl mx-auto space-y-5">
            {messages.map(msg => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isLoading && <TypingIndicator />}
            {error && (
              <div className="text-center">
                <p className="inline-block bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg px-4 py-2">
                  {error} — check that the backend is running at localhost:8000
                </p>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </div>
      )}

      {isCompleted && <CompletedBanner sessionId={session.id} />}

      <MessageInput
        onSend={onSend}
        isLoading={isLoading}
        disabled={isCompleted}
      />
    </div>
  );
}
