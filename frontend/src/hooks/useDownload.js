import { useState, useCallback } from 'react'

const API = import.meta.env.VITE_API_URL || ''

export function useDownload() {
  const [job, setJob] = useState(null)

  const fetchInfo = useCallback(async (url) => {
    const res = await fetch(`${API}/api/info`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `Erreur ${res.status}`)
    }
    return res.json()
  }, [])

  const startDownload = useCallback(async (url, quality) => {
    setJob({
      url,
      quality,
      status:    'loading',
      percent:   0,
      title:     '',
      thumbnail: '',
      filename:  '',
      error:     '',
    })

    const res = await fetch(`${API}/api/dl`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, quality }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      const msg = err.detail || `Erreur ${res.status}`
      setJob((p) => p ? { ...p, status: 'error', error: msg } : null)
      throw new Error(msg)
    }

    const data = await res.json()

    setJob({
      url,
      quality,
      status:    'done',
      percent:   100,
      title:     data.title,
      thumbnail: data.thumbnail,
      filename:  data.filename,
      error:     '',
    })

    // Trigger browser download — opens directly from CDN URL
    const a = document.createElement('a')
    a.href     = data.url
    a.download = data.filename
    a.target   = '_blank'
    a.rel      = 'noopener noreferrer'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)

    return data
  }, [])

  const cancel = useCallback(() => {
    setJob(null)
  }, [])

  const reset = useCallback(() => {
    setJob(null)
  }, [])

  return { job, fetchInfo, startDownload, cancel, reset }
}
