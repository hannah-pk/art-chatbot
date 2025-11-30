
import React from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import Register from "./pages/Register"
import Login from "./pages/Login"
import Conversation from "./pages/Conversation"
import ConversationList from "./pages/ConversationList"
import NotFound from "./pages/NotFound"
import ProtectedRoute from "./components/ProtectedRoute"

function Logout(){
  localStorage.clear()
  return <Navigate to="/" />

}

function RegisterClear(){
  localStorage.clear()
  return <Register />
}

function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path = "/"
          element = {<Conversation/>}
        />
        <Route 
          path = "/logout"
          element = {<Logout/>}
        />
        <Route 
          path = "*"
          element = {<NotFound />}
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
