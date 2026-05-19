import { useState, useRef, useCallback } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || ''

export function useDownload() {
  const [job, setJob] = useState(null)
  const esRef = useRef(null)

  const fetchInfo = useCallback(async (url) => {
    const res = await axios.post(`${API}/api/info`, { url })
    return res.data
  }, [])

  const startDownload = useCallback(async (url, quality) => {
    // Cancel existing job
    if (esRef.current) { esRef.current.close(); esRef.current = null }

    // Create the job
    const { data } = await axios.post(`${API}/api/start`, { url, quality })
    const jobId = data.job_id

    setJob({
      jobId,
      url,
      quality,
      status:  'downloading',
      percent: 0,
      speed:   '',
      eta:     '',
      title:   '',
      thumbnail: '',
      platform: '',
      filename: '',
      error: '',
    })

    // Open SSE stream
    const es = new EventSource(`${API}/api/download/${jobId}`)
    esRef.current = es

    es.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data)

        if (event.type === 'progress') {
          setJob((prev) => prev ? {
            ...prev,
            percent: event.percent,
            speed:   event.speed,
            eta:     event.eta,
          } : null)
        }

        else if (event.type === 'done') {
          setJob((prev) => prev ? {
            ...prev,
            status:    'done',
            percent:   100,
            title:     event.title || prev.title,
            thumbnail: event.thumbnail || prev.thumbnail,
            filename:  event.filename || '',
          } : null)
          es.close()

          // Trigger file download
          const link = document.createElement('a')
          link.href = `${API}/api/file/${jobId}`
          link.download = event.filename || 'reelwave-download'
          link.click()
        }

        else if (event.type === 'error') {
          setJob((prev) => prev ? {
            ...prev,
            status: 'error',
            error:  event.message || 'Erreur inconnue',
          } : null)
          es.close()
        }

      } catch {}
    }

    es.onerror = () => {
      setJob((prev) => prev?.status === 'downloading' ? {
        ...prev,
        status: 'error',
        error: 'Connexion interrompue.',
      } : prev)
      es.close()
    }

    return jobId
  }, [])

  const cancel = useCallback(async () => {
    if (!job) return
    esRef.current?.close()
    try { await axios.post(`${API}/api/cancel/${job.jobId}`) } catch {}
    setJob(null)
  }, [job])

  const reset = useCallback(() => {
    esRef.current?.close()
    setJob(null)
  }, [])

  return { job, fetchInfo, startDownload, cancel, reset }
}
