import React from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import ChatLayout from "./pages/ChatLayout"
import NotFound from "./pages/NotFound"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={<Navigate to="/chat" />}
        />
        <Route
          path="/chat"
          element={<ChatLayout />}
        />
        <Route
          path="/chat/:conv_id"
          element={<ChatLayout />}
        />
        <Route
          path="*"
          element={<NotFound />}
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
