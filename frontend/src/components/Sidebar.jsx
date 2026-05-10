import { MessageSquare, Plus, Trash2, CheckCircle, ChevronLeft, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

function groupSessions(sessions) {
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterdayStart = new Date(todayStart - 86400000);
  const weekStart = new Date(todayStart - 6 * 86400000);

  const groups = { Today: [], Yesterday: [], 'This week': [], Older: [] };

  for (const s of sessions) {
    const d = new Date(s?.updatedAt);
    if (d >= todayStart) groups['Today'].push(s);
    else if (d >= yesterdayStart) groups['Yesterday'].push(s);
    else if (d >= weekStart) groups['This week'].push(s);
    else groups['Older'].push(s);
  }

  return groups;
}

export default function Sidebar({ sessions, activeSessionId, onSelect, onNew, onDelete, onClose }) {
  const { user, signOut } = useAuth();
  const groups = sessions ? groupSessions(sessions) : { Today: [], Yesterday: [], 'This week': [], Older: [] };

  return (
    <aside className="flex flex-col h-full bg-slate-900 text-slate-100 w-72 shrink-0">

      <div className="flex items-center justify-between px-4 py-4 border-b border-slate-700/60">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-indigo-500 flex items-center justify-center shrink-0">
            <MessageSquare size={14} className="text-white" />
          </div>
          <span className="font-semibold text-sm text-white tracking-tight">TestBot</span>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-700/60 transition-colors"
          title="Collapse sidebar"
        >
          <ChevronLeft size={16} />
        </button>
      </div>


      <div className="px-3 py-3">
        <button
          onClick={onNew}
          className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium
                     bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
        >
          <Plus size={16} />
          New conversation
        </button>
      </div>


      <nav className="flex-1 overflow-y-auto scrollbar-thin px-2 pb-4">
        {!sessions || sessions.length === 0 && (
          <p className="text-center text-slate-500 text-xs mt-8 px-4">
            No conversations yet. Start one!
          </p>
        )}

        {Object.entries(groups).map(([label, items]) => {
          if (items.length === 0) return null;
          return (
            <div key={label} className="mb-2">
              <p className="px-2 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                {label}
              </p>
              <ul className="space-y-0.5">
                {items.map(session => (
                  <SessionItem
                    key={session.id}
                    session={session}
                    isActive={session.id === activeSessionId}
                    onSelect={onSelect}
                    onDelete={onDelete}
                  />
                ))}
              </ul>
            </div>
          );
        })}
      </nav>


      <div className="px-3 py-3 border-t border-slate-700/60 space-y-2">
        <div className="px-2 text-xs text-slate-500 truncate">
          {user?.email}
        </div>
        <button
          onClick={signOut}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm
                     text-slate-400 hover:text-white hover:bg-slate-700/60 transition-colors"
        >
          <LogOut size={14} />
          Sign out
        </button>
      </div>
    </aside>
  );
}

function SessionItem({ session, isActive, onSelect, onDelete }) {
  return (
    <li>
      <div
        className={`group flex items-center gap-2 px-2 py-2 rounded-lg cursor-pointer transition-colors
          ${isActive
            ? 'bg-indigo-600/20 text-white border border-indigo-500/30'
            : 'text-slate-300 hover:bg-slate-700/50 hover:text-white border border-transparent'
          }`}
        onClick={() => onSelect(session.id)}
      >
        <div className="flex items-center gap-1.5 flex-1 min-w-0">
          {session.completed
            ? <CheckCircle size={13} className="text-green-400 shrink-0" />
            : <MessageSquare size={13} className={isActive ? 'text-indigo-400' : 'text-slate-500'} />
          }
          <span className="text-sm truncate flex-1">{session.title}</span>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(session.id); }}
          className="opacity-0 group-hover:opacity-100 p-1 rounded text-slate-500 hover:text-red-400
                     transition-all shrink-0"
          title="Delete conversation"
        >
          <Trash2 size={12} />
        </button>
      </div>
    </li>
  );
}
