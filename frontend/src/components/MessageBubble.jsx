import { Bot, User } from 'lucide-react';

function formatTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return '';
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function renderContent(text) {
  if (!text) return '';

  const codeBlockRegex = /```[\s\S]*?```/g;
  const parts = [];
  let lastIndex = 0;

  text.replace(codeBlockRegex, (match, offset) => {
    if (offset > lastIndex) {
      parts.push({ type: 'text', content: text.slice(lastIndex, offset) });
    }
    const code = match.slice(3, -3).replace(/^\w+\n/, '');
    parts.push({ type: 'code', content: code });
    lastIndex = offset + match.length;
  });

  if (lastIndex < text.length) {
    parts.push({ type: 'text', content: text.slice(lastIndex) });
  }

  return parts.map((part, i) => {
    if (part.type === 'code') {
      return (
        <pre key={i} className="bg-slate-900 text-green-300 rounded-lg p-3 text-xs whitespace-pre-wrap break-words my-2 font-mono">
          {part.content.trim()}
        </pre>
      );
    }
    return (
      <span key={i}>
        {part.content.split('\n').map((line, j, arr) => (
          <span key={j}>
            {renderInline(line)}
            {j < arr.length - 1 && <br />}
          </span>
        ))}
      </span>
    );
  });
}

function renderInline(text) {
  if (!text) return '';

  const tokens = [];
  const regex = /(`[^`]+`|\*\*[^*]+\*\*)/g;
  let last = 0;

  text.replace(regex, (match, _, offset) => {
    if (offset > last) tokens.push(text.slice(last, offset));
    if (match.startsWith('`')) {
      tokens.push(
        <code key={offset} className="bg-slate-100 text-indigo-700 px-1.5 py-0.5 rounded text-xs font-mono">
          {match.slice(1, -1)}
        </code>
      );
    } else {
      tokens.push(<strong key={offset} className="font-semibold">{match.slice(2, -2)}</strong>);
    }
    last = offset + match.length;
  });
  if (last < text.length) tokens.push(text.slice(last));
  return tokens;
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end gap-3 group">
        <div className="max-w-[75%]">
          <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed">
            {message.content}
          </div>
          <p className="text-right text-xs text-slate-400 mt-1 mr-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {formatTime(message.timestamp)}
          </p>
        </div>
        <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center shrink-0 mt-0.5">
          <User size={14} className="text-indigo-600" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 group">
      <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center shrink-0 mt-0.5">
        <Bot size={14} className="text-slate-600" />
      </div>
      <div className="max-w-[90%]">
        <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed text-slate-800 shadow-sm">
          {renderContent(message.content)}
        </div>
        <p className="text-xs text-slate-400 mt-1 ml-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {formatTime(message.timestamp)}
        </p>
      </div>
    </div>
  );
}
