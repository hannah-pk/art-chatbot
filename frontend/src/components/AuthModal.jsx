import { useState } from "react"
import api from "../api"
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../constants"
import "../styles/AuthModal.css"

function AuthModal({ isOpen, onClose, onSuccess }) {
    const [mode, setMode] = useState("login")
    const [username, setUsername] = useState("")
    const [password, setPassword] = useState("")
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError(null)
        setLoading(true)

        try {
            const route = mode === "login" ? "/api/token/" : "/api/user/register/"
            const res = await api.post(route, { username, password })

            if (mode === "login") {
                localStorage.setItem(ACCESS_TOKEN, res.data.access)
                localStorage.setItem(REFRESH_TOKEN, res.data.refresh)
            } else {
                // After registration, log them in
                const loginRes = await api.post("/api/token/", { username, password })
                localStorage.setItem(ACCESS_TOKEN, loginRes.data.access)
                localStorage.setItem(REFRESH_TOKEN, loginRes.data.refresh)
            }

            setUsername("")
            setPassword("")
            onSuccess()
            onClose()
        } catch (err) {
            const data = err.response?.data
            if (!data) {
                setError(err.message || "An error occurred")
            } else if (typeof data === 'string') {
                setError(data)
            } else if (data.detail) {
                setError(data.detail)
            } else {
                // Build a readable string from field errors
                const parts = []
                Object.entries(data).forEach(([k, v]) => {
                    if (Array.isArray(v)) parts.push(`${k}: ${v.join(', ')}`)
                    else parts.push(`${k}: ${v}`)
                })
                setError(parts.join(' | '))
            }
        } finally {
            setLoading(false)
        }
    }

    if (!isOpen) return null

    return (
        <div className="auth-modal-overlay" onClick={onClose}>
            <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
                <button className="auth-modal-close" onClick={onClose}>×</button>

                <div className="auth-modal-content">
                    <h2>{mode === "login" ? "Login" : "Create Account"}</h2>

                    {error && <div className="auth-error">{error}</div>}

                    <form onSubmit={handleSubmit}>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Username"
                            disabled={loading}
                            required
                        />
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Password"
                            disabled={loading}
                            required
                        />
                        <button type="submit" disabled={loading}>
                            {loading ? "Loading..." : mode === "login" ? "Login" : "Register"}
                        </button>
                    </form>

                    <div className="auth-modal-footer">
                        {mode === "login" ? (
                            <p>
                                Don't have an account?{" "}
                                <button
                                    type="button"
                                    onClick={() => setMode("register")}
                                    className="auth-modal-link"
                                >
                                    Register
                                </button>
                            </p>
                        ) : (
                            <p>
                                Already have an account?{" "}
                                <button
                                    type="button"
                                    onClick={() => setMode("login")}
                                    className="auth-modal-link"
                                >
                                    Login
                                </button>
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default AuthModal
