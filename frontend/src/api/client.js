// عميل API موحّد — يمرّر التوكن عبر X-API-Token (يُخزّن محليا فقط)
const TOKEN_KEY = 'intel_api_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}
export function setToken(t) {
  localStorage.setItem(TOKEN_KEY, t)
}

async function req(path, opts = {}) {
  const res = await fetch(path, {
    ...opts,
    headers: {
      'X-API-Token': getToken(),
      ...(opts.headers || {})
    }
  })
  if (res.status === 401) throw new Error('رمز الدخول غير صالح — أدخله أعلى الصفحة')
  if (!res.ok) {
    const txt = await res.text()
    throw new Error(txt || ('خطأ ' + res.status))
  }
  const ct = res.headers.get('content-type') || ''
  return ct.includes('application/json') ? res.json() : res.text()
}

export const api = {
  listPersons: (q = '') => req('/api/persons' + (q ? '?q=' + encodeURIComponent(q) : '')),
  getPerson: (id) => req('/api/persons/' + id),
  createPerson: (data) =>
    req('/api/persons', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }),
  deletePerson: (id) => req('/api/persons/' + id, { method: 'DELETE' }),
  addNote: (id, data) =>
    req(`/api/persons/${id}/notes`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }),
  search: (q) => req('/api/search?q=' + encodeURIComponent(q)),
  relations: (id) => req('/api/relations/' + id),
  addRelation: (id, data) =>
    req('/api/relations/' + id, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }),
  uploadDocs: (id, files, description = '') => {
    const fd = new FormData()
    files.forEach((f) => fd.append('files', f))
    fd.append('description', description)
    return req(`/api/persons/${id}/documents`, { method: 'POST', body: fd })
  },
  fileUrl: (docId, inline = true) => `/files/${docId}?inline=${inline ? 'true' : 'false'}`,
  dossierPdfUrl: (id, o = {}) =>
    `/api/dossier/${id}/pdf?exclude_confidential=${o.excludeConf ? 'true' : 'false'}&exclude_media=${o.excludeMedia ? 'true' : 'false'}`
}
