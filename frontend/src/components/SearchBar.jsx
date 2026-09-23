import { useState } from 'react'
import { api } from '../api/client.js'

// شريط البحث الموحّد في كل عرض — عربي، لحظي، متسامح مع الأخطاء
export default function SearchBar({ onPick }) {
  const [q, setQ] = useState('')
  const [hits, setHits] = useState([])
  const [engine, setEngine] = useState('')
  const [loading, setLoading] = useState(false)

  let timer = null
  async function run(v) {
    setQ(v)
    clearTimeout(timer)
    if (!v.trim()) {
      setHits([])
      return
    }
    timer = setTimeout(async () => {
      setLoading(true)
      try {
        const r = await api.search(v)
        setEngine(r.engine || '')
        if (r.hits) setHits(r.hits)
        else {
          const merged = [
            ...(r.persons || []).map((p) => ({ id: p.id, full_name: p.full_name, _kind: 'شخص' })),
            ...(r.phones || []).map((x) => ({ id: x.person_id, full_name: x.number, _kind: 'هاتف' })),
            ...(r.emails || []).map((x) => ({ id: x.person_id, full_name: x.email, _kind: 'بريد' })),
            ...(r.notes || []).map((x) => ({ id: x.person_id, full_name: x.title, _kind: 'ملاحظة' }))
          ]
          setHits(merged)
        }
      } catch {
        setHits([])
      } finally {
        setLoading(false)
      }
    }, 250)
  }

  return (
    <div className="relative w-full max-w-xl">
      <input
        value={q}
        onChange={(e) => run(e.target.value)}
        placeholder="بحث فوري: اسم، كنية، هاتف، بريد، نص ملاحظة… (أ=إ=آ، ة=ه، ى=ي)"
        className="w-full rounded-xl border border-neutral-700 bg-neutral-900 px-4 py-2.5 text-sm outline-none focus:border-emerald-500"
      />
      {loading && <div className="absolute left-3 top-3 text-xs text-neutral-400">جارٍ البحث…</div>}
      {hits.length > 0 && (
        <div className="absolute z-20 mt-1 max-h-80 w-full overflow-auto rounded-xl border border-neutral-700 bg-neutral-900 shadow-2xl">
          <div className="px-3 py-1 text-[11px] text-neutral-400">المحرك: {engine} — {hits.length} نتيجة</div>
          {hits.map((h, i) => (
            <button
              key={i}
              onClick={() => {
                onPick && onPick(h.id || h.person_id)
                setHits([])
              }}
              className="flex w-full items-center justify-between px-3 py-2 text-right text-sm hover:bg-neutral-800"
            >
              <span>{h.full_name || h.search_blob_raw?.slice(0, 60)}</span>
              {h._kind && <span className="rounded bg-neutral-700 px-2 py-0.5 text-[11px]">{h._kind}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
