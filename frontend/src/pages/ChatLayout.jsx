import { useState, useEffect, useRef } from "react"
import { useParams, useNavigate } from "react-router-dom"
import api, { refreshAccessToken } from "../api"
import AuthModal from "../components/AuthModal"
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../constants"
import "../styles/ChatLayout.css"

// Utility function to convert blob URL to File
const blobUrlToFile = async (blobUrl, filename) => {
    const response = await fetch(blobUrl)
    const blob = await response.blob()
    return new File([blob], filename, { type: blob.type })
}

function ChatLayout() {
    const { conv_id } = useParams()
    const navigate = useNavigate()
    const messagesEndRef = useRef(null)
    const messageInputRef = useRef(null)
    const [conversations, setConversations] = useState([])
    const [messages, setMessages] = useState([])
    const [content, setContent] = useState("")
    const [imageFile, setImageFile] = useState(null)
    const [imagePreview, setImagePreview] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [conversationsLoading, setConversationsLoading] = useState(true)
    const [authModalOpen, setAuthModalOpen] = useState(false)
    const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem(ACCESS_TOKEN))

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }
    useEffect(() => {
        api.get('/api/init/')
      }, [])

    useEffect(() => {
        messageInputRef.current?.focus();
    }, [messages]);

    useEffect(() => {
        setTimeout(scrollToBottom,0)
    }, [messages])

    useEffect(() => {
        if (isAuthenticated) {
            getConversations()
        }
    }, [isAuthenticated])

    useEffect(() => {
        const initializeAuth = async () => {
            const hasAccess = !!localStorage.getItem(ACCESS_TOKEN)
            const hasRefresh = !!localStorage.getItem(REFRESH_TOKEN)

            if (hasAccess) {
                setIsAuthenticated(true)
                return
            }

            if (hasRefresh) {
                try {
                    await refreshAccessToken()
                    setIsAuthenticated(true)
                } catch (err) {
                    console.warn("Refresh token failed", err)
                    handleLogout()
                }
            }
        }

        initializeAuth()
    }, [])

    useEffect(() => {
        if (conv_id) {
            getMessages()
        } else {
            setMessages([])
        }
    }, [conv_id])

    const getConversations = async () => {
        try {
            setConversationsLoading(true)
            const response = await api.get("/api/conversations/")
            setConversations(response.data)
        } catch (err) {
            console.error("Failed to load conversations", err)
        } finally {
            setConversationsLoading(false)
        }
    }

    const getMessages = async () => {
        try {
            const response = await api.get(`/api/chat/${conv_id}/`)
            setMessages(response.data)
        } catch (err) {
            if (err?.response?.status === 404) {
                setError("Conversation does not exist.")
                setMessages([])
                navigate('/chat')
            } else {
                setError("Failed to load messages")
            }
            console.error("Failed to load messages", err)
        }
    }

    const createNewConversation = async () => {
        // Do not create a conversation on the server yet.
        // Just clear local messages and navigate to the empty conversation view.
        setMessages([])
        setContent("")
        navigate(`/chat`)
    }

    const sendMessage = async (e) => {
        e.preventDefault()
        if (!content.trim() && !imageFile) return

        let currentConvId = conv_id

        try {
            setLoading(true)
            setError(null)

            // If no conversation exists yet, create one first
            if (!currentConvId) {
                const convResponse = await api.post("/api/conversations/", { title: "New Conversation" })
                currentConvId = convResponse.data.id
                setConversations([convResponse.data, ...conversations])
                navigate(`/chat/${currentConvId}`)
            }

            // Create FormData to handle both text and image
            const formData = new FormData()
            formData.append("content", content)
            if (imageFile) {
                formData.append("image", imageFile)
            }

            // Send message with FormData (instead of JSON)
            const response = await api.post(`/api/chat/${currentConvId}/message/`, formData, {
                headers: {
                    "Content-Type": "multipart/form-data"
                }
            })
            setMessages([
                ...messages,
                response.data.user_message,
                response.data.response_message
            ])
            setContent("")
            setImageFile(null)
            setImagePreview(null)
            
        } catch (err) {
            // If conversation is gone (404), show warning and redirect to empty chat
            if (err?.response?.status === 404) {
                setError("This conversation no longer exists. You have been redirected to a new chat.")
                setMessages([])
                navigate('/chat')
            } else {
                setError("Failed to send message")
            }
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleLogout = () => {
        localStorage.clear()
        setIsAuthenticated(false)
        navigate("/chat")
    }

    const handleAuthSuccess = () => {
        setIsAuthenticated(true)
        getConversations()
        setMessages([])
        navigate('/chat')
    }

    useEffect(() => {
        const onUnauthorized = () => {
            console.warn("Unauthorized API response: logging out")
            handleLogout()
        }

        window.addEventListener('unauthorized', onUnauthorized)

        return () => {
            window.removeEventListener('unauthorized', onUnauthorized)
        }
    }, [])

    const [menuOpenId, setMenuOpenId] = useState(null)

    const handleImagePaste = async (e) => {
        const items = e.clipboardData?.items
        if (!items) return

        for (let item of items) {
            if (item.type.startsWith('image/')) {
                e.preventDefault()
                const file = item.getAsFile()
                await processImageFile(file)
                break
            }
        }
    }

    const handleImageDrop = async (e) => {
        e.preventDefault()
        const files = e.dataTransfer?.files
        if (!files) return

        for (let file of files) {
            if (file.type.startsWith('image/')) {
                await processImageFile(file)
                break
            }
        }
    }

    const processImageFile = async (file) => {
        setImageFile(file)
        // Create preview
        const reader = new FileReader()
        reader.onload = (e) => {
            setImagePreview(e.target?.result)
        }
        reader.readAsDataURL(file)
    }

    const clearImage = () => {
        setImageFile(null)
        setImagePreview(null)
    }

    const handleDragOver = (e) => {
        e.preventDefault()
    }

    const handleRenameConversation = async (convId) => {
        const newTitle = window.prompt("Enter new title for the conversation:", conversations.find(c=>c.id===convId)?.title || "")
        if (!newTitle || !newTitle.trim()) return
        try {
            const res = await api.patch(`/api/conversations/${convId}/`, { title: newTitle.trim() })
            setConversations(conversations.map(c => c.id === convId ? res.data : c))
            setMenuOpenId(null)
        } catch (err) {
            console.error("Failed to rename conversation", err)
            setError("Failed to rename conversation")
        }
    }

    const handleDeleteConversation = async (convId) => {
        if (!window.confirm("Delete this conversation? This cannot be undone.")) return
        try {
            await api.delete(`/api/conversations/${convId}/delete/`)
            setConversations(conversations.filter(c => c.id !== convId))
            setMenuOpenId(null)
            if (String(convId) === String(conv_id)) {
                navigate('/chat')
                setMessages([])
            }
        } catch (err) {
            console.error("Failed to delete conversation", err)
            setError("Failed to delete conversation")
        }
    }
    
    return (
        <div className="chat-layout">
            <AuthModal
                isOpen={authModalOpen}
                onClose={() => setAuthModalOpen(false)}
                onSuccess={handleAuthSuccess}
            />

            {isAuthenticated && (
            <aside className="sidebar">
                <div className="sidebar-header">
                    <button onClick={createNewConversation} className="new-chat-btn">
                        + New Chat
                    </button>
                </div>
                {conversationsLoading ? (
                    <p className="loading">Loading conversations...</p>
                ) : (
                    <div className="conversations-list">
                        {conversations.length === 0 ? (
                            <p className="empty">No conversations yet</p>
                        ) : (
                            <ul>
                                {conversations.map((conv) => (
                                    <li
                                        key={conv.id}
                                        className={String(conv_id) === String(conv.id) ? "active" : ""}
                                        onClick={() => navigate(`/chat/${conv.id}`)}
                                    >
                                        <span className="title">{conv.title}</span>
                                        <span className="date">
                                            {new Date(conv.created_at).toLocaleDateString()}
                                        </span>

                                        <button
                                            className="conv-menu-btn"
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                setMenuOpenId(menuOpenId === conv.id ? null : conv.id)
                                            }}
                                            aria-label="Conversation menu"
                                        >
                                            ⋯
                                        </button>

                                        {menuOpenId === conv.id && (
                                            <div className="conv-menu" onClick={(e)=>e.stopPropagation()}>
                                                <button onClick={() => handleRenameConversation(conv.id)}>Rename</button>
                                                <button onClick={() => handleDeleteConversation(conv.id)}>Delete</button>
                                            </div>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                )}

            </aside>
            )}

            <main className={`chat-main ${isAuthenticated ? '' : 'anon'}`}>
                <div className="top-action">
                    {isAuthenticated ? (
                        <button onClick={handleLogout} className="auth-btn small logout-btn">
                            Logout
                        </button>
                    ) : (
                        <button onClick={() => setAuthModalOpen(true)} className="auth-btn small login-btn">
                            Login / Register
                        </button>
                    )}
                </div>
                <div className="messages-container">
                    {messages.length === 0 && !conv_id ? (
                        <div className="welcome">
                            <h2>Start a New Conversation</h2>
                            <p>Create a new chat or select one from the left to begin</p>
                        </div>
                    ) : (
                        <div className="messages">
                            {messages.map((msg, idx) => (
                                <div key={idx} className={`message ${msg.isPrompt ? "user" : "bot"}`}>
                                    <div className="message-content">
                                        {msg.image && (
                                            <img src={msg.image.url} alt="Message" className="message-image" />
                                        )}
                                        <p>{msg.content}</p>
                                    </div>
                                </div>
                            ))}
                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>

                {error && <div className="error">{error}</div>}

                {imagePreview && (
                    <div className="image-preview-container">
                        <img src={imagePreview} alt="Preview" className="image-preview" />
                        <button
                            type="button"
                            onClick={clearImage}
                            className="clear-image-btn"
                            disabled={loading}
                        >
                            ✕
                        </button>
                    </div>
                )}

                <form onSubmit={sendMessage} className="message-form">
                    <input
                        ref={messageInputRef}
                        type="text"
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        onPaste={handleImagePaste}
                        onDrop={handleImageDrop}
                        onDragOver={handleDragOver}
                        placeholder="Type your message or drag/paste an image..."
                        disabled={loading}
                        className="message-input"
                    />
                    <button type="submit" disabled={loading} className="send-btn">
                        {loading ? "Sending..." : "Send"}
                    </button>
                </form>
            </main>
        </div>
    )
}

export default ChatLayout
