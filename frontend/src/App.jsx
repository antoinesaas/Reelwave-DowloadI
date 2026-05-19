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

    // 1. Implode toward center (swallow the click)
    setSphereState('imploding')

    // 2. Burst outward
    setTimeout(() => setSphereState('exploding'), 320)

    // 3. Converge to ring
    setTimeout(() => setSphereState('ring'), 680)

    // 4. Particles fade away, logo CSS circle pops in, input appears
    setTimeout(() => {
      setSphereState('logo')
      setIsLogoMode(true)
      setPhase('input')
    }, 1100)
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
      const isNetErr = !e.response
      setBackendError(
        isNetErr
          ? 'Serveur non disponible. Le backend n\'est pas encore déployé.'
          : (e.response?.data?.detail || 'Impossible de récupérer les infos.')
      )
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
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="fixed inset-0 flex items-end md:items-center justify-center px-4 pointer-events-none z-20"
            style={{ paddingBottom: 32 }}
          >
            <div className="pointer-events-auto w-full max-w-lg">
              <PastePanel
                onValidUrl={handleValidUrl}
                onClose={() => { setPhase('hero'); setIsLogoMode(false); setSphereState('idle') }}
              />
            </div>
          </motion.div>
        )}

        {/* QUALITY phase: bubbles + download button */}
        {phase === 'quality' && (
          <motion.div
            key="quality-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 flex flex-col items-center justify-center gap-6 md:gap-8 px-4 z-20"
            style={{ paddingTop: 60 }}
          >
            {/* Video preview card */}
            {(videoInfo || infoLoading) && (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0  }}
                className="glass-card rounded-[16px] p-3 flex items-center gap-3
                           w-full max-w-sm"
              >
                {infoLoading ? (
                  <div className="w-12 h-12 rounded-[8px] bg-rw-border/40 animate-pulse shrink-0" />
                ) : (
                  <img
                    src={videoInfo.thumbnail}
                    alt=""
                    className="w-12 h-12 rounded-[8px] object-cover shrink-0"
                  />
                )}
                <div className="min-w-0">
                  <p className="text-rw-ink text-[13px] font-semibold truncate">
                    {infoLoading ? '…' : videoInfo?.title || currentUrl.substring(0, 45)}
                  </p>
                  <p className="text-rw-muted text-[11px] mt-0.5">
                    {infoLoading ? '…' : videoInfo?.platform || ''}
                  </p>
                </div>
              </motion.div>
            )}

            <QualityBubbles
              onSelect={handleQualitySelect}
              initialQuality={selectedQuality}
            />

            {/* Download pill button */}
            <motion.button
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0  }}
              transition={{ delay: 0.45 }}
              onClick={handleDownload}
              className="bg-rw-ink text-rw-bg px-10 py-4 rounded-full
                         text-[15px] font-semibold tracking-wide
                         hover:bg-white transition-all duration-200
                         hover:shadow-[0_8px_30px_rgba(255,255,255,0.15)]
                         active:scale-[0.98]"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
            >
              Télécharger →
            </motion.button>

            {backendError && (
              <motion.p
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-red-500 text-xs text-center max-w-xs px-4"
              >
                ⚠ {backendError}
              </motion.p>
            )}

            <button
              onClick={() => { setPhase('input'); setBackendError(''); setVideoInfo(null) }}
              className="text-sm text-rw-muted hover:text-rw-ink transition-colors px-4 py-2"
            >
              ← changer le lien
            </button>
          </motion.div>
        )}

        {/* DOWNLOADING / DONE phase: progress card */}
        {(phase === 'downloading' || phase === 'done') && job && (
          <motion.div
            key="download-card-wrapper"
            className="fixed bottom-6 right-6 md:bottom-8 md:right-8
                       w-[calc(100vw-32px)] md:w-80 pointer-events-auto z-40"
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
