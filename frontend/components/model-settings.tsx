"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Cloud, Cpu, LoaderCircle, RefreshCw, ShieldCheck } from "lucide-react";
import { api, ModelSettings as ModelSettingsType } from "@/lib/api";

type OpenRouterModel = { id: string; name: string; context_length?: number; is_free: boolean; pricing?: Record<string, string> };
type OllamaModel = { name?: string; model?: string; size?: number; details?: { family?: string; parameter_size?: string; quantization_level?: string } };

export function ModelSettings() {
  const [password, setPassword] = useState(() => typeof window === "undefined" ? "" : sessionStorage.getItem("prompt-engineer-admin") || "");
  const [settings, setSettings] = useState<ModelSettingsType | null>(null);
  const [provider, setProvider] = useState<"openrouter" | "ollama">("openrouter");
  const [apiKey, setApiKey] = useState("");
  const [models, setModels] = useState<OpenRouterModel[]>([]);
  const [freeOnly, setFreeOnly] = useState(false);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState("openrouter/free");
  const [ollamaUrl, setOllamaUrl] = useState("http://localhost:11434");
  const [ollamaModels, setOllamaModels] = useState<OllamaModel[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api<ModelSettingsType>("/api/settings/model").then((data) => {
      setSettings(data); if (data.provider === "ollama") setProvider("ollama");
      if (data.model_id) setSelected(data.model_id); if (data.ollama_base_url) setOllamaUrl(data.ollama_base_url);
    }).catch(() => null);
  }, []);

  const visibleModels = useMemo(() => models.filter((model) =>
    (!freeOnly || model.is_free) && (!search || `${model.name} ${model.id}`.toLowerCase().includes(search.toLowerCase()))
  ), [models, freeOnly, search]);

  function rememberPassword(value: string) { setPassword(value); sessionStorage.setItem("prompt-engineer-admin", value); }
  function start() { setLoading(true); setError(""); setMessage(""); }
  function fail(err: unknown) { setError(err instanceof Error ? err.message : "The provider request failed."); setLoading(false); }

  async function connectOpenRouter() {
    start();
    try {
      const next = await api<ModelSettingsType>("/api/settings/openrouter", { method: "PUT", body: JSON.stringify({ api_key: apiKey || null, model_id: selected }) }, password);
      setSettings(next); setApiKey("");
      setModels(await api<OpenRouterModel[]>("/api/providers/openrouter/models", undefined, password));
      setMessage("OpenRouter connected. Select any available model below.");
    } catch (err) { fail(err); return; }
    setLoading(false);
  }

  async function saveOpenRouterModel() {
    start();
    try {
      const next = await api<ModelSettingsType>("/api/settings/openrouter", { method: "PUT", body: JSON.stringify({ model_id: selected }) }, password);
      setSettings(next); setMessage(`Active model changed to ${selected}.`);
    } catch (err) { fail(err); return; }
    setLoading(false);
  }

  async function detectOllama() {
    start();
    try {
      const data = await api<OllamaModel[]>(`/api/providers/ollama/models?base_url=${encodeURIComponent(ollamaUrl)}`, undefined, password);
      setOllamaModels(data); if (data[0]) setSelected(data[0].name || data[0].model || "");
      setMessage(data.length ? `Detected ${data.length} installed model${data.length === 1 ? "" : "s"}.` : "Ollama is running, but no models are installed.");
    } catch (err) { fail(err); return; }
    setLoading(false);
  }

  async function saveOllama() {
    start();
    try {
      const next = await api<ModelSettingsType>("/api/settings/ollama", { method: "PUT", body: JSON.stringify({ base_url: ollamaUrl, model_id: selected }) }, password);
      setSettings(next); setMessage(`Local model ${selected} is now active.`);
    } catch (err) { fail(err); return; }
    setLoading(false);
  }

  return <section className="settings-panel">
    <div className="active-model">
      <div className="active-icon"><CheckCircle2 /></div>
      <div><span>Active model</span><strong>{settings?.model_id || "Setup required"}</strong><small>{settings?.provider || "No provider connected"}</small></div>
    </div>
    <div className="admin-unlock">
      <ShieldCheck size={18} /><label>Administrator password<input type="password" value={password} onChange={(e) => rememberPassword(e.target.value)} placeholder="Required to change model settings" /></label>
    </div>
    <div className="provider-tabs" role="tablist" aria-label="Model provider">
      <button role="tab" aria-selected={provider === "openrouter"} onClick={() => setProvider("openrouter")}><Cloud /> OpenRouter<span>Hosted models</span></button>
      <button role="tab" aria-selected={provider === "ollama"} onClick={() => setProvider("ollama")}><Cpu /> Ollama<span>Your machine</span></button>
    </div>

    {provider === "openrouter" ? <div className="provider-form">
      <div className="form-section"><div><h2>Connect OpenRouter</h2><p>Use one key to access the live model catalog. The saved key is never returned to this browser.</p></div>
        <label>API key<input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder={settings?.has_api_key ? "Saved key available — leave blank to keep it" : "sk-or-v1-…"} /></label>
        <button className="primary-button" onClick={connectOpenRouter} disabled={!password || loading}>{loading ? <LoaderCircle className="spin" /> : <RefreshCw />} Connect and load models</button>
      </div>
      {models.length > 0 && <div className="model-picker">
        <div className="model-filter"><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search models" /><label><input type="checkbox" checked={freeOnly} onChange={(e) => setFreeOnly(e.target.checked)} /> Free only</label></div>
        <div className="model-list" role="radiogroup" aria-label="OpenRouter models">{visibleModels.map((model) => <label key={model.id} className={selected === model.id ? "selected" : ""}>
          <input type="radio" name="openrouter-model" value={model.id} checked={selected === model.id} onChange={() => setSelected(model.id)} />
          <span><strong>{model.name}</strong><small>{model.id}</small></span>{model.is_free ? <em>Free</em> : <em>{model.context_length ? `${Math.round(model.context_length / 1000)}K ctx` : "Paid"}</em>}
        </label>)}</div>
        <button className="primary-button align-right" onClick={saveOpenRouterModel} disabled={loading}>Use selected model</button>
      </div>}
    </div> : <div className="provider-form">
      <div className="form-section"><div><h2>Detect Ollama</h2><p>This works when the backend runs on the same computer or can reach the configured Ollama server.</p></div>
        <label>Ollama address<input value={ollamaUrl} onChange={(e) => setOllamaUrl(e.target.value)} /></label>
        <button className="primary-button" onClick={detectOllama} disabled={!password || loading}>{loading ? <LoaderCircle className="spin" /> : <RefreshCw />} Detect installed models</button>
      </div>
      {ollamaModels.length > 0 && <div className="model-picker"><div className="model-list">{ollamaModels.map((model) => { const id = model.name || model.model || ""; return <label key={id} className={selected === id ? "selected" : ""}>
        <input type="radio" name="ollama-model" checked={selected === id} onChange={() => setSelected(id)} /><span><strong>{id}</strong><small>{[model.details?.family, model.details?.parameter_size, model.details?.quantization_level].filter(Boolean).join(" · ")}</small></span><em>Local</em>
      </label>; })}</div><button className="primary-button align-right" onClick={saveOllama} disabled={loading}>Use selected model</button></div>}
    </div>}
    {message && <div className="success-banner" role="status">{message}</div>}
    {error && <div className="error-banner" role="alert">{error}</div>}
  </section>;
}
