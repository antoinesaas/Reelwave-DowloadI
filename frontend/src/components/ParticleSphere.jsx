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
    pos[i * 3 + 1] = (Math.random() - 0.5) * 0.08
    pos[i * 3 + 2] = Math.sin(t) * radius
  }
  return pos
}

function explodeTargets(count) {
  const pos = new Float32Array(count * 3)
  for (let i = 0; i < count; i++) {
    // Uniform sphere distribution so no directional bias
    const u     = Math.random()
    const v     = Math.random()
    const theta = 2 * Math.PI * u
    const phi   = Math.acos(2 * v - 1)
    const r     = 2.8 + Math.random() * 2.5
    pos[i * 3]     = Math.sin(phi) * Math.cos(theta) * r
    pos[i * 3 + 1] = Math.cos(phi) * r
    pos[i * 3 + 2] = Math.sin(phi) * Math.sin(theta) * r
  }
  return pos
}

// Origin (implosion target)
function originPositions(count) {
  const pos = new Float32Array(count * 3) // all zeros
  return pos
}

// ── Shaders ──────────────────────────────────────────────────────────────────

const VERT = /* glsl */`
  attribute float aSize;
  attribute float aAlpha;
  varying float vAlpha;
  void main() {
    vAlpha = aAlpha;
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
    float a = smoothstep(0.5, 0.18, d) * vAlpha;
    gl_FragColor = vec4(uColor, a);
  }
`

// ── Particles scene ───────────────────────────────────────────────────────────

function Particles({ sphereState, onReady, mouseNDC, particleCount, sphereRadius }) {
  const ref   = useRef()
  const { camera } = useThree()

  const homePos    = useMemo(() => fibonacciSphere(particleCount, sphereRadius), [particleCount, sphereRadius])
  const explodePos = useMemo(() => explodeTargets(particleCount), [particleCount])
  const ringPos    = useMemo(() => ringPositions(particleCount, sphereRadius * 1.4), [particleCount, sphereRadius])
  const originPos  = useMemo(() => originPositions(particleCount), [particleCount])

  const curPos = useRef(new Float32Array(particleCount * 3))
  const vel    = useRef(new Float32Array(particleCount * 3))
  const alphas = useRef(new Float32Array(particleCount).fill(1))
  const phase  = useRef('spawning')
  const spawnT = useRef(0)

  const sizes = useMemo(() => {
    const s = new Float32Array(particleCount)
    for (let i = 0; i < particleCount; i++) s[i] = 0.5 + Math.random() * 0.9
    return s
  }, [particleCount])

  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(curPos.current, 3))
    geo.setAttribute('aSize',    new THREE.BufferAttribute(sizes, 1))
    geo.setAttribute('aAlpha',   new THREE.BufferAttribute(alphas.current, 1))
    return geo
  }, [sizes])

  const material = useMemo(() => new THREE.ShaderMaterial({
    uniforms:       { uColor: { value: new THREE.Color(0.92, 0.92, 0.92) } },
    vertexShader:   VERT,
    fragmentShader: FRAG,
    transparent:    true,
    depthWrite:     false,
    blending:       THREE.NormalBlending,
  }), [])

  useEffect(() => {
    if      (sphereState === 'imploding')  phase.current = 'imploding'
    else if (sphereState === 'exploding')  phase.current = 'exploding'
    else if (sphereState === 'ring')       phase.current = 'ring'
    else if (sphereState === 'logo')       phase.current = 'logo'
    else if (sphereState === 'idle')       phase.current = phase.current === 'spawning' ? 'spawning' : 'idle'
  }, [sphereState])

  const raycaster  = useMemo(() => new THREE.Raycaster(), [])
  const plane      = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 0, 1), 0), [])
  const mouseWorld = useMemo(() => new THREE.Vector3(), [])

  useFrame((_, dt) => {
    if (!ref.current) return
    const posAttr   = ref.current.geometry.attributes.position
    const alphaAttr = ref.current.geometry.attributes.aAlpha
    const cur = curPos.current
    const p   = phase.current

    // Mouse repulsion world pos
    let mx = 0, my = 0, mz = 0
    if (mouseNDC.current && p === 'idle') {
      raycaster.setFromCamera(mouseNDC.current, camera)
      raycaster.ray.intersectPlane(plane, mouseWorld)
      mx = mouseWorld.x; my = mouseWorld.y; mz = mouseWorld.z
    }

    // ── Spawn ──────────────────────────────────────────────────────────────
    if (p === 'spawning') {
      spawnT.current = Math.min(1, spawnT.current + dt / 1.4)
      const t = 1 - Math.pow(1 - spawnT.current, 3)
      for (let i = 0; i < particleCount * 3; i++) cur[i] = homePos[i] * t
      for (let i = 0; i < particleCount; i++)     alphas.current[i] = Math.min(1, spawnT.current * 2)
      if (spawnT.current >= 1) { phase.current = 'idle'; onReady?.() }
      posAttr.array.set(cur); posAttr.needsUpdate = true
      alphaAttr.array.set(alphas.current); alphaAttr.needsUpdate = true
      return
    }

    // ── Choose target & lerp speed ─────────────────────────────────────────
    let target, lerpK
    if      (p === 'idle')      { target = homePos;    lerpK = 0.032 }
    else if (p === 'imploding') { target = originPos;  lerpK = 0.14  }
    else if (p === 'exploding') { target = explodePos; lerpK = 0.11  }
    else if (p === 'ring')      { target = ringPos;    lerpK = 0.065 }
    else if (p === 'logo')      { target = originPos;  lerpK = 0.10  }
    else                        { target = homePos;    lerpK = 0.032 }

    // ── Slow rotation in idle ──────────────────────────────────────────────
    if (p === 'idle') ref.current.rotation.y += dt * 0.08

    // ── Alpha fade for logo (vanish) ───────────────────────────────────────
    const targetAlpha = (p === 'logo') ? 0 : 1

    const REPULSE_R = 0.85

    for (let i = 0; i < particleCount; i++) {
      const idx = i * 3

      // Mouse repulsion
      if (p === 'idle' && mouseNDC.current) {
        const dx = cur[idx] - mx, dy = cur[idx+1] - my, dz = cur[idx+2] - mz
        const d2 = dx*dx + dy*dy + dz*dz
        if (d2 < REPULSE_R * REPULSE_R) {
          const d = Math.sqrt(d2) || 0.001
          const force = (REPULSE_R - d) / REPULSE_R * 0.038
          vel.current[idx]   += (dx/d) * force
          vel.current[idx+1] += (dy/d) * force
          vel.current[idx+2] += (dz/d) * force
        }
      }

      // Damp + integrate velocity
      vel.current[idx]   *= 0.86
      vel.current[idx+1] *= 0.86
      vel.current[idx+2] *= 0.86
      cur[idx]   += vel.current[idx]
      cur[idx+1] += vel.current[idx+1]
      cur[idx+2] += vel.current[idx+2]

      // Lerp toward target
      cur[idx]   += (target[idx]   - cur[idx])   * lerpK
      cur[idx+1] += (target[idx+1] - cur[idx+1]) * lerpK
      cur[idx+2] += (target[idx+2] - cur[idx+2]) * lerpK

      // Alpha
      alphas.current[i] += (targetAlpha - alphas.current[i]) * 0.07
    }

    posAttr.array.set(cur);     posAttr.needsUpdate   = true
    alphaAttr.array.set(alphas.current); alphaAttr.needsUpdate = true
  })

  return <points ref={ref} geometry={geometry} material={material} />
}

// ── Click sound ───────────────────────────────────────────────────────────────

function playSphereSound() {
  try {
    const ctx  = new AudioContext()
    const osc  = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain); gain.connect(ctx.destination)
    osc.frequency.setValueAtTime(520, ctx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(220, ctx.currentTime + 0.12)
    gain.gain.setValueAtTime(0.07, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.18)
    osc.start(ctx.currentTime); osc.stop(ctx.currentTime + 0.18)
  } catch {}
}

// ── Main export ───────────────────────────────────────────────────────────────

export default function ParticleSphere({ sphereState, onSphereClick, isLogoMode }) {
  const mouseNDC   = useRef(null)
  const [hovered, setHovered] = useState(false)
  const [ready, setReady]     = useState(false)

  const isMobile      = window.innerWidth < 768
  const particleCount = isMobile ? 1800 : 3600
  const sphereRadius  = isMobile ? 1.5 : 2.1

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

  const handleTouchMove = useCallback((e) => {
    const touch = e.touches[0]
    const rect  = e.currentTarget.getBoundingClientRect()
    mouseNDC.current = {
      x:  ((touch.clientX - rect.left) / rect.width)  * 2 - 1,
      y: -((touch.clientY - rect.top)  / rect.height) * 2 + 1,
    }
  }, [])

  return (
    <>
      {/* Canvas always full-screen — fades out via CSS when logo mode */}
      <div
        className="fixed inset-0 z-0"
        style={{
          pointerEvents: isLogoMode ? 'none' : 'auto',
          opacity:    isLogoMode ? 0 : 1,
          transition: 'opacity 0.35s ease',
        }}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        onTouchMove={handleTouchMove}
      >
        <Canvas
          camera={{ position: [0, 0, 5.5], fov: 55 }}
          gl={{ antialias: false, alpha: true }}
          style={{ background: 'transparent', cursor: isLogoMode ? 'default' : 'none' }}
        >
          <Particles
            sphereState={sphereState}
            onReady={() => setReady(true)}
            mouseNDC={mouseNDC}
            particleCount={particleCount}
            sphereRadius={sphereRadius}
          />
        </Canvas>

        {/* "Drop a link." label */}
        <AnimatePresence>
          {!isLogoMode && ready && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="absolute inset-0 flex items-center justify-center pointer-events-none select-none"
            >
              <span
                className="text-rw-ink font-light text-xl md:text-3xl"
                style={{ letterSpacing: '0.28em', opacity: hovered ? 0.75 : 0.5 }}
              >
                Drop a link.
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

    </>
  )
}
