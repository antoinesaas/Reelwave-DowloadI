import { useState, useCallback, useEffect, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

import ParticleSphere  from './components/ParticleSphere'
import PastePanel      from './components/PastePanel'
import QualityBubbles  from './components/QualityBubbles'
import DownloadCard    from './components/DownloadCard'
import HistoryPanel, { useHistory } from './components/HistoryPanel'
import CustomCursor    from './components/CustomCursor'
import { useDownload } from './hooks/useDownload'

// App phases: 'hero' | 'input' | 'quality' | 'downloading' | 'done'
// Sphere state: 'idle' | 'exploding' | 'ring' | 'logo'

export default function App() {
  const [phase, setPhase]           = useState('hero')
  const [sphereState, setSphereState] = useState('idle')
  const [isLogoMode, setIsLogoMode] = useState(false)
  const [currentUrl, setCurrentUrl]  = useState('')
  const [selectedQuality, setSelectedQuality] = useState('1080p')
  const [videoInfo, setVideoInfo]    = useState(null)
  const [showHistory, setShowHistory] = useState(false)
  const [infoLoading, setInfoLoading] = useState(false)
  const [backendError, setBackendError] = useState('')

  const { job, fetchInfo, startDownload, cancel, reset } = useDownload()
  const { history, add: addHistory, clear: clearHistory } = useHistory()

  // ── Sphere click → implode → explode → ring → logo ──────────────────────────
  const handleSphereClick = useCallback(() => {
    if (phase !== 'hero') return

    setSphereState('imploding')
    setTimeout(() => setSphereState('exploding'), 160)
    setTimeout(() => setSphereState('ring'),      340)
    setTimeout(() => {
      setSphereState('logo')
      setIsLogoMode(true)
      setPhase('input')
    }, 480)
  }, [phase])

  // ── URL submitted from PastePanel ────────────────────────────────────────────
  const handleValidUrl = useCallback(async (url) => {
    setCurrentUrl(url)
    setInfoLoading(true)
    setBackendError('')
    setPhase('quality')

    try {
      const info = await fetchInfo(url)
      setVideoInfo(info)
    } catch (e) {
      setBackendError(e.message || 'Impossible de récupérer les infos.')
    } finally {
      setInfoLoading(false)
    }
  }, [fetchInfo])

  // ── Quality selected + download triggered ────────────────────────────────────
  const handleQualitySelect = useCallback((q) => {
    setSelectedQuality(q)
  }, [])

  const handleDownload = useCallback(async () => {
    setBackendError('')
    setPhase('downloading')
    try {
      await startDownload(currentUrl, selectedQuality)
    } catch (err) {
      const isNetErr = !err.response
      setBackendError(
        isNetErr
          ? 'Serveur non disponible. Déploie le backend pour activer les téléchargements.'
          : (err.response?.data?.detail || 'Erreur lors du démarrage.')
      )
      setPhase('quality')
    }
  }, [currentUrl, selectedQuality, startDownload])

  // ── When download completes, add to history ──────────────────────────────────
  useEffect(() => {
    if (job?.status === 'done') {
      addHistory({
        jobId:     job.jobId,
        url:       job.url,
        title:     job.title,
        thumbnail: job.thumbnail,
        platform:  videoInfo?.platform || 'Web',
        quality:   job.quality,
        filename:  job.filename,
        date:      new Date().toISOString(),
      })
      setPhase('done')
    }
  }, [job?.status, job?.jobId])

  // ── Re-download from history ─────────────────────────────────────────────────
  const handleRedownload = useCallback((entry) => {
    setShowHistory(false)
    setCurrentUrl(entry.url)
    setSelectedQuality(entry.quality)
    setPhase('quality')
    setIsLogoMode(true)
    setSphereState('logo')
  }, [])

  // ── Reset everything ─────────────────────────────────────────────────────────
  const handleReset = useCallback(() => {
    reset()
    setPhase('input')
    setCurrentUrl('')
    setVideoInfo(null)
  }, [reset])

  return (
    <div className="w-full h-full bg-rw-bg relative overflow-hidden select-none">
      {/* Custom cursor — desktop only */}
      <div className="hidden md:block"><CustomCursor /></div>

      {/* ── Particle sphere (always mounted) ── */}
      <ParticleSphere
        sphereState={sphereState}
        onSphereClick={handleSphereClick}
        isLogoMode={isLogoMode}
      />

      {/* ── Overlay content ── */}
      <AnimatePresence mode="wait">

        {/* HERO phase: tap hint */}
        {phase === 'hero' && (
          <motion.div
            key="hero-hint"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ delay: 1.2 }}
            className="fixed bottom-8 left-0 right-0 flex justify-center pointer-events-none"
          >
            <motion.p
              animate={{ y: [0, -5, 0] }}
              transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
              className="text-rw-muted text-xs md:text-sm font-light tracking-widest"
            >
              <span className="md:hidden">↑ appuyer pour commencer</span>
              <span className="hidden md:inline">↑ cliquer pour commencer</span>
            </motion.p>
          </motion.div>
        )}

        {/* INPUT phase: URL paste panel */}
        {phase === 'input' && (
          <motion.div
            key="input-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-x-0 bottom-0 md:inset-0 flex items-end md:items-center
                       justify-center px-3 pb-6 md:pb-0 pointer-events-none z-20"
          >
            <div className="pointer-events-auto w-full max-w-md">
              <PastePanel
                onValidUrl={handleValidUrl}
                onClose={() => { setPhase('hero'); setIsLogoMode(false); setSphereState('idle') }}
              />
            </div>
          </motion.div>
        )}

        {/* QUALITY phase */}
        {phase === 'quality' && (
          <motion.div
            key="quality-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-20 flex flex-col items-center justify-center
                       px-4 gap-4 overflow-y-auto"
          >
            {/* Video preview card */}
            {(videoInfo || infoLoading) && (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card rounded-2xl p-3 flex items-center gap-3 w-full max-w-xs shrink-0"
              >
                {infoLoading ? (
                  <div className="w-10 h-10 rounded-lg bg-white/10 animate-pulse shrink-0" />
                ) : (
                  <img src={videoInfo.thumbnail} alt=""
                    className="w-10 h-10 rounded-lg object-cover shrink-0" />
                )}
                <div className="min-w-0">
                  <p className="text-rw-ink text-xs font-semibold truncate">
                    {infoLoading ? '…' : videoInfo?.title || currentUrl.substring(0, 40)}
                  </p>
                  <p className="text-rw-muted text-[10px] mt-0.5">
                    {infoLoading ? '…' : videoInfo?.platform || ''}
                  </p>
                </div>
              </motion.div>
            )}

            <QualityBubbles onSelect={handleQualitySelect} initialQuality={selectedQuality} />

            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              onClick={handleDownload}
              whileTap={{ scale: 0.97 }}
              className="bg-rw-ink text-rw-bg w-full max-w-xs py-4 rounded-2xl
                         text-[15px] font-semibold tracking-wide shrink-0
                         active:scale-[0.98] transition-all duration-200"
            >
              Télécharger →
            </motion.button>

            {backendError && (
              <p className="text-rw-error text-xs text-center max-w-[280px] leading-relaxed">
                ⚠ {backendError}
              </p>
            )}

            <button
              onClick={() => { setPhase('input'); setBackendError(''); setVideoInfo(null) }}
              className="text-sm text-rw-muted py-2 px-4"
            >
              ← changer le lien
            </button>
          </motion.div>
        )}

        {/* DOWNLOADING / DONE phase: progress card */}
        {(phase === 'downloading' || phase === 'done') && job && (
          <motion.div
            key="download-card-wrapper"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0  }}
            className="fixed bottom-4 left-3 right-3 md:left-auto md:right-8
                       md:bottom-8 md:w-80 pointer-events-auto z-40"
          >
            <DownloadCard
              job={job}
              onCancel={() => { cancel(); handleReset() }}
            />

            {phase === 'done' && (
              <motion.button
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                onClick={handleReset}
                className="mt-2 w-full text-center text-xs text-rw-muted hover:text-rw-ink
                           transition-colors py-2"
              >
                + Nouveau téléchargement
              </motion.button>
            )}
          </motion.div>
        )}

      </AnimatePresence>

      {/* ── History toggle (bottom-right when not in progress) ─────────────────── */}
      {phase !== 'downloading' && !showHistory && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          onClick={() => setShowHistory(true)}
          className="fixed bottom-6 right-6 text-xs text-rw-muted/50
                     hover:text-rw-muted transition-colors z-30"
        >
          Historique {history.length > 0 && `(${history.length})`}
        </motion.button>
      )}

      {/* ── History panel ────────────────────────────────────────────────────────── */}
      <AnimatePresence>
        {showHistory && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/10 z-40"
              onClick={() => setShowHistory(false)}
            />
            <HistoryPanel
              history={history}
              onClear={clearHistory}
              onClose={() => setShowHistory(false)}
              onRedownload={handleRedownload}
            />
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
