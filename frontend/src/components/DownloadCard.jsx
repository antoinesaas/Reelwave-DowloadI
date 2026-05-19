import { motion, AnimatePresence } from 'framer-motion'

const PLATFORM_COLORS = {
  YouTube:   '#FF0000',
  TikTok:    '#000000',
  Instagram: '#E1306C',
  Pinterest: '#E60023',
  'Twitter/X': '#000000',
  Vimeo:     '#1AB7EA',
  Web:       '#6E6E73',
}

function ProgressRing({ percent, size = 40, stroke = 2.5 }) {
  const r   = (size - stroke) / 2
  const circ = 2 * Math.PI * r
  const off  = circ * (1 - percent / 100)
  return (
    <svg width={size} height={size} className="-rotate-90">
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#E0E0E0" strokeWidth={stroke} />
      <circle
        cx={size/2} cy={size/2} r={r} fill="none"
        stroke="#0A0A0A" strokeWidth={stroke}
        strokeDasharray={circ}
        strokeDashoffset={off}
        strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.3s ease' }}
      />
    </svg>
  )
}

export default function DownloadCard({ job, onCancel }) {
  if (!job) return null
  const isDone     = job.status === 'done'
  const isError    = job.status === 'error'
  const isProgress = job.status === 'downloading'
  const platformColor = PLATFORM_COLORS[job.platform] || '#6E6E73'

  return (
    <motion.div
      initial={{ opacity: 0, x: 60, scale: 0.96 }}
      animate={{ opacity: 1, x: 0,  scale: 1    }}
      exit={{    opacity: 0, x: 60, scale: 0.96 }}
      transition={{ type: 'spring', stiffness: 260, damping: 28 }}
      className="glass-card rounded-[20px] p-4 w-full max-w-sm"
      style={{
        border: isDone  ? '1.5px solid rgba(34,197,94,0.4)'
              : isError ? '1.5px solid rgba(239,68,68,0.4)'
              : '1px solid rgba(224,224,224,0.8)',
        boxShadow: isDone  ? '0 0 32px rgba(34,197,94,0.12)'
                 : isError ? '0 0 32px rgba(239,68,68,0.10)'
                 : '0 8px 40px rgba(0,0,0,0.08)',
      }}
    >
      {/* Top row */}
      <div className="flex items-start gap-3">
        {/* Thumbnail */}
        {job.thumbnail ? (
          <img
            src={job.thumbnail}
            alt=""
            className="w-14 h-14 rounded-[10px] object-cover shrink-0"
          />
        ) : (
          <div className="w-14 h-14 rounded-[10px] bg-rw-border/40 shrink-0 animate-pulse" />
        )}

        <div className="flex-1 min-w-0">
          {/* Platform badge */}
          <div className="flex items-center gap-1.5 mb-1">
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: platformColor }}
            />
            <span className="text-[10px] font-semibold text-rw-muted uppercase tracking-wider">
              {job.platform}
            </span>
            <span className="text-[10px] text-rw-muted/60 font-mono">· {job.quality}</span>
          </div>

          {/* Title */}
          <p className="text-rw-ink text-[13px] font-semibold leading-tight line-clamp-2">
            {job.title || job.url?.substring(0, 50) || 'Chargement…'}
          </p>
        </div>

        {/* Status icon */}
        <div className="shrink-0">
          {isDone && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 400, damping: 20 }}
              className="text-green-500 text-xl"
            >
              ✓
            </motion.span>
          )}
          {isError && <span className="text-red-500 text-xl">✕</span>}
          {isProgress && (
            <ProgressRing percent={job.percent || 0} />
          )}
        </div>
      </div>

      {/* Progress bar */}
      {!isDone && !isError && (
        <div className="mt-3 progress-bar-track h-[3px]">
          <div
            className="progress-bar-fill"
            style={{ width: `${job.percent || 0}%` }}
          />
        </div>
      )}

      {/* Stats row */}
      <div className="mt-2 flex items-center justify-between">
        <span className="font-mono text-[11px] text-rw-muted">
          {isDone  ? 'Téléchargé ✓'
         : isError ? job.error || 'Erreur'
         : [job.speed, job.eta && `ETA ${job.eta}`, job.percent != null && `${job.percent}%`]
             .filter(Boolean).join('  ·  ')
          }
        </span>

        {!isDone && !isError && (
          <button
            onClick={onCancel}
            className="text-[11px] text-rw-muted/60 hover:text-rw-ink transition-colors"
          >
            Annuler
          </button>
        )}

        {isDone && (
          <a
            href={`/api/file/${job.jobId}`}
            download={job.filename}
            className="text-[11px] text-rw-ink font-semibold hover:opacity-70 transition-opacity"
          >
            ↓ Enregistrer
          </a>
        )}
      </div>
    </motion.div>
  )
}
