import { useEffect, useState } from "react";
import { getHealthStatus } from "../services/healthService";

function Home() {
  const [status, setStatus] = useState("Checking backend...");

  useEffect(() => {
    getHealthStatus()
      .then((data) => {
        setStatus(`${data.status} — ${data.service}`);
      })
      .catch(() => {
        setStatus("Backend connection failed");
      });
  }, []);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-950 text-white">
      <h1 className="mb-4 text-4xl font-bold">AI Interview Assessment System</h1>

      <p className="text-lg text-gray-300">Backend status: {status}</p>
    </div>
  );
}

export default Home;
