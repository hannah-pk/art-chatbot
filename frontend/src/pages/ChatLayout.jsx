import { useState, useEffect, useLayoutEffect, useRef } from "react"
import { useParams, useNavigate } from "react-router-dom"
import api, { refreshAccessToken } from "../api"
import AuthModal from "../components/AuthModal"
import TutorialModal from "../components/TutorialModal"
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../constants"
import "../styles/ChatLayout.css"
import 'bootstrap-icons/font/bootstrap-icons.css';

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
    const imageInputRef = useRef(null)
    const [conversations, setConversations] = useState([])
    const [messages, setMessages] = useState([])
    const [content, setContent] = useState("")
    const [imageFile, setImageFile] = useState(null)
    const [imagePreview, setImagePreview] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [conversationsLoading, setConversationsLoading] = useState(true)
    const [authModalOpen, setAuthModalOpen] = useState(false)
    const [tutorialOpen, setTutorialOpen] = useState(false)
    const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem(ACCESS_TOKEN))

    const scrollToBottom = () => {
        if (messagesEndRef.current) {
            // Wait for any images in the last few messages to load before scrolling
            const container = messagesEndRef.current.closest('.messages-container');
            // Only check the last 2 messages (user + bot response) for new images
            const recentMessages = container?.querySelectorAll('.message');
            const recentImages = [];
            if (recentMessages && recentMessages.length >= 2) {
                // Check the last 2 messages for images
                for (let i = Math.max(0, recentMessages.length - 2); i < recentMessages.length; i++) {
                    const imgs = recentMessages[i].querySelectorAll('img.message-image');
                    recentImages.push(...imgs);
                }
            }

            if (recentImages.length > 0) {
                console.log('Waiting for', recentImages.length, 'images to load');
                const imagePromises = recentImages.map((img, index) => {
                    if (img.complete) {
                        console.log('Image', index, 'already loaded');
                        return Promise.resolve();
                    }
                    console.log('Image', index, 'not loaded, waiting...');
                    return new Promise((resolve) => {
                        const loadHandler = () => {
                            console.log('Image', index, 'loaded');
                            resolve();
                        };
                        const errorHandler = () => {
                            console.log('Image', index, 'error');
                            resolve();
                        };
                        img.addEventListener('load', loadHandler, { once: true });
                        img.addEventListener('error', errorHandler, { once: true });
                        // Timeout after 5 seconds to avoid hanging
                        setTimeout(() => {
                            console.log('Image', index, 'timeout');
                            resolve();
                        }, 5000);
                    });
                });

                Promise.all(imagePromises).then(() => {
                    console.log('All images ready, scrolling');
                    messagesEndRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
                });
            } else {
                console.log('No new images, scrolling immediately');
                messagesEndRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
            }
        }
    }
    useEffect(() => {
        api.get('/api/init/')
      }, [])

    useEffect(() => {
        messageInputRef.current?.focus();
    }, [messages]);

    useLayoutEffect(() => {
        // Scroll after messages update, now handles image loading internally
        scrollToBottom()
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

    // Scroll to bottom when messages are first loaded
    useLayoutEffect(() => {
        if (messages.length > 0) {
            scrollToBottom()
        }
    }, [conv_id, messages.length])

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
    const [messageMenuOpenId, setMessageMenuOpenId] = useState(null)

    const handleDeleteMessage = async (messageId) => {
        if (!window.confirm("Delete this message? This cannot be undone.")) return
        try {
            await api.delete(`/api/chat/${conv_id}/message/${messageId}/delete/`)
            setMessages(messages.filter((msg) => msg.id !== messageId))
            setMessageMenuOpenId(null)
        } catch (err) {
            console.error("Failed to delete message", err)
            setError("Failed to delete message")
        }
    }

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

    const handleImageUpload = async(e) => {
        const files = e.target?.files
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
            <TutorialModal
                isOpen={tutorialOpen}
                onClose={() => setTutorialOpen(false)}
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
                    <button
                        type="button"
                        className="auth-btn small tutorial-btn"
                        onClick={() => setTutorialOpen(true)}
                        aria-label="Open tutorial"
                        title="Tutorial"
                    >
                        ?
                    </button>
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
                            <p>Prompt ideas:</p>
                            <p>"Give me a colour scheme for a happy picnic scene"</p>
                            <p>"Give this image a more eerie feel"</p>
                        </div>
                    ) : (
                        <div className="messages">
                            {messages.map((msg, idx) => (
                                <div key={msg.id ?? idx} className={`message ${msg.isPrompt ? "user" : "bot"}`}>
                                    <div className="message-content">
                                        {msg.image && (
                                            <img src={msg.image.url} alt="Message" className="message-image" />
                                        )}
                                        <p>{msg.content}</p>
                                        <div className="message-controls">
                                        <button
                                            type="button"
                                            className="message-menu-btn"
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                setMessageMenuOpenId(messageMenuOpenId === msg.id ? null : msg.id)
                                            }}
                                            aria-label="Message actions"
                                        >
                                            ⋯
                                        </button>
                                        {messageMenuOpenId === msg.id && (
                                            <div className="message-menu" onClick={(e) => e.stopPropagation()}>
                                                <button type="button" onClick={() => handleDeleteMessage(msg.id)}>
                                                    Delete
                                                </button>
                                            </div>
                                        )}
                                    </div>
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
                        ref={imageInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleImageUpload}
                        style={{ display: 'none' }}
                    />
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
                    <button type="button" onClick={() => imageInputRef.current?.click()}>
                        <i class="bi bi-upload"></i>
                    </button>
                    <button type="submit" disabled={loading} className="send-btn">
                        <i class="bi bi-send-fill"></i>
                    </button>
                </form>
            </main>
        </div>
    )
}

export default ChatLayout
