import { useEffect, useRef } from 'react'
import { motion, useMotionValue, useSpring } from 'framer-motion'

export default function CustomCursor() {
  const x = useMotionValue(-100)
  const y = useMotionValue(-100)
  const scale = useMotionValue(1)

  const springX = useSpring(x, { stiffness: 800, damping: 60 })
  const springY = useSpring(y, { stiffness: 800, damping: 60 })
  const springS = useSpring(scale, { stiffness: 400, damping: 30 })

  const isMobile = /Mobi|Android/i.test(navigator.userAgent)

  useEffect(() => {
    if (isMobile) return

    const move = (e) => {
      x.set(e.clientX)
      y.set(e.clientY)
    }

    const over = (e) => {
      const el = e.target
      const isInteractive = el.closest('button, a, input, [role="button"], canvas')
      scale.set(isInteractive ? 2.5 : 1)
    }

    window.addEventListener('mousemove', move)
    window.addEventListener('mouseover', over)
    return () => {
      window.removeEventListener('mousemove', move)
      window.removeEventListener('mouseover', over)
    }
  }, [isMobile, x, y, scale])

  if (isMobile) return null

  return (
    <motion.div
      className="fixed z-[9999] pointer-events-none top-0 left-0"
      style={{
        x: springX,
        y: springY,
        translateX: '-50%',
        translateY: '-50%',
      }}
    >
      <motion.div
        style={{ scale: springS }}
        className="w-2 h-2 rounded-full bg-rw-ink mix-blend-difference"
      />
    </motion.div>
  )
}
