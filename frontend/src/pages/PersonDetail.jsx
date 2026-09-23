import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client.js'
import Gallery from '../components/Gallery.jsx'

export default function PersonDetail() {
  const { id } = useParams()
  const [p, setP] = useState(null)
  const [rels, setRels] = useState([])
  const [err, setErr] = useState('')
  const [note, setNote] = useState({ title: '', content: '', category: 'meeting', is_confidential: false })
  const [showConf, setShowConf] = useState(false)
  const [dossierOpts, setDossierOpts] = useState({ excludeConf: false, excludeMedia: false })

  async function load() {
    try {
      setP(await api.getPerson(id))
      setRels(await api.relations(id))
    } catch (e) {
      setErr(e.message)
    }
  }
  useEffect(() => {
    load()
  }, [id])

  async function upload(e) {
    const files = Array.from(e.target.files || [])
    if (!files.length) return
    // سحب وإفلات + اختيار متعدد
    await api.uploadDocs(id, files, '')
    e.target.value = ''
    load()
  }

  if (err) return <div className="p-6 text-red-300">{err} — <Link to="/" className="underline">عودة</Link></div>
  if (!p) return <div className="p-6">جارٍ التحميل…</div>

  const notes = (p.notes || []).filter((n) => showConf || !n.is_confidential)

  return (
    <div className="mx-auto max-w-5xl space-y-4 p-4">
      <Link to="/" className="no-print text-sm text-emerald-300 underline">→ عودة للوحة</Link>

      <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
        <h1 className="text-2xl font-bold">{p.full_name}</h1>
        {p.aliases && <div className="text-sm text-neutral-400">كنيات: {p.aliases}</div>}
        <div className="mt-2 grid gap-1 text-sm text-neutral-300 md:grid-cols-2">
          <div>الجنسية: {p.nationality || '—'}</div>
          <div>المهنة: {p.occupation || '—'}</div>
          <div>الميلاد: {p.date_of_birth || '—'}</div>
          <div>العنوان: {p.address || '—'}</div>
        </div>
        {p.summary && <p className="mt-3 rounded-xl bg-neutral-950 p-3 text-sm leading-7">{p.summary}</p>}

        <div className="mt-3 grid gap-2 text-sm md:grid-cols-3">
          <div className="rounded-xl border border-neutral-800 p-2">
            <b>هواتف</b>
            {(p.phones || []).map((x) => (
              <div key={x.id} dir="ltr" className="text-left text-xs">{x.number} <span className="text-neutral-400">({x.label})</span></div>
            ))}
          </div>
          <div className="rounded-xl border border-neutral-800 p-2">
            <b>بريد</b>
            {(p.emails || []).map((x) => (
              <div key={x.id} dir="ltr" className="text-left text-xs">{x.email}</div>
            ))}
          </div>
          <div className="rounded-xl border border-neutral-800 p-2">
            <b>تواصل</b>
            {(p.socials || []).map((x) => (
              <div key={x.id} className="text-xs">{x.platform}: <span dir="ltr">{x.handle}</span></div>
            ))}
          </div>
        </div>
      </div>

      {/* تصدير الدوسية */}
      <div className="no-print rounded-2xl border border-amber-900 bg-amber-950/30 p-4">
        <h2 className="font-bold text-amber-200">تصدير الدوسية الجنائية</h2>
        <div className="mt-2 flex flex-wrap items-center gap-3 text-sm">
          <label className="flex items-center gap-1">
            <input type="checkbox" checked={dossierOpts.excludeConf} onChange={(e) => setDossierOpts({ ...dossierOpts, excludeConf: e.target.checked })} />
            استبعاد الاستخبارات السرّية
          </label>
          <label className="flex items-center gap-1">
            <input type="checkbox" checked={dossierOpts.excludeMedia} onChange={(e) => setDossierOpts({ ...dossierOpts, excludeMedia: e.target.checked })} />
            استبعاد المرفقات
          </label>
          <a href={api.dossierPdfUrl(id, dossierOpts)} className="rounded-lg bg-amber-600 px-3 py-1.5 font-bold text-black">
            تنزيل PDF
          </a>
          <button onClick={() => window.print()} className="rounded-lg border border-amber-700 px-3 py-1.5">
            طباعة مباشرة
          </button>
        </div>
      </div>

      {/* الملاحظات */}
      <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
        <div className="flex items-center justify-between">
          <h2 className="font-bold">السجل الاستخباراتي</h2>
          <label className="no-print flex items-center gap-1 text-xs text-neutral-300">
            <input type="checkbox" checked={showConf} onChange={(e) => setShowConf(e.target.checked)} />
            إظهار السرّي (يتطلب تأكيدا واعيا)
          </label>
        </div>
        <form
          className="no-print mt-2 grid gap-2"
          onSubmit={async (e) => {
            e.preventDefault()
            if (note.is_confidential && !confirm('هذه الملاحظة سرّية — تأكيد الإضافة؟')) return
            await api.addNote(id, note)
            setNote({ title: '', content: '', category: 'meeting', is_confidential: false })
            load()
          }}
        >
          <input required value={note.title} onChange={(e) => setNote({ ...note, title: e.target.value })} placeholder="عنوان الملاحظة *" className="rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm" />
          <textarea value={note.content} onChange={(e) => setNote({ ...note, content: e.target.value })} placeholder="المحتوى (Markdown مدعوم)" rows="3" className="rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm" />
          <div className="flex gap-2 text-sm">
            <select value={note.category} onChange={(e) => setNote({ ...note, category: e.target.value })} className="rounded-lg bg-neutral-950 px-2 py-1">
              <option value="meeting">محضر لقاء</option>
              <option value="financial">مسار مالي</option>
              <option value="background">فحص خلفية</option>
              <option value="leak">تسرّب مصدر</option>
              <option value="other">أخرى</option>
            </select>
            <label className="flex items-center gap-1">
              <input type="checkbox" checked={note.is_confidential} onChange={(e) => setNote({ ...note, is_confidential: e.target.checked })} />
              سرّية
            </label>
            <button className="rounded-lg bg-emerald-600 px-3 py-1 font-bold">إضافة</button>
          </div>
        </form>
        <div className="mt-3 space-y-2">
          {notes.map((n) => (
            <div key={n.id} className={'note-card rounded-xl border p-3 text-sm ' + (n.is_confidential ? 'border-red-900 bg-red-950/20' : 'border-neutral-800 bg-neutral-950')}>
              <b>{n.title}</b> <span className="text-xs text-neutral-400">— {n.category} — {n.event_date || n.created_at}</span>
              {n.is_confidential && <span className="mr-2 rounded bg-red-900 px-1 text-[11px]">سرّي</span>}
              <div className="mt-1 whitespace-pre-wrap leading-7">{n.content}</div>
            </div>
          ))}
        </div>
      </div>

      {/* العلاقات */}
      <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
        <h2 className="font-bold">شبكة العلاقات</h2>
        <div className="mt-2 space-y-1 text-sm">
          {rels.map((r) => (
            <div key={r.id} className="flex justify-between rounded-lg bg-neutral-950 px-3 py-1.5">
              <Link to={'/person/' + r.other_id} className="text-emerald-300 underline">{r.other_name}</Link>
              <span className="text-neutral-400">{r.rel_type} — {r.confidence}</span>
            </div>
          ))}
          {!rels.length && <p className="text-xs text-neutral-500">لا علاقات مسجلة.</p>}
        </div>
      </div>

      {/* الملفات */}
      <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
        <h2 className="font-bold">الأدلة والمرفقات</h2>
        <label className="no-print mt-2 block cursor-pointer rounded-xl border border-dashed border-neutral-600 p-4 text-center text-sm text-neutral-300">
          اسحب وأفلت هنا أو انقر لاختيار ملفات (صور / PDF / مستندات)
          <input type="file" multiple className="hidden" onChange={upload} />
        </label>
        <div className="mt-3">
          <Gallery docs={p.documents} />
        </div>
        <div className="mt-2 space-y-1 text-xs">
          {(p.documents || []).map((d) => (
            <div key={d.id} className="flex items-center justify-between rounded-lg bg-neutral-950 px-2 py-1">
              <span>{d.original_name} <span className="text-neutral-500" dir="ltr">{d.sha256.slice(0, 16)}…</span></span>
              <a href={api.fileUrl(d.id)} target="_blank" rel="noreferrer" className="text-emerald-300 underline">معاينة / تنزيل</a>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
