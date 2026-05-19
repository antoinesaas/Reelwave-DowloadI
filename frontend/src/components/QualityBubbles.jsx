import { useState } from 'react'
import { motion } from 'framer-motion'

const QUALITIES = [
  { id: '4K',    label: '4K',    desc: '2160p' },
  { id: '1080p', label: '1080p', desc: 'Full HD' },
  { id: '720p',  label: '720p',  desc: 'HD'      },
  { id: '480p',  label: '480p',  desc: 'SD'      },
  { id: 'MP3',   label: '♪',     desc: 'MP3'     },
]

export default function QualityBubbles({ onSelect, initialQuality = '1080p' }) {
  const [selected, setSelected] = useState(initialQuality)

  const handleSelect = (id) => {
    setSelected(id)
    onSelect?.(id)
  }

  return (
    <div className="flex flex-col items-center gap-3 w-full">
      <p className="text-rw-muted text-xs font-medium tracking-widest uppercase">
        Qualité
      </p>

      <div className="flex items-center justify-center gap-2 flex-wrap w-full px-2">
        {QUALITIES.map((q, i) => {
          const isSelected = selected === q.id
          return (
            <motion.button
              key={q.id}
              onClick={() => handleSelect(q.id)}
              initial={{ opacity: 0, scale: 0.7 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ type: 'spring', stiffness: 380, damping: 24, delay: i * 0.06 }}
              whileTap={{ scale: 0.92 }}
              className={`relative flex flex-col items-center justify-center rounded-full
                          w-14 h-14 md:w-[72px] md:h-[72px]
                          transition-all duration-200 select-none shrink-0
                          ${isSelected ? 'bubble-selected' : 'liquid-bubble'}`}
            >
              <span className={`text-xs md:text-sm font-bold leading-none
                                ${isSelected ? 'text-rw-bg' : 'text-rw-ink'}`}>
                {q.label}
              </span>
              <span className={`text-[8px] md:text-[9px] mt-0.5 font-medium
                                ${isSelected ? 'text-rw-bg/70' : 'text-rw-muted'}`}>
                {q.desc}
              </span>
            </motion.button>
          )
        })}
      </div>
    </div>
  )
}
