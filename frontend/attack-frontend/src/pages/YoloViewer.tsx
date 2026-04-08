import { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

type StartYoloResponse = {
  status: "success" | "error";
  message: string;
  task_id?: string;
  active_task_id?: string;
  source?: string;
  started_by?: string;
};

export default function YoloViewer() {
  const [taskId, setTaskId] = useState<string>("");
  const [imageUrl, setImageUrl] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  const token = localStorage.getItem("token") || "";

  const startYolo = async () => {
    try {
      setLoading(true);
      setError("");

      const res = await fetch(`${API_BASE}/yolo/start?source=0`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data: StartYoloResponse = await res.json();

      if (data.status === "success" && data.task_id) {
        setTaskId(data.task_id);
      } else if (data.active_task_id) {
        setTaskId(data.active_task_id);
        setError(data.message);
      } else {
        setError(data.message || "啟動失敗");
      }
    } catch (err) {
      setError("無法連線到後端");
    } finally {
      setLoading(false);
    }
  };

  const stopYolo = async () => {
    if (!taskId) return;

    try {
      await fetch(`${API_BASE}/yolo/stop/${taskId}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    } catch (err) {
      console.error(err);
    } finally {
      setTaskId("");
      setImageUrl("");
    }
  };

  useEffect(() => {
    if (!taskId) return;

    const timer = setInterval(() => {
      setImageUrl(`${API_BASE}/yolo/stream/${taskId}?t=${Date.now()}`);
    }, 200);

    return () => clearInterval(timer);
  }, [taskId]);

  return (
    <div style={{ padding: 24 }}>
      <h2>YOLO 即時畫面</h2>

      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <button onClick={startYolo} disabled={loading}>
          {loading ? "啟動中..." : "啟動 YOLO"}
        </button>

        <button onClick={stopYolo} disabled={!taskId}>
          停止 YOLO
        </button>
      </div>

      {error && <p style={{ color: "red" }}>{error}</p>}
      {taskId && <p>Task ID: {taskId}</p>}

      <div
        style={{
          width: 960,
          minHeight: 540,
          border: "1px solid #ccc",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#111",
        }}
      >
        {taskId ? (
          <img
            src={imageUrl}
            alt="YOLO stream"
            style={{ width: "100%", maxWidth: 960 }}
          />
        ) : (
          <span style={{ color: "#fff" }}>尚未啟動任務</span>
        )}
      </div>
    </div>
  );
}