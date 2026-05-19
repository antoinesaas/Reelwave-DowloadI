import { useRef, useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const PLATFORM_MAP = {
  youtube:   { name: 'YouTube',   slug: 'youtube',   dot: '#FF0000' },
  tiktok:    { name: 'TikTok',    slug: 'tiktok',    dot: '#000000' },
  instagram: { name: 'Instagram', slug: 'instagram', dot: '#E1306C' },
  pinterest: { name: 'Pinterest', slug: 'pinterest', dot: '#E60023' },
  twitter:   { name: 'Twitter/X', slug: 'twitter',   dot: '#000000' },
  x:         { name: 'Twitter/X', slug: 'twitter',   dot: '#000000' },
  vimeo:     { name: 'Vimeo',     slug: 'vimeo',     dot: '#1AB7EA' },
}

function detectPlatform(url) {
  if (!url) return null
  const u = url.toLowerCase()
  if (u.includes('youtube.com') || u.includes('youtu.be')) return PLATFORM_MAP.youtube
  if (u.includes('tiktok.com'))   return PLATFORM_MAP.tiktok
  if (u.includes('instagram.com'))return PLATFORM_MAP.instagram
  if (u.includes('pinterest.com'))return PLATFORM_MAP.pinterest
  if (u.includes('twitter.com') || u.includes('x.com')) return PLATFORM_MAP.twitter
  if (u.includes('vimeo.com'))    return PLATFORM_MAP.vimeo
  return null
}

function isValidUrl(url) {
  try { new URL(url); return true } catch { return false }
}

export default function PastePanel({ onValidUrl, onClose }) {
  const [url, setUrl]           = useState('')
  const [platform, setPlatform] = useState(null)
  const [invalid, setInvalid]   = useState(false)
  const [shaking, setShaking]   = useState(false)
  const inputRef = useRef()

  // Auto-focus on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleChange = useCallback((e) => {
    const v = e.target.value.trim()
    setUrl(v)
    setInvalid(false)
    setPlatform(detectPlatform(v))
  }, [])

  // Ctrl+V / right-click paste — works without clipboard permission
  const handleNativePaste = useCallback((e) => {
    const text = (e.clipboardData || window.clipboardData)?.getData('text')
    if (!text) return
    const v = text.trim()
    setUrl(v)
    setInvalid(false)
    setPlatform(detectPlatform(v))
    // If valid URL, auto-submit after short delay
    if (isValidUrl(v)) {
      setTimeout(() => onValidUrl(v), 150)
    }
  }, [onValidUrl])

  const handleSubmit = useCallback(() => {
    const trimmed = url.trim()
    if (!isValidUrl(trimmed)) {
      setInvalid(true)
      setShaking(true)
      setTimeout(() => setShaking(false), 450)
      return
    }
    onValidUrl(trimmed)
  }, [url, onValidUrl])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') handleSubmit()
    if (e.key === 'Escape') onClose?.()
  }, [handleSubmit, onClose])

  const handlePaste = useCallback(async () => {
    // Try Clipboard API first (HTTPS only), fall back silently
    try {
      const text = await navigator.clipboard.readText()
      if (text) {
        const v = text.trim()
        setUrl(v)
        setInvalid(false)
        setPlatform(detectPlatform(v))
        inputRef.current?.focus()
        if (isValidUrl(v)) setTimeout(() => onValidUrl(v), 150)
        return
      }
    } catch {}
    // If permission blocked, focus input so user can Ctrl+V manually
    inputRef.current?.focus()
  }, [onValidUrl])

  return (
    <motion.div
      key="paste-panel"
      initial={{ opacity: 0, scale: 0.88, filter: 'blur(20px)' }}
      animate={{ opacity: 1, scale: 1,    filter: 'blur(0px)'  }}
      exit={{    opacity: 0, scale: 0.92, filter: 'blur(12px)' }}
      transition={{ type: 'spring', stiffness: 300, damping: 30, duration: 0.4 }}
      className="glass-card rounded-[20px] p-6 w-full max-w-lg mx-auto"
    >
      {/* Platform badge */}
      <AnimatePresence mode="wait">
        {platform && (
          <motion.div
            key={platform.slug}
            initial={{ opacity: 0, y: -8, scale: 0.8 }}
            animate={{ opacity: 1, y: 0,  scale: 1   }}
            exit={{    opacity: 0, y: -4, scale: 0.9 }}
            transition={{ type: 'spring', stiffness: 400, damping: 28 }}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full
                        border text-xs font-semibold mb-3 badge-${platform.slug}`}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: platform.dot }}
            />
            {platform.name}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input */}
      <motion.div
        animate={shaking ? { x: [0, -8, 8, -5, 5, 0] } : {}}
        transition={{ duration: 0.4 }}
      >
        <div
          className={`flex items-center gap-3 rounded-[14px] border transition-all duration-200
                      bg-white/5 px-4 py-3
                      ${invalid
                        ? 'border-rw-error shadow-[0_0_0_3px_rgba(248,113,113,0.12)]'
                        : url && isValidUrl(url)
                          ? 'border-white/40 shadow-[0_0_0_3px_rgba(255,255,255,0.06)]'
                          : 'border-rw-border focus-within:border-white/30'
                      }`}
        >
          <input
            ref={inputRef}
            type="url"
            value={url}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onPaste={handleNativePaste}
            placeholder="Colle ton lien ici…"
            className="flex-1 bg-transparent text-rw-ink text-[15px] font-medium
                       placeholder:text-rw-muted/50 outline-none min-w-0"
            spellCheck={false}
            autoComplete="off"
          />

          {/* Paste button */}
          {!url && (
            <button
              onClick={handlePaste}
              className="shrink-0 text-xs text-rw-muted hover:text-rw-ink
                         bg-rw-border/60 hover:bg-rw-border px-2 py-1 rounded-[6px]
                         transition-all font-medium"
            >
              Coller
            </button>
          )}

          {/* Clear */}
          {url && (
            <button
              onClick={() => { setUrl(''); setPlatform(null); setInvalid(false) }}
              className="shrink-0 text-rw-muted/60 hover:text-rw-ink text-lg leading-none"
            >
              ×
            </button>
          )}
        </div>

        {invalid && (
          <p className="text-red-500 text-xs mt-1.5 pl-1">
            Lien invalide — essaie YouTube, TikTok, Instagram…
          </p>
        )}
      </motion.div>

      {/* Confirm button */}
      <motion.button
        onClick={handleSubmit}
        className={`mt-4 w-full py-3 rounded-[12px] text-[15px] font-semibold
                    transition-all duration-200 active:scale-[0.99]
                    ${url && isValidUrl(url)
                      ? 'bg-rw-ink text-rw-bg hover:bg-white hover:shadow-lg'
                      : 'bg-white/8 text-rw-muted cursor-not-allowed border border-rw-border'
                    }`}
        whileHover={url && isValidUrl(url) ? { scale: 1.015 } : {}}
        whileTap={{ scale: 0.98 }}
      >
        Continuer →
      </motion.button>

      {/* Hint */}
      <p className="text-center text-rw-muted text-xs mt-3">
        YouTube · TikTok · Instagram · Pinterest · Twitter/X
      </p>
    </motion.div>
  )
}
