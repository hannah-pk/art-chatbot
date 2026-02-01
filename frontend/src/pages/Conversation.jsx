import { useState, useEffect, useRef } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import api from "../api"

function Conversation(){
    const { conv_id } = useParams()
    const navigate = useNavigate()
    const [messages, setMessages] = useState([])
    const [content, setContent] = useState("")
    const [image, setImage] = useState(null)
    const [imagePreview, setImagePreview] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const textInputRef = useRef(null)

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

    const handleImageChange = (e) => {
        const file = e.target.files[0]
        if (file) {
            setImage(file)
            const reader = new FileReader()
            reader.onloadend = () => {
                setImagePreview(reader.result)
            }
            reader.readAsDataURL(file)
        }
    }

    const clearImage = () => {
        setImage(null)
        setImagePreview(null)
    }

    const sendMessage = async (e) => {
        e.preventDefault()
        if (!content.trim() && !image) return

        try {
            setLoading(true)
            const formData = new FormData()
            formData.append('content', content)
            if (image) {
                formData.append('image', image)
            }

            const response = await api.post(`/api/chat/${conv_id}/message/`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })
            setMessages([
                ...messages,
                response.data.user_message,
                response.data.response_message
            ])
            setContent("")
            clearImage()
            textInputRef.current?.focus()
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
                <div style={{ marginBottom: "10px" }}>
                    <input
                        ref={textInputRef}
                        type="text"
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        placeholder="Type your message..."
                        disabled={loading}
                        style={{ width: "100%", padding: "8px", marginBottom: "8px" }}
                    />
                    <input
                        type="file"
                        accept="image/*"
                        onChange={handleImageChange}
                        disabled={loading}
                        style={{ marginBottom: "8px" }}
                    />
                </div>
                {imagePreview && (
                    <div style={{ marginBottom: "10px", position: "relative", display: "inline-block" }}>
                        <img
                            src={imagePreview}
                            alt="Preview"
                            style={{ maxWidth: "200px", maxHeight: "200px", borderRadius: "4px" }}
                        />
                        <button
                            type="button"
                            onClick={clearImage}
                            disabled={loading}
                            style={{ marginLeft: "10px" }}
                        >
                            Remove Image
                        </button>
                    </div>
                )}
                <div>
                    <button type="submit" disabled={loading || (!content.trim() && !image)}>
                        {loading ? "Sending..." : "Send"}
                    </button>
                </div>
            </form>
        </div>
    )
}
export default Conversation