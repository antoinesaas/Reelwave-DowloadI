import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const QUALITIES = [
  { id: '4K',    label: '4K',    desc: '2160p' },
  { id: '1080p', label: '1080p', desc: 'Full HD' },
  { id: '720p',  label: '720p',  desc: 'HD'      },
  { id: '480p',  label: '480p',  desc: 'SD'      },
  { id: 'MP3',   label: '♪',     desc: 'MP3'    },
]

export default function QualityBubbles({ onSelect, initialQuality = '1080p' }) {
  const [selected, setSelected] = useState(initialQuality)

  const handleSelect = (id) => {
    setSelected(id)
    onSelect?.(id)
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center gap-6"
    >
      <p className="text-rw-muted text-sm font-medium tracking-wide">
        Choisir la qualité
      </p>

      {/* Bubbles row */}
      <div className="flex items-end justify-center gap-3 flex-wrap">
        {QUALITIES.map((q, i) => (
          <motion.button
            key={q.id}
            onClick={() => handleSelect(q.id)}
            initial={{ opacity: 0, y: 60, scale: 0.6 }}
            animate={{ opacity: 1, y: 0,  scale: 1   }}
            transition={{
              type:      'spring',
              stiffness: 320,
              damping:   22,
              delay:     i * 0.08,
            }}
            whileHover={{ scale: selected === q.id ? 1.15 : 1.08 }}
            whileTap={{ scale: 0.92 }}
            className={`relative w-20 h-20 rounded-full flex flex-col items-center justify-center
                        transition-all duration-200 select-none
                        ${selected === q.id ? 'bubble-selected' : 'liquid-bubble hover:shadow-md'}`}
            style={{
              // Float animation for unselected bubbles
              animation: selected === q.id
                ? 'none'
                : `float ${3.5 + i * 0.4}s ease-in-out ${i * 0.2}s infinite`,
            }}
          >
            {/* Label */}
            <span
              className={`text-sm font-bold leading-none
                          ${selected === q.id ? 'text-white' : 'text-rw-ink'}`}
            >
              {q.label}
            </span>
            <span
              className={`text-[9px] mt-0.5 font-medium
                          ${selected === q.id ? 'text-white/70' : 'text-rw-muted'}`}
            >
              {q.desc}
            </span>

            {/* Selected ring glow */}
            {selected === q.id && (
              <motion.span
                layoutId="bubble-ring"
                className="absolute inset-0 rounded-full border-2 border-rw-ink"
                style={{ boxShadow: '0 0 24px rgba(10,10,10,0.2)' }}
              />
            )}
          </motion.button>
        ))}
      </div>
    </motion.div>
  )
}
