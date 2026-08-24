import { BrowserRouter, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute";
import Dashboard from "./pages/Dashboard";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Interview from "./pages/Interview";
import InterviewResult from "./pages/InterviewResult";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />
        </Route>

        <Route path="/interview/:sessionId" element={<Interview />} />
        <Route path="/interview/:sessionId/result" element={<InterviewResult />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
