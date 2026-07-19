import { useEffect, useState } from 'react'
import {
  getHealth,
  getSections,
  parsePdf,
  generate,
  regenerate,
  exportDoc,
} from './api'
import './App.css'

const FIELDS = [
  { key: 'title_hint', label: '발명 제목/주제', placeholder: '예: 자동 접이식 스마트 우산' },
  { key: 'description', label: '발명 설명 (핵심)', textarea: true, placeholder: '발명의 내용을 자유롭게 서술하세요.' },
  { key: 'problem', label: '해결하려는 문제', textarea: true },
  { key: 'key_features', label: '핵심 아이디어/특징', textarea: true },
  { key: 'background', label: '배경/종래기술', textarea: true },
]

export default function App() {
  const [health, setHealth] = useState(null)
  const [sections, setSections] = useState([])
  const [invention, setInvention] = useState({})
  const [refText, setRefText] = useState('')
  const [generated, setGenerated] = useState({})
  const [busy, setBusy] = useState(null) // null | 'all' | section key
  const [error, setError] = useState('')

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth({ service: 'down' }))
    getSections().then(setSections).catch(() => {})
  }, [])

  const payload = () => ({ ...invention, reference_text: refText || null })

  function update(key, value) {
    setInvention((prev) => ({ ...prev, [key]: value }))
  }

  async function handleUpload(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setError('')
    try {
      const r = await parsePdf(file)
      setRefText((prev) => (prev ? prev + '\n\n' : '') + `[${r.filename}]\n${r.text}`)
    } catch (err) {
      setError(`PDF 파싱 실패: ${err.message}`)
    }
    e.target.value = ''
  }

  async function handleGenerate() {
    setError('')
    setBusy('all')
    try {
      const r = await generate(payload(), null)
      setGenerated(r.generated)
    } catch (err) {
      setError(`생성 실패: ${err.message}`)
    } finally {
      setBusy(null)
    }
  }

  async function handleRegenerate(key) {
    setError('')
    const extra = window.prompt('이 섹션에 대한 추가 요청 (선택, 비워도 됨):') ?? ''
    setBusy(key)
    try {
      const r = await regenerate(payload(), key, generated, extra)
      setGenerated((prev) => ({ ...prev, [key]: r.text }))
    } catch (err) {
      setError(`재생성 실패: ${err.message}`)
    } finally {
      setBusy(null)
    }
  }

  const llmReady = health?.llm?.model_ready
  const hasOutput = Object.keys(generated).length > 0

  return (
    <div className="app">
      <header>
        <h1>특허 명세서 초안 생성기 <span className="tag">폐쇄형 MVP</span></h1>
        <div className={`llm-status ${llmReady ? 'ok' : 'warn'}`}>
          {health == null
            ? 'LLM 상태 확인 중…'
            : llmReady
            ? `LLM 준비됨: ${health.llm.configured_model}`
            : `LLM 미연결 (${health?.llm?.configured_model ?? '?'}) — Ollama 실행/모델 pull 필요`}
        </div>
      </header>

      {error && <div className="error">{error}</div>}

      <div className="layout">
        <section className="panel input-panel">
          <h2>발명 정보 입력</h2>
          {FIELDS.map((f) => (
            <label key={f.key} className="field">
              <span>{f.label}</span>
              {f.textarea ? (
                <textarea
                  rows={3}
                  placeholder={f.placeholder || ''}
                  value={invention[f.key] || ''}
                  onChange={(e) => update(f.key, e.target.value)}
                />
              ) : (
                <input
                  placeholder={f.placeholder || ''}
                  value={invention[f.key] || ''}
                  onChange={(e) => update(f.key, e.target.value)}
                />
              )}
            </label>
          ))}

          <label className="field">
            <span>참고 문서 (PDF 업로드 → 텍스트 추출)</span>
            <input type="file" accept="application/pdf" onChange={handleUpload} />
          </label>
          {refText && (
            <details className="ref">
              <summary>추출된 참고 텍스트 ({refText.length}자)</summary>
              <pre>{refText}</pre>
            </details>
          )}

          <button
            className="primary"
            onClick={handleGenerate}
            disabled={busy != null || !invention.description}
          >
            {busy === 'all' ? '명세서 생성 중… (수십 초 소요)' : '명세서 초안 생성'}
          </button>
          {!invention.description && <p className="hint">‘발명 설명’은 필수입니다.</p>}
        </section>
          
        <section className="panel output-panel">
          <div className="output-header">
            <h2>명세서 초안</h2>
            {hasOutput && (
              <div className="export">
                <button onClick={() => exportDoc('markdown', generated)}>Markdown</button>
                <button onClick={() => exportDoc('docx', generated)}>DOCX</button>
              </div>
            )}
          </div>

          {!hasOutput && <p className="hint">아직 생성된 초안이 없습니다.</p>}

          {sections.map((s) =>
            generated[s.key] != null ? (
              <div className="section" key={s.key}>
                <div className="section-head">
                  <h3>{s.title}</h3>
                  <button
                    className="ghost"
                    onClick={() => handleRegenerate(s.key)}
                    disabled={busy != null}
                  >
                    {busy === s.key ? '재생성 중…' : '재생성'}
                  </button>
                </div>
                <textarea
                  className="section-body"
                  rows={Math.max(3, (generated[s.key] || '').split('\n').length + 1)}
                  value={generated[s.key]}
                  onChange={(e) =>
                    setGenerated((prev) => ({ ...prev, [s.key]: e.target.value }))
                  }
                />
              </div>
            ) : null
          )}
        </section>
      </div>
      <footer>
        초안은 변리사·발명자의 검토·수정을 전제로 합니다. 모든 처리는 로컬에서만 수행됩니다.
      </footer>
    </div>
  )
}
