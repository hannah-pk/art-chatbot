import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import api from "../api"
import AuthModal from "../components/AuthModal"
import { ACCESS_TOKEN } from "../constants"
import "../styles/ChatLayout.css"

function ChatLayout() {
    const { conv_id } = useParams()
    const navigate = useNavigate()
    const [conversations, setConversations] = useState([])
    const [messages, setMessages] = useState([])
    const [content, setContent] = useState("")
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [conversationsLoading, setConversationsLoading] = useState(true)
    const [authModalOpen, setAuthModalOpen] = useState(false)
    const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem(ACCESS_TOKEN))

    useEffect(() => {
        getConversations()
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
            console.error("Failed to load messages", err)
        }
    }

    const createNewConversation = async () => {
        try {
            const response = await api.post("/api/conversations/", { title: "New Conversation" })
            setConversations([response.data, ...conversations])
            navigate(`/chat/${response.data.id}`)
        } catch (err) {
            setError("Failed to create conversation")
            console.error(err)
        }
    }

    const sendMessage = async (e) => {
        e.preventDefault()
        if (!content.trim()) return

        let currentConvId = conv_id

        try {
            setLoading(true)
            
            // If no conversation exists yet, create one first
            if (!currentConvId) {
                const convResponse = await api.post("/api/conversations/", { title: "New Conversation" })
                currentConvId = convResponse.data.id
                setConversations([convResponse.data, ...conversations])
                navigate(`/chat/${currentConvId}`)
            }

            // Send message
            const response = await api.post(`/api/chat/${currentConvId}/message/`, { content })
            setMessages([
                ...messages,
                response.data.user_message,
                response.data.response_message
            ])
            setContent("")
        } catch (err) {
            setError("Failed to send message")
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
    }

    return (
        <div className="chat-layout">
            <AuthModal
                isOpen={authModalOpen}
                onClose={() => setAuthModalOpen(false)}
                onSuccess={handleAuthSuccess}
            />

            <aside className="sidebar">
                <div className="sidebar-header">
                    <h1>Conversations</h1>
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
                                        className={conv_id === conv.id ? "active" : ""}
                                        onClick={() => navigate(`/chat/${conv.id}`)}
                                    >
                                        <span className="title">{conv.title}</span>
                                        <span className="date">
                                            {new Date(conv.created_at).toLocaleDateString()}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                )}

                <div className="sidebar-footer">
                    {isAuthenticated ? (
                        <button onClick={handleLogout} className="auth-btn logout-btn">
                            Logout
                        </button>
                    ) : (
                        <button onClick={() => setAuthModalOpen(true)} className="auth-btn login-btn">
                            Login / Register
                        </button>
                    )}
                </div>
            </aside>

            <main className="chat-main">
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
                                        <strong>{msg.isPrompt ? "You" : "Bot"}:</strong>
                                        <p>{msg.content}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {error && <div className="error">{error}</div>}

                <form onSubmit={sendMessage} className="message-form">
                    <input
                        type="text"
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        placeholder="Type your message..."
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
