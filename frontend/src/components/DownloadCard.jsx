import { motion } from 'framer-motion'

export default function DownloadCard({ job, onCancel }) {
  if (!job) return null

  const isDone    = job.status === 'done'
  const isError   = job.status === 'error'
  const isLoading = job.status === 'loading'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.96 }}
      animate={{ opacity: 1, y: 0,  scale: 1    }}
      exit={{    opacity: 0, y: 20, scale: 0.96 }}
      transition={{ type: 'spring', stiffness: 260, damping: 28 }}
      className="glass-card rounded-[20px] p-4 w-full"
      style={{
        border: isDone  ? '1.5px solid rgba(52,211,153,0.35)'
              : isError ? '1.5px solid rgba(248,113,113,0.35)'
              : '1px solid rgba(255,255,255,0.10)',
        boxShadow: isDone  ? '0 0 32px rgba(52,211,153,0.10)'
                 : isError ? '0 0 32px rgba(248,113,113,0.10)'
                 : '0 8px 40px rgba(0,0,0,0.4)',
      }}
    >
      <div className="flex items-center gap-3">
        {/* Thumbnail or spinner */}
        {job.thumbnail ? (
          <img
            src={job.thumbnail}
            alt=""
            className="w-12 h-12 rounded-[8px] object-cover shrink-0"
          />
        ) : (
          <div className={`w-12 h-12 rounded-[8px] shrink-0 flex items-center justify-center
                          bg-white/08 border border-rw-border
                          ${isLoading ? 'animate-pulse' : ''}`}
          >
            {isLoading && (
              <div className="w-5 h-5 rounded-full border-2 border-rw-muted border-t-rw-ink animate-spin" />
            )}
          </div>
        )}

        <div className="flex-1 min-w-0">
          <p className="text-rw-ink text-[13px] font-semibold leading-tight truncate">
            {job.title || (isLoading ? 'Récupération en cours…' : job.url?.substring(0, 45))}
          </p>
          <p className="text-rw-muted text-[11px] mt-0.5">
            {isDone  ? '✓ Téléchargement déclenché'
           : isError ? `⚠ ${job.error}`
           : isLoading ? 'Extraction de l\'URL…'
           : ''}
          </p>
        </div>

        {/* Status icon */}
        {isDone && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 400, damping: 20 }}
            className="text-rw-success text-xl shrink-0"
          >✓</motion.span>
        )}
        {isError && <span className="text-rw-error text-xl shrink-0">✕</span>}

        {/* Cancel */}
        {isLoading && (
          <button
            onClick={onCancel}
            className="text-[11px] text-rw-muted/60 hover:text-rw-ink transition-colors shrink-0"
          >
            Annuler
          </button>
        )}
      </div>
    </motion.div>
  )
}
