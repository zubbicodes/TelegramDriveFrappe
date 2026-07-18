import React, { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, Loader, Pencil, Plus, Search, StickyNote, Trash2, X } from 'lucide-react';

const COLORS = {
  yellow: 'border-amber-200 bg-amber-50 dark:border-amber-500/40 dark:bg-amber-950/35',
  blue: 'border-sky-200 bg-sky-50 dark:border-sky-500/40 dark:bg-sky-950/35',
  green: 'border-emerald-200 bg-emerald-50 dark:border-emerald-500/40 dark:bg-emerald-950/35',
  pink: 'border-rose-200 bg-rose-50 dark:border-rose-500/40 dark:bg-rose-950/35',
  violet: 'border-violet-200 bg-violet-50 dark:border-violet-500/40 dark:bg-violet-950/35',
};

const COLOR_DOTS = {
  yellow: 'bg-amber-300',
  blue: 'bg-sky-300',
  green: 'bg-emerald-300',
  pink: 'bg-rose-300',
  violet: 'bg-violet-300',
};

const emptyDraft = { title: '', body: '', color: 'yellow' };

const CloudNotes = ({ api, currentUser = 'Owner', onBack }) => {
  const [notes, setNotes] = useState([]);
  const [query, setQuery] = useState('');
  const [draft, setDraft] = useState(emptyDraft);
  const [editing, setEditing] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const loadNotes = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.list();
      setNotes(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotes();
  }, []);

  const filteredNotes = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return notes;
    return notes.filter(note =>
      note.title.toLowerCase().includes(term) ||
      note.body.toLowerCase().includes(term) ||
      (note.created_by || '').toLowerCase().includes(term)
    );
  }, [notes, query]);

  const formatDateTime = (value) => {
    if (!value) return 'No date';
    const date = new Date(`${value}Z`);
    if (Number.isNaN(date.getTime())) return 'No date';
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const submitNote = async (e) => {
    e.preventDefault();
    if (!draft.title.trim() && !draft.body.trim()) return;
    setSaving(true);
    setError('');
    const formData = new FormData();
    formData.append('title', draft.title);
    formData.append('body', draft.body);
    formData.append('color', draft.color);
    try {
      if (editing) {
        await api.update(editing.id, formData);
      } else {
        await api.create(formData);
      }
      setDraft(emptyDraft);
      setEditing(null);
      await loadNotes();
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (note) => {
    setEditing(note);
    setDraft({ title: note.title, body: note.body, color: note.color || 'yellow' });
  };

  const cancelEdit = () => {
    setEditing(null);
    setDraft(emptyDraft);
  };

  const removeNote = async (note) => {
    if (!confirm('Delete this note?')) return;
    setError('');
    try {
      await api.remove(note.id);
      setNotes(prev => prev.filter(item => item.id !== note.id));
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col bg-[#f8fafc] dark:bg-gray-950">
      <div className="shrink-0 border-b border-gray-200 bg-white px-4 py-4 dark:border-gray-700 dark:bg-gray-900 lg:px-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm font-medium text-blue-600">
              {onBack && (
                <button onClick={onBack} className="rounded-lg p-1 text-gray-500 hover:bg-gray-100 hover:text-blue-600 dark:text-gray-400 dark:hover:bg-gray-800" title="Back to drive">
                  <ArrowLeft className="h-4 w-4" />
                </button>
              )}
              <StickyNote className="h-4 w-4" /> CloudNote
            </div>
            <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-gray-100">Shared sticky notes</h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{notes.length} notes on the board</p>
          </div>
          <div className="relative w-full lg:w-80">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search notes" className="w-full rounded-xl border border-gray-200 bg-gray-50 py-2 pl-9 pr-3 text-sm outline-none transition focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-100 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100 dark:focus:bg-gray-950 dark:focus:ring-blue-500/20" />
          </div>
        </div>
      </div>

      <div className="grid min-h-0 flex-1 gap-5 overflow-y-auto p-4 lg:grid-cols-[320px_1fr] lg:p-6">
        <form onSubmit={submitNote} className="h-fit rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">{editing ? 'Edit note' : 'New note'}</h2>
            {editing && (
              <button type="button" onClick={cancelEdit} className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800" title="Cancel edit">
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          {error && <div className="mb-3 rounded-lg bg-red-100 p-3 text-sm text-red-700">{error}</div>}
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Title</label>
          <input value={draft.title} onChange={e => setDraft(prev => ({ ...prev, title: e.target.value }))} maxLength={80} className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100" placeholder="Quick title" />
          <label className="mt-4 block text-sm font-medium text-gray-700 dark:text-gray-300">Note</label>
          <textarea value={draft.body} onChange={e => setDraft(prev => ({ ...prev, body: e.target.value }))} rows={8} maxLength={4000} className="mt-1 w-full resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100" placeholder="Write something for everyone..." />
          <div className="mt-4 flex items-center justify-between gap-3">
            <div className="flex gap-2">
              {Object.keys(COLORS).map(color => (
                <button key={color} type="button" onClick={() => setDraft(prev => ({ ...prev, color }))} className={`h-7 w-7 rounded-full border-2 ${COLOR_DOTS[color]} ${draft.color === color ? 'border-gray-900 dark:border-white' : 'border-white shadow-sm dark:border-gray-800'}`} title={color} />
              ))}
            </div>
            <button type="submit" disabled={saving || (!draft.title.trim() && !draft.body.trim())} className="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50">
              {saving ? <Loader className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              {editing ? 'Save' : 'Add'}
            </button>
          </div>
        </form>

        <div className="min-w-0">
          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <Loader className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : filteredNotes.length === 0 ? (
            <div className="rounded-xl border border-dashed border-gray-300 bg-white p-10 text-center text-gray-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-400">
              {query ? 'No matching notes.' : 'No notes yet.'}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {filteredNotes.map(note => (
                <article key={note.id} className={`group min-h-56 rounded-xl border p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md ${COLORS[note.color] || COLORS.yellow}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="break-words text-base font-semibold text-gray-900 dark:text-gray-100">{note.title}</h3>
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">By {note.created_by || currentUser} - {formatDateTime(note.updated_at || note.created_at)}</p>
                    </div>
                    <div className="flex shrink-0 gap-1 opacity-0 transition group-hover:opacity-100">
                      <button onClick={() => startEdit(note)} className="rounded-lg p-2 text-gray-600 hover:bg-white/70 dark:text-gray-300 dark:hover:bg-gray-900/70" title="Edit note">
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button onClick={() => removeNote(note)} className="rounded-lg p-2 text-red-500 hover:bg-white/70 dark:hover:bg-gray-900/70" title="Delete note">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  <p className="mt-4 whitespace-pre-wrap break-words text-sm leading-6 text-gray-700 dark:text-gray-200">{note.body}</p>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CloudNotes;
