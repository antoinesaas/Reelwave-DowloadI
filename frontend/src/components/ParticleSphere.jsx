import { useRef, useMemo, useEffect, useState, useCallback } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import * as THREE from 'three'
import { motion, AnimatePresence } from 'framer-motion'

// ── Geometry helpers ──────────────────────────────────────────────────────────

function fibonacciSphere(count, radius) {
  const pos = new Float32Array(count * 3)
  const phi = Math.PI * (3 - Math.sqrt(5))
  for (let i = 0; i < count; i++) {
    const y = 1 - (i / (count - 1)) * 2
    const r = Math.sqrt(Math.max(0, 1 - y * y))
    const t = phi * i
    pos[i * 3]     = Math.cos(t) * r * radius
    pos[i * 3 + 1] = y * radius
    pos[i * 3 + 2] = Math.sin(t) * r * radius
  }
  return pos
}

function ringPositions(count, radius) {
  const pos = new Float32Array(count * 3)
  for (let i = 0; i < count; i++) {
    const t = (i / count) * Math.PI * 2
    pos[i * 3]     = Math.cos(t) * radius
    pos[i * 3 + 1] = (Math.random() - 0.5) * 0.12
    pos[i * 3 + 2] = Math.sin(t) * radius
  }
  return pos
}

function explodeTargets(count) {
  const pos = new Float32Array(count * 3)
  for (let i = 0; i < count; i++) {
    const theta = Math.random() * Math.PI * 2
    const phi   = Math.acos(2 * Math.random() - 1)
    const r     = 3.5 + Math.random() * 4
    pos[i * 3]     = Math.sin(phi) * Math.cos(theta) * r
    pos[i * 3 + 1] = Math.cos(phi) * r
    pos[i * 3 + 2] = Math.sin(phi) * Math.sin(theta) * r
  }
  return pos
}

// ── Custom round-particle shader ──────────────────────────────────────────────

const VERT = /* glsl */`
  attribute float aSize;
  varying float vAlpha;
  void main() {
    vAlpha = 1.0;
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    gl_PointSize = aSize * (28.0 / -mv.z);
    gl_Position  = projectionMatrix * mv;
  }
`
const FRAG = /* glsl */`
  varying float vAlpha;
  uniform vec3 uColor;
  void main() {
    vec2  c = gl_PointCoord - 0.5;
    float d = length(c);
    if (d > 0.5) discard;
    float a = smoothstep(0.5, 0.22, d) * vAlpha;
    gl_FragColor = vec4(uColor, a);
  }
`

// ── Particles scene component ─────────────────────────────────────────────────

function Particles({ sphereState, onReady, mouseNDC, particleCount, sphereRadius }) {
  const ref       = useRef()
  const { camera, size } = useThree()

  const homePos    = useMemo(() => fibonacciSphere(particleCount, sphereRadius), [particleCount, sphereRadius])
  const explodePos = useMemo(() => explodeTargets(particleCount), [particleCount])
  const ringPos    = useMemo(() => ringPositions(particleCount, sphereRadius * 1.5), [particleCount, sphereRadius])

  const curPos  = useRef(new Float32Array(particleCount * 3))        // start at 0,0,0
  const vel     = useRef(new Float32Array(particleCount * 3))
  const phase   = useRef('spawning')   // spawning | idle | exploding | ring | logo
  const spawnT  = useRef(0)
  const explodeT = useRef(0)

  const sizes = useMemo(() => {
    const s = new Float32Array(particleCount)
    for (let i = 0; i < particleCount; i++) s[i] = 0.6 + Math.random()
    return s
  }, [particleCount])

  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(curPos.current, 3))
    geo.setAttribute('aSize',    new THREE.BufferAttribute(sizes, 1))
    return geo
  }, [sizes])

  const material = useMemo(() => new THREE.ShaderMaterial({
    uniforms:       { uColor: { value: new THREE.Color(0.08, 0.08, 0.08) } },
    vertexShader:   VERT,
    fragmentShader: FRAG,
    transparent:    true,
    depthWrite:     false,
    blending:       THREE.NormalBlending,
  }), [])

  // Sync phase with external sphereState
  useEffect(() => {
    if (sphereState === 'exploding') {
      phase.current  = 'exploding'
      explodeT.current = 0
    } else if (sphereState === 'ring') {
      phase.current = 'ring'
    } else if (sphereState === 'logo') {
      phase.current = 'logo'
    }
  }, [sphereState])

  const raycaster = useMemo(() => new THREE.Raycaster(), [])
  const plane     = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 0, 1), 0), [])
  const mouseWorld = useMemo(() => new THREE.Vector3(), [])

  useFrame((_, dt) => {
    if (!ref.current) return
    const posAttr = ref.current.geometry.attributes.position
    const cur = curPos.current
    const p   = phase.current

    // Project mouse to 3D plane (z=0)
    let mx = 0, my = 0, mz = 0
    if (mouseNDC.current && p === 'idle') {
      raycaster.setFromCamera(mouseNDC.current, camera)
      raycaster.ray.intersectPlane(plane, mouseWorld)
      mx = mouseWorld.x; my = mouseWorld.y; mz = mouseWorld.z
    }

    // ── Spawn animation (1.2s easing) ──────────────────────────────────────
    if (p === 'spawning') {
      spawnT.current = Math.min(1, spawnT.current + dt / 1.2)
      const t = 1 - Math.pow(1 - spawnT.current, 3) // ease-out-cubic
      for (let i = 0; i < particleCount * 3; i++) {
        cur[i] = homePos[i] * t
      }
      if (spawnT.current >= 1) {
        phase.current = 'idle'
        onReady?.()
      }
      posAttr.array.set(cur)
      posAttr.needsUpdate = true
      return
    }

    // ── Choose target ───────────────────────────────────────────────────────
    let target, lerpK
    if (p === 'idle')      { target = homePos;    lerpK = 0.035 }
    else if (p === 'exploding') { target = explodePos; lerpK = 0.10 }
    else if (p === 'ring')  { target = ringPos;   lerpK = 0.06 }
    else if (p === 'logo')  { target = ringPos;   lerpK = 0.10 }
    else                    { target = homePos;   lerpK = 0.035 }

    // ── Slow rotation in idle ───────────────────────────────────────────────
    if (p === 'idle') {
      ref.current.rotation.y += dt * 0.09
    }

    const REPULSE_R = 0.9

    for (let i = 0; i < particleCount; i++) {
      const idx = i * 3

      // Mouse repulsion (idle only)
      if (p === 'idle' && mouseNDC.current) {
        const dx = cur[idx]     - mx
        const dy = cur[idx + 1] - my
        const dz = cur[idx + 2] - mz
        const d2 = dx * dx + dy * dy + dz * dz
        if (d2 < REPULSE_R * REPULSE_R) {
          const d    = Math.sqrt(d2) || 0.001
          const force = (REPULSE_R - d) / REPULSE_R * 0.04
          vel.current[idx]     += (dx / d) * force
          vel.current[idx + 1] += (dy / d) * force
          vel.current[idx + 2] += (dz / d) * force
        }
      }

      // Damp velocity
      vel.current[idx]     *= 0.88
      vel.current[idx + 1] *= 0.88
      vel.current[idx + 2] *= 0.88

      // Integrate velocity
      cur[idx]     += vel.current[idx]
      cur[idx + 1] += vel.current[idx + 1]
      cur[idx + 2] += vel.current[idx + 2]

      // Lerp toward target
      cur[idx]     += (target[idx]     - cur[idx])     * lerpK
      cur[idx + 1] += (target[idx + 1] - cur[idx + 1]) * lerpK
      cur[idx + 2] += (target[idx + 2] - cur[idx + 2]) * lerpK
    }

    posAttr.array.set(cur)
    posAttr.needsUpdate = true
  })

  return <points ref={ref} geometry={geometry} material={material} />
}

// ── Click sound ───────────────────────────────────────────────────────────────

function playSphereSound() {
  try {
    const ctx  = new AudioContext()
    const osc  = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.frequency.setValueAtTime(440, ctx.currentTime)
    gain.gain.setValueAtTime(0.06, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.06)
    osc.start(ctx.currentTime)
    osc.stop(ctx.currentTime + 0.06)
  } catch {}
}

// ── Main export ───────────────────────────────────────────────────────────────

export default function ParticleSphere({ sphereState, onSphereClick, isLogoMode }) {
  const mouseNDC    = useRef(null)
  const [hovered, setHovered] = useState(false)
  const [ready, setReady]     = useState(false)

  const isMobile       = window.innerWidth < 768
  const particleCount  = isMobile ? 2200 : 4200
  const sphereRadius   = isMobile ? 1.6 : 2.2
  const logoSize       = 72

  const handleMouseMove = useCallback((e) => {
    const rect = e.currentTarget.getBoundingClientRect()
    mouseNDC.current = {
      x:  ((e.clientX - rect.left) / rect.width)  * 2 - 1,
      y: -((e.clientY - rect.top)  / rect.height) * 2 + 1,
    }
    setHovered(true)
  }, [])

  const handleMouseLeave = useCallback(() => {
    mouseNDC.current = null
    setHovered(false)
  }, [])

  const handleClick = useCallback(() => {
    if (!ready || isLogoMode) return
    playSphereSound()
    onSphereClick?.()
  }, [ready, isLogoMode, onSphereClick])

  // Touch support
  const handleTouchMove = useCallback((e) => {
    const touch = e.touches[0]
    const rect  = e.currentTarget.getBoundingClientRect()
    mouseNDC.current = {
      x:  ((touch.clientX - rect.left) / rect.width)  * 2 - 1,
      y: -((touch.clientY - rect.top)  / rect.height) * 2 + 1,
    }
  }, [])

  return (
    <motion.div
      className="fixed z-0 overflow-hidden"
      style={{ background: 'transparent' }}
      animate={isLogoMode ? {
        top:          16,
        left:         16,
        width:        logoSize,
        height:       logoSize,
        borderRadius: logoSize / 2,
      } : {
        top:          0,
        left:         0,
        width:        '100vw',
        height:       '100vh',
        borderRadius: 0,
      }}
      transition={{ type: 'spring', stiffness: 180, damping: 26 }}
    >
      {/* Three.js canvas */}
      <Canvas
        camera={{ position: [0, 0, 5.5], fov: 55 }}
        gl={{ antialias: false, alpha: true }}
        style={{ background: 'transparent', cursor: isLogoMode ? 'default' : 'none' }}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        onTouchMove={handleTouchMove}
      >
        <Particles
          sphereState={sphereState}
          onReady={() => setReady(true)}
          mouseNDC={mouseNDC}
          particleCount={particleCount}
          sphereRadius={sphereRadius}
        />
      </Canvas>

      {/* "Drop a link." center text — only in full sphere mode */}
      <AnimatePresence>
        {!isLogoMode && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: ready ? (hovered ? 0.75 : 0.15) : 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="absolute inset-0 flex items-center justify-center pointer-events-none select-none"
          >
            <span
              className="text-rw-ink font-light text-2xl md:text-3xl"
              style={{ letterSpacing: '0.3em' }}
            >
              Drop a link.
            </span>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
