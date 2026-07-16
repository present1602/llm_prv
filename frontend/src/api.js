// 백엔드 API 래퍼. 모든 요청은 /api 프록시(로컬 백엔드)로만 나간다.

async function req(path, opts = {}) {
  const res = await fetch(`/api${path}`, opts)
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`${res.status}: ${text || res.statusText}`)
  }
  return res
}

export async function getHealth() {
  return (await req('/health')).json()
}

export async function getSections() {
  return (await req('/sections')).json()
}

export async function parsePdf(file) {
  const fd = new FormData()
  fd.append('file', file)
  return (await req('/parse', { method: 'POST', body: fd })).json()
}

export async function generate(invention, sections) {
  return (
    await req('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ invention, sections }),
    })
  ).json()
}

export async function regenerate(invention, section, generated, extra) {
  return (
    await req('/regenerate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        invention,
        section,
        generated,
        extra_instruction: extra || null,
      }),
    })
  ).json()
}

export async function exportDoc(kind, generated) {
  const res = await req(`/export/${kind}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ generated }),
  })
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = kind === 'docx' ? 'specification.docx' : 'specification.md'
  a.click()
  URL.revokeObjectURL(url)
}
