import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute";
import AppShell from "./components/AppShell";
import Dashboard from "./pages/Dashboard";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Interview from "./pages/Interview";
import InterviewResult from "./pages/InterviewResult";
import InterviewSetup from "./pages/InterviewSetup";
import Resume from "./pages/Resume";
import History from "./pages/History";
import Performance from "./pages/Performance";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/resume" element={<Resume />} />
            <Route path="/interview" element={<InterviewSetup />} />
            <Route path="/history" element={<History />} />
            <Route path="/performance" element={<Performance />} />
            <Route path="/interview/:sessionId" element={<Interview />} />
            <Route path="/interview/:sessionId/result" element={<InterviewResult />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
