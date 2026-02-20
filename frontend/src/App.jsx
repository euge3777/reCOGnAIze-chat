import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import logo from '../assets/logo.png'

const API_BASE = 'https://recognaize-chat.onrender.com'

function App() {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [fileName, setFileName] = useState(null)
  const [fileContext, setFileContext] = useState('')
  const [messages, setMessages] = useState([])
  const textareaRef = useRef(null)

  const handleUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    setLoading(true)
    try {
      const res = await axios.post(`${API_BASE}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      if (res.data.error) {
        alert(res.data.error)
        return
      }
      setFileName(res.data.filename)
      const parsed = res.data.content || ''
      console.log('Parsed report content length:', parsed.length)
      setFileContext(parsed)
    } catch (err) {
      console.error(err)
      alert('Error uploading file')
    } finally {
      setLoading(false)
    }
  }

  const handleSend = async () => {
    if (!message.trim()) return

    const userMessage = {
      role: 'user',
      content: message,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    const payload = {
      message,
      conversation_history: messages.map((m) => ({ role: m.role, content: m.content })),
      file_context: fileContext || null,
    }

    setLoading(true)
    try {
      const res = await axios.post(`${API_BASE}/chat`, payload)
      const assistantReply = {
        role: 'assistant',
        content: res.data.reply,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }

      setMessages((prev) => [...prev, userMessage, assistantReply])
      setMessage('')
    } catch (err) {
      console.error(err)
      alert('Error contacting chatbot')
    } finally {
      setLoading(false)
    }
  }

  const handleQuickReply = (text) => {
    setMessage(text)
  }

  const autoResizeTextarea = () => {
    const el = textareaRef.current
    if (!el) return

    // Reset height so scrollHeight is measured correctly
    el.style.height = 'auto'

    const maxHeight = 130 // should match CSS max-height for .input-field
    const newHeight = Math.min(el.scrollHeight, maxHeight)
    el.style.height = `${newHeight}px`

    // Only show scrollbar when content exceeds the max height
    el.style.overflowY = el.scrollHeight > maxHeight ? 'auto' : 'hidden'
  }

  useEffect(() => {
    autoResizeTextarea()
  }, [message])

  const renderMessageContent = (msg) => {
    if (msg.role !== 'assistant') {
      return msg.content
    }

    const normalizeAssistantLine = (line) => {
      let cleaned = line.trim()

      // Remove common markdown bold markers so they don't show up as raw asterisks.
      cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, '$1') // **text** -> text
      cleaned = cleaned.replace(/\*(.*?)\*/g, '$1') // *text* -> text

      // Strip any leftover leading/trailing asterisks that aren't part of bullets.
      cleaned = cleaned.replace(/^\*+\s*/, '')
      cleaned = cleaned.replace(/\*+$/g, '')

      return cleaned
    }

    const rawLines = (msg.content || '')
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0)
      .map(normalizeAssistantLine)

    // Detect if this message is one of the structured "slide" style
    // responses with the four key sections.
    const hasSlideSections = rawLines.some((line) => {
      const lower = line.toLowerCase()
      return (
        lower.includes('understanding your results') ||
        lower.includes('your personalized action plan') ||
        lower.includes('monitoring your progress') ||
        lower.includes('when to see your doctor')
      )
    })

    if (hasSlideSections) {
      const sectionDefs = [
        {
          key: 'understanding',
          match: 'understanding your results',
          icon: '📊',
        },
        {
          key: 'action',
          match: 'your personalized action plan',
          icon: '🎯',
        },
        {
          key: 'monitoring',
          match: 'monitoring your progress',
          icon: '📅',
        },
        {
          key: 'doctor',
          match: 'when to see your doctor',
          icon: '⚕️',
        },
      ]

      const sections = []
      let current = null

      rawLines.forEach((line) => {
        const lower = line.toLowerCase()
        const header = sectionDefs.find((s) => lower.includes(s.match))

        if (header) {
          // Strip any leading emoji or punctuation so we don't
          // render the icon twice (once from the model text and
          // once from our own icon span).
          const cleanedTitle = line.replace(/^[^a-zA-Z0-9]+/, '').trim()

          current = {
            key: header.key,
            title: cleanedTitle,
            icon: header.icon,
            paragraphs: [],
            bullets: [],
          }
          sections.push(current)
          return
        }

        if (!current) return

        if (line.startsWith('•') || line.startsWith('-')) {
          const cleaned = line.replace(/^[-•]\s*/, '')
          current.bullets.push(cleaned)
        } else {
          current.paragraphs.push(line)
        }
      })

      return (
        <div className="assistant-slide">
          {sections.map((section) => (
            <div
              key={section.key}
              className={`assistant-section-card section-${section.key}`}
            >
              <div className="assistant-section-header">
                <span className="assistant-section-icon">{section.icon}</span>
                <span className="assistant-section-title">{section.title}</span>
              </div>

              {section.paragraphs.length > 0 && (
                <div className="assistant-section-content">
                  {section.paragraphs.map((p, idx) => (
                    <p key={idx}>{p}</p>
                  ))}
                </div>
              )}

              {section.bullets.length > 0 && (
                <ul className="assistant-section-list">
                  {section.bullets.map((b, idx) => (
                    <li key={idx}>{b}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )
    }

    const isHeaderLine = (line, index) => {
      const lower = line.toLowerCase()

      if (line.startsWith('•') || line.startsWith('-')) return false

      if (
        lower === 'your results by game:' ||
        lower === 'what this means:' ||
        lower === 'next steps:' ||
        lower === 'key points' ||
        lower === 'common symptoms' ||
        lower === 'types of mci' ||
        lower === 'important note' ||
        lower.includes('understanding your results') ||
        lower.includes('your personalized action plan') ||
        lower.includes('monitoring your progress') ||
        lower.includes('when to see your doctor')
      ) {
        return true
      }

      // If this line is short and the next line is a bullet, treat it as a header.
      const next = rawLines[index + 1] || ''
      if (line.length <= 60 && (next.startsWith('•') || next.startsWith('-'))) {
        return true
      }

      return false
    }

    return rawLines.map((line, index) => (
      <div
        key={index}
        className={isHeaderLine(line, index) ? 'msg-line msg-header-line' : 'msg-line'}
      >
        {line}
      </div>
    ))
  }

  return (
    <div className="page-root">
      <div className="chat-container">
        {/* Header */}
        <div className="chat-header">
          <div className="header-content">
            <div className="bot-avatar">
              <img src={logo} alt="Cognitive Assistant logo" />
            </div>
            <div className="bot-name"> ReCOGnAIze Assistant</div>
            <div className="bot-status">
              <span className="status-dot" />
              <span>Ready to help with your assessment</span>
            </div>
          </div>
        </div>

        {/* Messages / main area */}
        <div className="messages-area">
          <div className="welcome-banner">
            <h3>Welcome to Your Cognitive Health Journey</h3>
            <p>Get personalized insights and actionable next steps</p>
          </div>

          {/* Upload report section */}
          <div className="upload-section">
            <div className="upload-icon">📄</div>
            <h4>Upload Your Report</h4>
            <p>Share your ReCOGnAIze assessment results to get personalized advice.</p>
            <label className="upload-button">
              {fileName ? `Report loaded: ${fileName}` : 'Choose file'}
              <input
                type="file"
                accept=".pdf,.txt,.csv,.json,.xlsx,.xls"
                onChange={handleUpload}
                style={{ display: 'none' }}
              />
            </label>
          </div>

          {/* Quick actions */}
          <div className="quick-actions">
            <button
              type="button"
              className="quick-reply-btn"
              onClick={() => handleQuickReply('Give me personalized advice based on my report')}
            >
              💬 Get Personalized Advice
            </button>
            <button
              type="button"
              className="quick-reply-btn"
              onClick={() => handleQuickReply('Help me understand my ReCOGnAIze results')}
            >
              📊 Understand My Results
            </button>
            <button
              type="button"
              className="quick-reply-btn"
              onClick={() => handleQuickReply('Create an action plan to improve my cognitive health')}
            >
              🎯 Create Action Plan
            </button>
            <button
              type="button"
              className="quick-reply-btn"
              onClick={() => handleQuickReply('When should I repeat this assessment?')}
            >
              📅 When to Retest?
            </button>
          </div>

          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-avatar">
                {msg.role === 'user' ? (
                  <span className="user-initial">You</span>
                ) : (
                  <img src={logo} alt="Cognitive Assistant" />
                )}
              </div>
              <div className="message-content">
                <div
                  className={`message-bubble ${
                    msg.role === 'assistant' ? 'assistant-bubble' : ''
                  }`}
                >
                  {renderMessageContent(msg)}
                </div>
                <div className="message-time">{msg.time}</div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="typing-indicator">
              <div className="message-avatar">
                <img src={logo} alt="Cognitive Assistant typing" />
              </div>
              <div className="typing-dots">
                <span />
                <span />
                <span />
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              className="input-field"
              placeholder="Ask me about the assessment or your results..."
              rows={1}
              value={message}
              ref={textareaRef}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
            />
            <button
              type="button"
              className="send-button"
              onClick={handleSend}
              disabled={loading}
            >
              {loading ? '...' : '>'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
