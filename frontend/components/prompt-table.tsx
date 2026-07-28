"use client";

import { useEffect, useMemo, useState } from "react";
import { Copy, FlaskConical, LoaderCircle, Pencil, Plus, Search, Trash2, X } from "lucide-react";
import { api, PromptRecord } from "@/lib/api";

const emptyPrompt: Partial<PromptRecord> = { name: "", category: "Other", content: "", status: "Draft" };

export function PromptTable() {
  const [prompts, setPrompts] = useState<PromptRecord[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [editing, setEditing] = useState<Partial<PromptRecord> | null>(null);
  const [testInput, setTestInput] = useState("");
  const [testing, setTesting] = useState<PromptRecord | null>(null);
  const [testResult, setTestResult] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true); setError("");
    try { setPrompts(await api<PromptRecord[]>("/api/prompts")); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not load prompts."); }
    finally { setLoading(false); }
  }

  useEffect(() => {
    let active = true;
    api<PromptRecord[]>("/api/prompts")
      .then((data) => { if (active) setPrompts(data); })
      .catch((err) => { if (active) setError(err instanceof Error ? err.message : "Could not load prompts."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const filtered = useMemo(() => prompts.filter((prompt) =>
    (!search || prompt.name.toLowerCase().includes(search.toLowerCase())) &&
    (!category || prompt.category === category) && (!status || prompt.status === status)
  ), [prompts, search, category, status]);

  async function save() {
    if (!editing?.name?.trim() || !editing.content?.trim()) return;
    if (editing.id) {
      await api(`/api/prompts/${editing.id}`, { method: "PATCH", body: JSON.stringify(editing) });
    } else {
      await api("/api/prompts", { method: "POST", body: JSON.stringify(editing) });
    }
    setEditing(null); await load();
  }

  async function duplicate(prompt: PromptRecord) {
    await api(`/api/prompts/${prompt.id}/duplicate`, { method: "POST" }); await load();
  }

  async function remove(prompt: PromptRecord) {
    if (!window.confirm(`Delete “${prompt.name}”? This cannot be undone.`)) return;
    await api(`/api/prompts/${prompt.id}`, { method: "DELETE" }); await load();
  }

  async function runTest() {
    if (!testing || !testInput.trim()) return;
    setTestResult("Running…");
    try {
      const result = await api<{ model_output: string; passed: boolean }>(`/api/prompts/${testing.id}/test`, {
        method: "POST", body: JSON.stringify({ test_input: testInput }),
      });
      setTestResult(`${result.passed ? "PASS" : "FAIL"}\n\n${result.model_output}`);
    } catch (err) { setTestResult(err instanceof Error ? err.message : "Test failed."); }
  }

  return (
    <section className="library-panel">
      <div className="table-toolbar">
        <label className="search-field"><Search size={17} /><span className="sr-only">Search prompts</span>
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search prompts" />
        </label>
        <select aria-label="Filter by category" value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {["Landing Page", "Website", "Web Application", "Agent Workflow", "Other"].map((item) => <option key={item}>{item}</option>)}
        </select>
        <select aria-label="Filter by status" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option><option>Draft</option><option>Tested</option><option>Approved</option>
        </select>
        <button className="primary-button" onClick={() => setEditing({ ...emptyPrompt })}><Plus size={17} /> New prompt</button>
      </div>

      {loading && <div className="table-state"><LoaderCircle className="spin" /> Loading prompt library…</div>}
      {error && <div className="error-banner" role="alert">{error}</div>}
      {!loading && !error && filtered.length === 0 && (
        <div className="empty-state"><span>∅</span><h2>No prompts found</h2><p>Generate one with the agent or create your first contract here.</p></div>
      )}
      {filtered.length > 0 && (
        <div className="table-scroll"><table>
          <thead><tr><th>Name</th><th>Category</th><th>Version</th><th>Model</th><th>Status</th><th>Updated</th><th><span className="sr-only">Actions</span></th></tr></thead>
          <tbody>{filtered.map((prompt) => <tr key={prompt.id}>
            <td><button className="prompt-name" onClick={() => setEditing(prompt)}>{prompt.name}</button></td>
            <td>{prompt.category}</td><td className="mono">{prompt.version}</td><td className="model-cell">{prompt.model_id || "—"}</td>
            <td><span className={`status status-${prompt.status.toLowerCase()}`}>{prompt.status}</span></td>
            <td>{new Date(prompt.updated_at).toLocaleDateString()}</td>
            <td><div className="row-actions">
              <button aria-label={`Edit ${prompt.name}`} onClick={() => setEditing(prompt)}><Pencil size={15} /></button>
              <button aria-label={`Duplicate ${prompt.name}`} onClick={() => duplicate(prompt)}><Copy size={15} /></button>
              <button aria-label={`Test ${prompt.name}`} onClick={() => { setTesting(prompt); setTestInput(""); setTestResult(""); }}><FlaskConical size={15} /></button>
              <button aria-label={`Delete ${prompt.name}`} onClick={() => remove(prompt)}><Trash2 size={15} /></button>
            </div></td>
          </tr>)}</tbody>
        </table></div>
      )}

      {editing && <div className="modal-backdrop" role="presentation"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="editor-title">
        <header><div><p className="eyebrow"><span /> Prompt contract</p><h2 id="editor-title">{editing.id ? "Edit prompt" : "Create prompt"}</h2></div><button aria-label="Close editor" onClick={() => setEditing(null)}><X /></button></header>
        <div className="form-grid">
          <label>Name<input value={editing.name || ""} onChange={(e) => setEditing({ ...editing, name: e.target.value })} /></label>
          <label>Category<select value={editing.category || "Other"} onChange={(e) => setEditing({ ...editing, category: e.target.value })}>{["Landing Page", "Website", "Web Application", "Agent Workflow", "Other"].map((item) => <option key={item}>{item}</option>)}</select></label>
          <label>Status<select value={editing.status || "Draft"} onChange={(e) => setEditing({ ...editing, status: e.target.value })}><option>Draft</option><option>Tested</option><option>Approved</option></select></label>
          <label className="full">Prompt<textarea rows={18} value={editing.content || ""} onChange={(e) => setEditing({ ...editing, content: e.target.value })} /></label>
        </div>
        <footer><button className="secondary-button" onClick={() => setEditing(null)}>Cancel</button><button className="primary-button" onClick={save}>Save prompt</button></footer>
      </section></div>}

      {testing && <div className="modal-backdrop" role="presentation"><section className="modal compact-modal" role="dialog" aria-modal="true" aria-labelledby="test-title">
        <header><div><p className="eyebrow"><span /> Regression test</p><h2 id="test-title">Test {testing.name}</h2></div><button aria-label="Close test" onClick={() => setTesting(null)}><X /></button></header>
        <label>Test input<textarea rows={5} value={testInput} onChange={(e) => setTestInput(e.target.value)} placeholder="Enter a realistic input this prompt must handle…" /></label>
        {testResult && <pre className="test-result">{testResult}</pre>}
        <footer><button className="secondary-button" onClick={() => setTesting(null)}>Close</button><button className="primary-button" onClick={runTest}><FlaskConical size={16} /> Run test</button></footer>
      </section></div>}
    </section>
  );
}
