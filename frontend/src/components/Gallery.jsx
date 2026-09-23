// معرض الصور مع Lightbox داخل صفحة الشخص
import { useState } from 'react'
import { api } from '../api/client.js'

export default function Gallery({ docs }) {
  const [active, setActive] = useState(null)
  const imgs = (docs || []).filter((d) => d.mime?.startsWith('image/'))
  if (!imgs.length) return <p className="text-sm text-neutral-400">لا توجد صور بعد.</p>
  return (
    <>
      <div className="grid grid-cols-3 gap-2 md:grid-cols-5">
        {imgs.map((d) => (
          <button key={d.id} onClick={() => setActive(d)} className="overflow-hidden rounded-lg border border-neutral-700">
            <img src={api.fileUrl(d.id)} alt={d.original_name} className="h-24 w-full object-cover" loading="lazy" />
          </button>
        ))}
      </div>
      {active && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4" onClick={() => setActive(null)}>
          <div className="max-h-full max-w-4xl">
            <img src={api.fileUrl(active.id)} alt={active.original_name} className="max-h-[85vh] rounded-lg" />
            <div className="mt-2 text-center text-sm text-neutral-300" dir="ltr">{active.sha256}</div>
          </div>
        </div>
      )}
    </>
  )
}
