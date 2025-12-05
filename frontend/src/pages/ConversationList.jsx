import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import api from "../api"

function ConversationList(){
    const [conversations, setConversations] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        getConversations()
    }, [])

    const getConversations = async () => {
        try {
            setLoading(true)
            const response = await api.get("/api/conversations/")
            setConversations(response.data)
            setError(null)
        } catch (err) {
            setError("Failed to load conversations")
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const createConversation = async () => {
        try {
            const response = await api.post("/api/conversations/", { title: "New Conversation" })
            setConversations([...conversations, response.data])
        } catch (err) {
            setError("Failed to create conversation")
            console.error(err)
        }
    }

    if (loading) return <div>Loading conversations...</div>

    return (
        <div>
            <h2>Conversations</h2>
            {error && <div style={{ color: "red" }}>{error}</div>}
            <button onClick={createConversation}>+ New Conversation</button>
            {conversations.length === 0 ? (
                <p>No conversations yet. Create one to get started!</p>
            ) : (
                <ul>
                    {conversations.map((conv) => (
                        <li key={conv.id}>
                            <Link to={`/conversation/${conv.id}`}>
                                {conv.title}
                            </Link>
                            <small> - {new Date(conv.created_at).toLocaleDateString()}</small>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    )
}
export default ConversationList