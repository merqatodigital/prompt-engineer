import { PromptTable } from "@/components/prompt-table";

export default function PromptsPage() {
  return (
    <main className="page-shell">
      <header className="page-heading">
        <div>
          <p className="eyebrow"><span /> Working library</p>
          <h1>Your prompt contracts</h1>
        </div>
        <p>Version, test, and improve prompts without losing the outcome they were designed to produce.</p>
      </header>
      <PromptTable />
    </main>
  );
}

