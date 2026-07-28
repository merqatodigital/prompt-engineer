import { ModelSettings } from "@/components/model-settings";

export default function ModelsPage() {
  return (
    <main className="page-shell narrow-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow"><span /> Administrator</p>
          <h1>Model settings</h1>
        </div>
        <p>Choose OpenRouter or a local Ollama model. Credentials remain on the backend.</p>
      </header>
      <ModelSettings />
    </main>
  );
}

