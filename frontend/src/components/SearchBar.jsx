import React, { useState, useEffect, useRef } from 'react';
import { Search, X } from 'lucide-react';

export default function SearchBar({
  value,
  onChange,
  placeholder = "Search posts, topics, products or competitors...",
}) {
  const [localVal, setLocalVal] = useState(value || '');
  const inputRef = useRef(null);
  const timerRef = useRef(null);

  // Sync external value changes
  useEffect(() => {
    setLocalVal(value || '');
  }, [value]);

  // Debounced notification to parent
  const handleInputChange = (newVal) => {
    setLocalVal(newVal);
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      onChange(newVal);
    }, 350);
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const handleClear = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setLocalVal('');
    onChange('');
    if (inputRef.current) inputRef.current.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      if (timerRef.current) clearTimeout(timerRef.current);
      onChange(localVal);
    } else if (e.key === 'Escape') {
      handleClear();
    }
  };

  return (
    <div className="relative flex-1 min-w-[260px] sm:min-w-[320px]">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
        <Search className="w-4 h-4" />
      </div>
      <input
        ref={inputRef}
        type="search"
        aria-label="Search brand conversations"
        value={localVal}
        onChange={(e) => handleInputChange(e.target.value)}
        onBlur={() => {
          if (localVal !== value) onChange(localVal);
        }}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="block w-full appearance-none pl-10 pr-14 py-2.5 text-sm bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 transition-all"
      />
      <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center gap-1">
        {localVal ? (
          <button
            type="button"
            onClick={handleClear}
            className="p-1 text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300 rounded transition-colors"
            title="Clear search"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        ) : (
          <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-medium text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded shadow-2xs">
            /
          </kbd>
        )}
      </div>
    </div>
  );
}
