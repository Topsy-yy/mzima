import React, { useState } from 'react';
import { useAuth } from '../auth/AuthContext';
import { extractObservation } from '../api';

export function Extract() {
  const { token } = useAuth();
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await extractObservation(text, token ?? '');
      setResult(response.extracted_fields ?? {});
    } catch (err) {
      const status = (err as { status?: number }).status;
      if (status === 503) {
        setError('AI extraction is not configured on the server yet.');
      } else {
        setError(err instanceof Error ? err.message : 'Extraction failed.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main id="main" className="section">
      <div className="max" style={{ maxWidth: 760, margin: '0 auto' }}>
        <p className="eyebrow peach-eyebrow">ASSISTIVE AI</p>
        <h1 className="display display-md" style={{ color: 'var(--emerald-800)', marginTop: 8 }}>Extract observation</h1>
        <p className="sub" style={{ margin: '12px auto 0' }}>
          The model proposes structured fields from clinic note text. Results always require human review.
        </p>

        <form onSubmit={handleSubmit} style={{ marginTop: 24, display: 'grid', gap: 12 }}>
          <label htmlFor="extract-text" className="field-label" style={{ fontWeight: 700 }}>Clinical note text</label>
          <textarea
            id="extract-text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={6}
            style={{
              width: '100%',
              padding: 12,
              borderRadius: 12,
              border: '1px solid var(--peach-300)',
              fontSize: 15,
              background: '#fff',
              color: 'var(--ink)',
            }}
          />
          <button type="submit" className="btn btn-primary" disabled={loading || !text.trim()} style={{ width: '100%' }}>
            {loading ? 'Extracting…' : 'Extract'}
          </button>
        </form>

        {error && (
          <p role="alert" style={{ color: '#B00020', marginTop: 16, fontWeight: 600 }}>{error}</p>
        )}

        {result && (
          <div className="card" style={{ marginTop: 20, padding: 20 }}>
            <strong style={{ color: 'var(--emerald-800)' }}>Extracted fields</strong>
            <pre style={{ marginTop: 12, whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: 13 }}>
              {JSON.stringify(result, null, 2)}
            </pre>
            <small style={{ color: 'var(--muted)', marginTop: 8, display: 'block' }}>
              requires_human_review: true — verify before use.
            </small>
          </div>
        )}
      </div>
    </main>
  );
}