import { useEffect, useRef } from 'react'

// Keep initial content ahead of optional WebGL work. The CSS globe is also
// the default for reduced-motion, data-saving, and unsupported devices.
export default function IntelligenceGlobe({ paused }) {
  const hostRef = useRef(null)
  const pausedRef = useRef(paused)
  const animationControlRef = useRef(() => {})
  useEffect(() => { pausedRef.current = paused; animationControlRef.current() }, [paused])

  useEffect(() => {
    const host = hostRef.current
    let disposed = false
    let teardown = () => {}
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)')
    let nearViewport = false
    let started = false
    let idleHandle = null
    const useIdleCallback = typeof window.requestIdleCallback === 'function'
    const shouldLoad = () => !disposed && nearViewport && !document.hidden && !reduced.matches && !navigator.connection?.saveData && document.readyState === 'complete'
    const start = () => {
      idleHandle = null
      if (!shouldLoad()) return
      started = true
      loadScene()
    }
    const scheduleStart = () => {
      if (started || idleHandle !== null || !shouldLoad()) return
      idleHandle = useIdleCallback ? window.requestIdleCallback(start, { timeout: 2000 }) : window.setTimeout(start, 200)
    }
    const loadScene = () => import('three').then(THREE => {
      if (disposed) return
      let renderer
      try { renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' }) } catch { return }
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75))
      renderer.setClearColor(0x000000, 0)
      renderer.domElement.setAttribute('aria-hidden', 'true')
      host.appendChild(renderer.domElement)
      const scene = new THREE.Scene()
      const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 100)
      camera.position.z = 7.4
      const world = new THREE.Group()
      world.rotation.z = -0.22
      scene.add(world)
      const globe = new THREE.Group()
      world.add(globe)
      globe.add(new THREE.Mesh(new THREE.SphereGeometry(1.39, 48, 32), new THREE.MeshBasicMaterial({ color: 0xf5f3eb })))
      globe.add(new THREE.Mesh(new THREE.SphereGeometry(1.405, 48, 28), new THREE.MeshBasicMaterial({ color: 0x6b7469, wireframe: true, transparent: true, opacity: 0.23 })))
      const vertices = []
      const colors = []
      const ink = new THREE.Color(0x303f34)
      const orange = new THREE.Color(0xe76a37)
      for (let i = 0; i < 4400; i++) {
        const phi = Math.acos(1 - 2 * (i + 0.5) / 4400)
        const theta = Math.PI * (1 + Math.sqrt(5)) * i
        const x = Math.cos(theta) * Math.sin(phi)
        const y = Math.cos(phi)
        const z = Math.sin(theta) * Math.sin(phi)
        // Organic clusters form an abstract neural atlas.
        const field = Math.sin(x * 7 + z * 3) + Math.cos(y * 8 - x * 2) + Math.sin(z * 9 + y * 3)
        if (field < -0.15) continue
        vertices.push(x * 1.425, y * 1.425, z * 1.425)
        const c = field > 2.1 ? orange : ink
        colors.push(c.r, c.g, c.b)
      }
      const geometry = new THREE.BufferGeometry()
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3))
      geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))
      globe.add(new THREE.Points(geometry, new THREE.PointsMaterial({ size: 0.025, vertexColors: true })))
      const rings = new THREE.Group()
      rings.rotation.set(0.95, 0.25, -0.3)
      world.add(rings)
      const satellites = []
      for (let j = 0; j < 3; j++) {
        const radius = 1.78 + j * 0.18
        const points = Array.from({ length: 180 }, (_, i) => new THREE.Vector3(Math.cos(i / 180 * Math.PI * 2) * radius, Math.sin(i / 180 * Math.PI * 2) * radius, 0))
        const ring = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(points), new THREE.LineBasicMaterial({ color: j === 1 ? 0xe66b39 : 0x777f73, transparent: true, opacity: j === 1 ? 0.8 : 0.3 }))
        ring.rotation.x = j * 0.34
        rings.add(ring)
        const dot = new THREE.Mesh(new THREE.SphereGeometry(j === 1 ? 0.065 : 0.04, 16, 12), new THREE.MeshBasicMaterial({ color: j === 1 ? 0xe66b39 : 0x414d3f }))
        ring.add(dot)
        satellites.push({ dot, radius, offset: j * 2.3 })
      }
      let frame = 0
      let visible = true
      let contextLost = false
      let rotation = 0.5
      let previousTime = 0
      const pointer = { x: 0, y: 0 }
      const render = () => renderer.render(scene, camera)
      const resize = () => {
        const { width, height } = host.getBoundingClientRect()
        if (!width || !height) return
        renderer.setSize(width, height)
        camera.aspect = width / height
        camera.position.z = 7.4 * Math.max(1, 0.98 / camera.aspect)
        camera.updateProjectionMatrix()
        render()
      }
      const canAnimate = () => visible && !contextLost && !document.hidden && !reduced.matches && !pausedRef.current
      const animate = time => {
        frame = 0
        if (!canAnimate()) return
        const delta = Math.min((time - previousTime) / 1000, 0.04)
        previousTime = time
        rotation += delta * 0.12
        globe.rotation.y = rotation
        world.rotation.x += (pointer.y * 0.15 - world.rotation.x) * 0.025
        world.rotation.y += (pointer.x * 0.22 - world.rotation.y) * 0.025
        satellites.forEach(({ dot, radius, offset }) => dot.position.set(Math.cos(rotation * 1.6 + offset) * radius, Math.sin(rotation * 1.6 + offset) * radius, 0))
        render()
        frame = requestAnimationFrame(animate)
      }
      const syncAnimation = () => {
        if (canAnimate()) {
          if (!frame) { previousTime = performance.now(); frame = requestAnimationFrame(animate) }
        } else {
          cancelAnimationFrame(frame)
          frame = 0
        }
      }
      animationControlRef.current = syncAnimation
      document.addEventListener('visibilitychange', syncAnimation)
      reduced.addEventListener('change', syncAnimation)
      const onPointer = e => { const rect = host.getBoundingClientRect(); pointer.x = (e.clientX - rect.left) / rect.width - 0.5; pointer.y = (e.clientY - rect.top) / rect.height - 0.5 }
      const resetPointer = () => { pointer.x = 0; pointer.y = 0 }
      const onContextLost = e => { e.preventDefault(); host.classList.remove('globe-ready'); contextLost = true; syncAnimation() }
      const onContextRestored = () => { contextLost = false; resize(); host.classList.add('globe-ready'); syncAnimation() }
      renderer.domElement.addEventListener('webglcontextlost', onContextLost)
      renderer.domElement.addEventListener('webglcontextrestored', onContextRestored)
      host.addEventListener('pointermove', onPointer)
      host.addEventListener('pointerleave', resetPointer)
      const observer = new ResizeObserver(resize)
      observer.observe(host)
      const intersection = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; syncAnimation() })
      intersection.observe(host)
      globe.rotation.y = rotation
      satellites.forEach(({ dot, radius, offset }) => dot.position.set(Math.cos(offset) * radius, Math.sin(offset) * radius, 0))
      resize()
      host.classList.add('globe-ready')
      syncAnimation()
      teardown = () => {
        cancelAnimationFrame(frame)
        animationControlRef.current = () => {}
        document.removeEventListener('visibilitychange', syncAnimation)
        reduced.removeEventListener('change', syncAnimation)
        observer.disconnect()
        intersection.disconnect()
        host.removeEventListener('pointermove', onPointer)
        host.removeEventListener('pointerleave', resetPointer)
        renderer.domElement.removeEventListener('webglcontextlost', onContextLost)
        renderer.domElement.removeEventListener('webglcontextrestored', onContextRestored)
        scene.traverse(object => { object.geometry?.dispose(); object.material?.dispose() })
        renderer.dispose()
        renderer.domElement.remove()
        host.classList.remove('globe-ready')
      }
    }).catch(() => { /* Keep the fallback if the optional 3D chunk fails. */ })
    const startupObserver = new IntersectionObserver(([entry]) => { nearViewport = entry.isIntersecting; scheduleStart() }, { rootMargin: '100px' })
    startupObserver.observe(host)
    window.addEventListener('load', scheduleStart)
    document.addEventListener('visibilitychange', scheduleStart)
    reduced.addEventListener('change', scheduleStart)
    return () => {
      disposed = true
      startupObserver.disconnect()
      window.removeEventListener('load', scheduleStart)
      document.removeEventListener('visibilitychange', scheduleStart)
      reduced.removeEventListener('change', scheduleStart)
      if (idleHandle !== null) {
        if (useIdleCallback) window.cancelIdleCallback(idleHandle)
        else window.clearTimeout(idleHandle)
      }
      teardown()
    }
  }, [])

  return <div ref={hostRef} className="intelligence-globe" role="img" aria-label="An interactive three-dimensional neural globe with orbiting signals"><div className="globe-fallback" aria-hidden="true"><i /><i /><i /></div></div>
}
