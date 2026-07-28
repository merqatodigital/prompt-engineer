import { AgentChat } from "@/components/agent-chat";

export default function HomePage() {
  return (
    <main className="home-shell">
      <section className="hero-copy" aria-labelledby="page-title">
        <p className="eyebrow"><span /> Outcome-first prompt design</p>
        <h1 id="page-title">Turn rough ideas into prompts that <em>work.</em></h1>
        <p className="hero-summary">
          Describe the result you need. The agent turns it into a precise, testable contract for modern websites, applications, and agent workflows.
        </p>
        <div className="quality-note">
          <strong>No generic templates.</strong>
          <span>Every web prompt includes a brand-specific creative contract and visual quality checks.</span>
        </div>
      </section>
      <AgentChat />
    </main>
  );
}

