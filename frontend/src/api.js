import axios from "axios";
import { ACCESS_TOKEN, REFRESH_TOKEN } from "./constants";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    withCredentials: true,
})

api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem(ACCESS_TOKEN);
        if (token){
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Token is invalid or expired, clear it
            localStorage.removeItem(ACCESS_TOKEN)
            localStorage.removeItem(REFRESH_TOKEN)
            // Dispatch event so ChatLayout can handle logout
            window.dispatchEvent(new Event('unauthorized'))
        }
        return Promise.reject(error)
    }
)

export const refreshAccessToken = async () => {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN)
    if (!refreshToken) {
        throw new Error("No refresh token available")
    }
    const response = await api.post("/api/token/refresh/", { refresh: refreshToken })
    const { access, refresh } = response.data
    if (access) {
        localStorage.setItem(ACCESS_TOKEN, access)
    }
    if (refresh) {
        localStorage.setItem(REFRESH_TOKEN, refresh)
    }
    return access
}

export default api