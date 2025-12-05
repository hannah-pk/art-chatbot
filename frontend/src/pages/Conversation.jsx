import { useState, useEffect } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import api from "../api"

function Conversation(){
    const { conv_id } = useParams()
    const navigate = useNavigate()
    const [messages, setMessages] = useState([])
    const [content, setContent] = useState("")
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (conv_id) {
            getMessages()
        }
    }, [conv_id])

    const getMessages = async () => {
        try {
            const response = await api.get(`/api/chat/${conv_id}/`)
            setMessages(response.data)
        } catch (err) {
            setError("Failed to load messages")
            console.error(err)
        }
    }

    const sendMessage = async (e) => {
        e.preventDefault()
        if (!content.trim()) return

        try {
            setLoading(true)
            const response = await api.post(`/api/chat/${conv_id}/message/`, { content })
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

    if (!conv_id) {
        return (
            <div>
                <h1>Chatbot</h1>
                <Link to="/conversations">← Back to Conversations</Link>
                <p>Select or create a conversation to start chatting</p>
            </div>
        )
    }

    return (
        <div>
            <Link to="/conversations">← Back to Conversations</Link>
            <h2>Chat</h2>
            {error && <div style={{ color: "red" }}>{error}</div>}
            <div style={{ height: "400px", overflowY: "auto", border: "1px solid #ccc", padding: "10px" }}>
                {messages.map((msg, idx) => (
                    <div key={idx} style={{ marginBottom: "10px" }}>
                        <strong>{msg.isPrompt ? "You" : "Bot"}:</strong> {msg.content}
                    </div>
                ))}
            </div>
            <form onSubmit={sendMessage} style={{ marginTop: "10px" }}>
                <input
                    type="text"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="Type your message..."
                    disabled={loading}
                />
                <button type="submit" disabled={loading}>
                    {loading ? "Sending..." : "Send"}
                </button>
            </form>
        </div>
    )
}
export default Conversation