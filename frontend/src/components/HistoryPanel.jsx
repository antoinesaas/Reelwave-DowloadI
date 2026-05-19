import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const PLATFORM_COLORS = {
  YouTube: '#FF0000', TikTok: '#000000', Instagram: '#E1306C',
  Pinterest: '#E60023', 'Twitter/X': '#000000', Vimeo: '#1AB7EA',
}

const LS_KEY = 'rw_history'

export function useHistory() {
  const [history, setHistory] = useState(() => {
    try { return JSON.parse(localStorage.getItem(LS_KEY) || '[]') }
    catch { return [] }
  })

  const add = (entry) => {
    setHistory((prev) => {
      const next = [entry, ...prev].slice(0, 200)
      localStorage.setItem(LS_KEY, JSON.stringify(next))
      return next
    })
  }

  const clear = () => {
    localStorage.removeItem(LS_KEY)
    setHistory([])
  }

  return { history, add, clear }
}

export default function HistoryPanel({ history, onClear, onClose, onRedownload }) {
  const isMobile = window.innerWidth < 768

  return (
    <AnimatePresence>
      <motion.div
        key="history-panel"
        initial={isMobile ? { y: '100%' } : { x: '100%' }}
        animate={isMobile ? { y: 0 }      : { x: 0      }}
        exit={isMobile   ? { y: '100%' } : { x: '100%' }}
        transition={{ type: 'spring', stiffness: 260, damping: 30 }}
        className={`fixed z-50 bg-white/95 backdrop-blur-xl
                    ${isMobile
                      ? 'bottom-0 left-0 right-0 rounded-t-[24px] max-h-[80vh]'
                      : 'top-0 right-0 h-full w-80'
                    } overflow-hidden flex flex-col`}
        style={{
          boxShadow: '-4px 0 40px rgba(0,0,0,0.10)',
          borderLeft: isMobile ? 'none' : '1px solid rgba(224,224,224,0.8)',
          borderTop: isMobile ? '1px solid rgba(224,224,224,0.8)' : 'none',
        }}
      >
        {/* Handle (mobile) */}
        {isMobile && (
          <div className="flex justify-center pt-3 pb-1">
            <div className="w-8 h-1 rounded-full bg-rw-border" />
          </div>
        )}

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-rw-border/50">
          <h2 className="text-base font-semibold text-rw-ink">Historique</h2>
          <div className="flex items-center gap-4">
            {history.length > 0 && (
              <button
                onClick={onClear}
                className="text-[12px] text-rw-muted hover:text-red-500 transition-colors"
              >
                Tout effacer
              </button>
            )}
            <button
              onClick={onClose}
              className="text-rw-muted hover:text-rw-ink transition-colors text-lg leading-none"
            >
              ×
            </button>
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {history.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 gap-2">
              <span className="text-3xl opacity-20">⌛</span>
              <p className="text-rw-muted text-sm">Aucun téléchargement</p>
            </div>
          ) : (
            <div className="p-3 flex flex-col gap-2">
              <AnimatePresence>
                {history.map((entry, i) => (
                  <motion.div
                    key={entry.jobId || i}
                    layout
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.96 }}
                    className="flex items-center gap-3 p-3 rounded-[12px]
                               hover:bg-rw-border/20 transition-colors cursor-pointer group"
                    onClick={() => onRedownload?.(entry)}
                  >
                    {entry.thumbnail ? (
                      <img
                        src={entry.thumbnail}
                        alt=""
                        className="w-11 h-11 rounded-[8px] object-cover shrink-0"
                      />
                    ) : (
                      <div className="w-11 h-11 rounded-[8px] bg-rw-border/40 shrink-0" />
                    )}

                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-medium text-rw-ink truncate">
                        {entry.title || 'Vidéo'}
                      </p>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span
                          className="w-1.5 h-1.5 rounded-full"
                          style={{ background: PLATFORM_COLORS[entry.platform] || '#6E6E73' }}
                        />
                        <span className="text-[10px] text-rw-muted font-mono">
                          {entry.platform} · {entry.quality}
                        </span>
                        {entry.date && (
                          <span className="text-[10px] text-rw-muted/60">
                            · {new Date(entry.date).toLocaleDateString('fr-FR')}
                          </span>
                        )}
                      </div>
                    </div>

                    <span className="text-rw-muted/40 group-hover:text-rw-muted transition-colors text-sm">
                      ↓
                    </span>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
