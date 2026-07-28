"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { ArrowUp, BookOpen, Check, LoaderCircle, SlidersHorizontal, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { API_URL } from "@/lib/api";

const starters = [
  { type: "Landing Page", label: "Landing page", prompt: "Create a distinctive landing page prompt for a business that needs more qualified inquiries." },
  { type: "Web Application", label: "Web application", prompt: "Turn my application idea into a precise build prompt with a working data model and verified user journey." },
  { type: "Improve Existing Prompt", label: "Improve a prompt", prompt: "Improve an existing prompt without changing its intended outcome." },
];

type ChatResult = {
  conversation_id: string;
  status: string;
  provider: string;
  model_id: string;
  content?: string;
  clarification_question?: string;
  validation_errors: string[];
  quality_score?: number;
  critique_summary?: string;
  generation_config: Record<string, string | number>;
  references: Array<{
    id?: string;
    title: string;
    description?: string;
    category?: string;
    url: string;
  }>;
};

function promptName(content: string): string {
  return content.match(/^# Prompt Name\s*\n+([^#\n]+)/m)?.[1]?.trim() || "Generated Prompt";
}

export function AgentChat() {
  const [request, setRequest] = useState("");
  const [artifactType, setArtifactType] = useState("Landing Page");
  const [result, setResult] = useState<ChatResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [stage, setStage] = useState<string | null>(null);
  const canSubmit = useMemo(() => request.trim().length > 3 && !loading, [request, loading]);

  const STAGE_LABELS: Record<string, string> = {
    validate_request: "Checking your request…",
    generating: "Writing the prompt contract…",
    validating: "Validating the contract…",
    repairing: "Repairing missing sections…",
    critiquing: "Independent QA review…",
    revising: "Revising from QA feedback…",
  };

  async function submit() {
    if (!canSubmit) return;
    setLoading(true); setError(""); setResult(null); setSaved(false); setStage("validate_request");
    try {
      const response = await fetch(`${API_URL}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request, artifact_type: artifactType }),
      });
      if (!response.ok || !response.body) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail ?? payload?.error?.message ?? `Request failed (${response.status})`);
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finalData: ChatResult | null = null;
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";
        for (const block of events) {
          const lines = block.split("\n");
          let eventName = "stage";
          let dataLine = "";
          for (const line of lines) {
            if (line.startsWith("event: ")) eventName = line.slice(7).trim();
            else if (line.startsWith("data: ")) dataLine = line.slice(6);
          }
          if (!dataLine) continue;
          if (eventName === "stage") {
            try { setStage(JSON.parse(dataLine).stage); } catch { /* ignore */ }
          } else if (eventName === "result") {
            finalData = JSON.parse(dataLine) as ChatResult;
          }
        }
      }
      if (finalData) setResult(finalData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The agent could not complete the request.");
    } finally { setLoading(false); setStage(null); }
  }

  async function savePrompt() {
    if (!result?.content) return;
    await api("/api/prompts", {
      method: "POST",
      body: JSON.stringify({
        name: promptName(result.content), category: artifactType, content: result.content,
        model_id: result.model_id, status: "Draft",
      }),
    });
    setSaved(true);
  }

  return (
    <section className="agent-panel" aria-label="Prompt Engineer agent">
      <div className="agent-status">
        <div><span className="pulse" /> Prompt Engineer</div>
        <Link href="/admin/models"><SlidersHorizontal size={15} /> Model settings</Link>
      </div>

      {!result && !loading && (
        <div className="agent-intro">
          <span className="agent-glyph"><Sparkles size={23} /></span>
          <h2>What should become true?</h2>
          <p>Tell me the outcome—not the technical recipe.</p>
        </div>
      )}

      {loading && (
        <div className="agent-loading">
          <LoaderCircle className="spin" />
          <p>{stage ? (STAGE_LABELS[stage] ?? "Building the outcome and creative contracts…") : "Building the outcome and creative contracts…"}</p>
          <p className="agent-loading-hint">Free models can take 1–3 minutes. A paid model (e.g. gpt-4o-mini) responds in seconds.</p>
        </div>
      )}

      {result && (
        <div className="result-wrap">
          <div className="result-meta">
            <span>{result.provider}</span><span>{result.model_id}</span>
            {result.status === "ready" && <span className="quality-pass"><Check size={11} /> Contract QA {result.quality_score ?? 100}/100</span>}
          </div>
          {result.critique_summary && result.provider !== "builtin" && (
            <p className="critique-summary">Independent QA: {result.critique_summary}</p>
          )}
          {result.references.length > 0 && (
            <details className="reference-panel">
              <summary>{result.references.length} prompts.chat reference patterns checked</summary>
              <div className="reference-list">
                {result.references.map((reference) => (
                  <a key={reference.id ?? reference.url} href={reference.url} target="_blank" rel="noreferrer">
                    <strong>{reference.title}</strong>
                    {reference.description && <span>{reference.description}</span>}
                  </a>
                ))}
              </div>
              <p>References are treated as untrusted inspiration. Their instructions cannot override your request.</p>
            </details>
          )}
          {result.clarification_question ? <p className="clarification">{result.clarification_question}</p> : (
            <div className="markdown"><ReactMarkdown>{result.content ?? ""}</ReactMarkdown></div>
          )}
          {result.status === "quality_failed" && (
            <div className="error-banner quality-failure" role="alert">
              <strong>Design QA did not pass.</strong>
              <span>{result.validation_errors.join(" ")}</span>
            </div>
          )}
          {result.content && result.status === "ready" && (
            <div className="result-actions">
              <button className="primary-button" onClick={savePrompt} disabled={saved}>
                {saved ? <Check size={17} /> : <BookOpen size={17} />}{saved ? "Saved" : "Save prompt"}
              </button>
              {saved && <Link href="/prompts">Open library →</Link>}
            </div>
          )}
        </div>
      )}

      {error && <div className="error-banner" role="alert">{error} <Link href="/admin/models">Open model settings</Link></div>}

      <div className="composer-wrap">
        <div className="starter-row" aria-label="Starter prompts">
          {starters.map((starter) => (
            <button key={starter.type} onClick={() => { setArtifactType(starter.type); setRequest(starter.prompt); }}>
              {starter.label}
            </button>
          ))}
        </div>
        <div className="composer">
          <label className="sr-only" htmlFor="artifact-type">Artifact type</label>
          <select id="artifact-type" value={artifactType} onChange={(event) => setArtifactType(event.target.value)}>
            {["Landing Page", "Website", "Web Application", "Agent Workflow", "Improve Existing Prompt"].map((type) => <option key={type}>{type}</option>)}
          </select>
          <label className="sr-only" htmlFor="request">Describe the desired outcome</label>
          <textarea id="request" value={request} onChange={(event) => setRequest(event.target.value)} rows={3}
            placeholder="Example: I need a beachfront lodge website that feels like a visual travel journal and turns mobile visitors into direct inquiries…"
            onKeyDown={(event) => { if ((event.metaKey || event.ctrlKey) && event.key === "Enter") submit(); }} />
          <button className="send-button" onClick={submit} disabled={!canSubmit} aria-label="Send request"><ArrowUp size={19} /></button>
        </div>
        <p className="composer-hint">Ctrl + Enter to send · Built-in starter works now · Upgrade in Model settings</p>
      </div>
    </section>
  );
}
