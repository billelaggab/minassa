import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, getToken, setToken } from '../api/client.js'
import SearchBar from '../components/SearchBar.jsx'
import PersonCard from '../components/PersonCard.jsx'

export default function Dashboard() {
  const [persons, setPersons] = useState([])
  const [token, setTok] = useState(getToken())
  const [form, setForm] = useState({ full_name: '', aliases: '', nationality: '', occupation: '', sensitivity: 'confidential' })
  const [err, setErr] = useState('')
  const nav = useNavigate()

  async function load() {
    try {
      setErr('')
      setPersons(await api.listPersons())
    } catch (e) {
      setErr(e.message)
    }
  }
  useEffect(() => {
    load()
  }, [])

  async function create(e) {
    e.preventDefault()
    try {
      await api.createPerson({ ...form, reliability: 3 })
      setForm({ full_name: '', aliases: '', nationality: '', occupation: '', sensitivity: 'confidential' })
      load()
    } catch (e2) {
      setErr(e2.message)
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-4">
      <header className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold">منظومة الاستقصاء</h1>
          <p className="text-xs text-neutral-400">تعمل محليا بالكامل — دون إنترنت — خط تجوَّل محلّي — وضع ليلي</p>
        </div>
        <SearchBar onPick={(id) => nav('/person/' + id)} />
      </header>

      <div className="no-print flex items-center gap-2 rounded-xl border border-neutral-800 bg-neutral-900 p-3">
        <label className="text-xs">رمز الدخول API:</label>
        <input
          type="password"
          value={token}
          onChange={(e) => setTok(e.target.value)}
          className="w-64 rounded-lg border border-neutral-700 bg-neutral-950 px-2 py-1 text-sm"
          placeholder="X-API-Token"
        />
        <button
          onClick={() => {
            setToken(token)
            load()
          }}
          className="rounded-lg bg-emerald-600 px-3 py-1 text-sm font-bold"
        >
          حفظ
        </button>
      </div>

      {err && <div className="rounded-xl border border-red-900 bg-red-950 p-3 text-sm text-red-200">{err}</div>}

      <form onSubmit={create} className="no-print grid gap-2 rounded-2xl border border-neutral-800 bg-neutral-900 p-4 md:grid-cols-5">
        <input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} placeholder="الاسم الكامل *" className="rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm" />
        <input value={form.aliases} onChange={(e) => setForm({ ...form, aliases: e.target.value })} placeholder="كنيات / أسماء مستعارة" className="rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm" />
        <input value={form.nationality} onChange={(e) => setForm({ ...form, nationality: e.target.value })} placeholder="الجنسية" className="rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm" />
        <input value={form.occupation} onChange={(e) => setForm({ ...form, occupation: e.target.value })} placeholder="المهنة / الغطاء" className="rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm" />
        <button className="rounded-lg bg-emerald-600 py-2 text-sm font-bold">+ ملف شخص جديد</button>
      </form>

      <div className="grid gap-3 md:grid-cols-2">
        {persons.map((p) => (
          <PersonCard
            key={p.id}
            p={p}
            onDelete={async (pp) => {
              if (!confirm('حذف ملف «' + pp.full_name + '» نهائيا؟')) return
              await api.deletePerson(pp.id)
              load()
            }}
          />
        ))}
      </div>
      {!persons.length && <p className="text-center text-sm text-neutral-500">لا توجد ملفات بعد — أنشئ أول ملف من النموذج أعلاه.</p>}

      <footer className="pt-6 text-center text-[11px] text-neutral-500">
        <Link to="/" className="underline">تحديث</Link> — البحث يتفهّم: أ=إ=آ، ة=ه، ى=ي ويتجاهل التشكيل.
      </footer>
    </div>
  )
}
