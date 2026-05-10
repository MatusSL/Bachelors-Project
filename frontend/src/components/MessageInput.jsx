import { useRef, useEffect, useState } from 'react';
import { Send, Loader2 } from 'lucide-react';

export default function MessageInput({ onSend, isLoading, disabled }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [text]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const submit = () => {
    if (!text.trim() || isLoading || disabled) return;
    onSend(text.trim());
    setText('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  return (
    <div className="border-t border-slate-200 bg-white px-4 py-4">
      <div className="max-w-3xl mx-auto">
        <div className={`flex items-end gap-3 bg-slate-50 border rounded-2xl px-4 py-3 transition-colors
          ${disabled ? 'opacity-50' : 'border-slate-200 focus-within:border-indigo-400 focus-within:bg-white focus-within:shadow-sm focus-within:shadow-indigo-100'}`}
        >
          <textarea
            ref={textareaRef}
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? 'Checklist generated — start a new conversation' : 'Describe your project or answer a question…'}
            disabled={disabled || isLoading}
            rows={1}
            className="flex-1 resize-none bg-transparent text-sm text-slate-800 placeholder:text-slate-400
                       outline-none leading-relaxed min-h-[24px] disabled:cursor-not-allowed"
          />
          <button
            onClick={submit}
            disabled={!text.trim() || isLoading || disabled}
            className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 transition-all
                       bg-indigo-600 text-white hover:bg-indigo-500 disabled:bg-slate-200 disabled:text-slate-400
                       disabled:cursor-not-allowed"
            title="Send (Enter)"
          >
            {isLoading
              ? <Loader2 size={15} className="animate-spin" />
              : <Send size={15} />
            }
          </button>
        </div>
        <p className="text-center text-xs text-slate-400 mt-2">
          Press <kbd className="px-1 py-0.5 bg-slate-100 rounded text-xs">Enter</kbd> to send,{' '}
          <kbd className="px-1 py-0.5 bg-slate-100 rounded text-xs">Shift+Enter</kbd> for new line
        </p>
      </div>
    </div>
  );
}
