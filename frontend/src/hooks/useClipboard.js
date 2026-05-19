import { useState, useCallback } from 'react'

export function useClipboard() {
  const [text, setText] = useState('')

  const read = useCallback(async () => {
    try {
      const t = await navigator.clipboard.readText()
      setText(t)
      return t
    } catch {
      return ''
    }
  }, [])

  return { text, read }
}
