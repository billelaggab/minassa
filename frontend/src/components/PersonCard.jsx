import { Link } from 'react-router-dom'

const SENS = { public: 'عام', confidential: 'سرّي', top_secret: 'سرّي للغاية' }

export default function PersonCard({ p, onDelete }) {
  return (
    <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4 shadow">
      <div className="flex items-start justify-between gap-2">
        <div>
          <Link to={'/person/' + p.id} className="text-lg font-bold text-emerald-300 hover:underline">
            {p.full_name}
          </Link>
          {p.aliases && <div className="mt-1 text-xs text-neutral-400">كنيات: {p.aliases}</div>}
          <div className="mt-2 flex flex-wrap gap-1 text-[11px]">
            <span className="rounded bg-neutral-800 px-2 py-0.5">الموثوقية {p.reliability}/5</span>
            <span className="rounded bg-red-950 px-2 py-0.5 text-red-200">{SENS[p.sensitivity] || p.sensitivity}</span>
            {p.nationality && <span className="rounded bg-neutral-800 px-2 py-0.5">{p.nationality}</span>}
            {p.occupation && <span className="rounded bg-neutral-800 px-2 py-0.5">{p.occupation}</span>}
          </div>
        </div>
        <button onClick={() => onDelete && onDelete(p)} className="no-print rounded-lg border border-red-900 px-2 py-1 text-xs text-red-300 hover:bg-red-950">
          حذف
        </button>
      </div>
    </div>
  )
}
