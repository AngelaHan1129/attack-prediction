import { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

type DualResponse = {
  status: "success" | "error";
  message: string;
  task_id?: string;
  active_task_id?: string;
};

export default function DualYoloViewer() {
  const [taskId, setTaskId] = useState("");
  const [cam0Url, setCam0Url] = useState("");
  const [cam1Url, setCam1Url] = useState("");
  const [error, setError] = useState("");
  const [cam0Error, setCam0Error] = useState(false);
  const [cam1Error, setCam1Error] = useState(false);

  const token = localStorage.getItem("token") || "";

  const startDual = async () => {
    try {
      setError("");
      setCam0Error(false);
      setCam1Error(false);
      setTaskId("");
      setCam0Url("");
      setCam1Url("");

      const res = await fetch(
        `${API_BASE}/yolo/start/dual?source0=0&source1=1`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!res.ok) {
        const text = await res.text();
        setError(`雙鏡頭啟動失敗：${res.status} ${text}`);
        return;
      }

      const data: DualResponse = await res.json();

      if (data.status === "success" && data.task_id) {
        setTaskId(data.task_id);
      } else if (data.active_task_id) {
        setTaskId(data.active_task_id);
        setError(data.message);
      } else {
        setError(data.message || "雙鏡頭啟動失敗");
      }
    } catch (err) {
      setError("無法連線到後端");
    }
  };

  const stopDual = async () => {
    if (!taskId) return;

    try {
      const res = await fetch(`${API_BASE}/yolo/stop/${taskId}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json();

      if (res.ok) {
        setError("");
        setTaskId("");
        setCam0Url("");
        setCam1Url("");
        setCam0Error(false);
        setCam1Error(false);
      } else {
        setError(data.detail || "停止任務失敗");
      }
    } catch (err) {
      setError("無法連線到後端，停止失敗");
    }
  };

  useEffect(() => {
    if (!taskId) return;

    setCam0Error(false);
    setCam1Error(false);

    const timer = setInterval(() => {
      const t = Date.now();
      setCam0Url(`${API_BASE}/yolo/stream/${taskId}/cam0?t=${t}`);
      setCam1Url(`${API_BASE}/yolo/stream/${taskId}/cam1?t=${t}`);
    }, 200);

    return () => clearInterval(timer);
  }, [taskId]);

  return (
    <div style={{ padding: 24 }}>
      <h2>雙鏡頭 YOLO</h2>

      <div style={{ display: "flex", gap: 12, marginTop: 12 }}>
        <button onClick={startDual}>啟動雙鏡頭</button>
        <button onClick={stopDual} disabled={!taskId}>
          停止任務
        </button>
      </div>

      {taskId && <p style={{ marginTop: 12 }}>Task ID: {taskId}</p>}
      {error && <p style={{ color: "red", marginTop: 12 }}>{error}</p>}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 16,
          marginTop: 20,
        }}
      >
        <div>
          <h3>cam0</h3>
          {cam0Url ? (
            <>
              <img
                src={cam0Url}
                alt="cam0"
                style={{
                  width: "100%",
                  border: "1px solid #ccc",
                  minHeight: 240,
                  objectFit: "contain",
                  background: "#111",
                }}
                onError={() => setCam0Error(true)}
                onLoad={() => setCam0Error(false)}
              />
              {cam0Error && (
                <p style={{ color: "red", marginTop: 8 }}>
                  cam0 畫面載入失敗
                </p>
              )}
            </>
          ) : (
            <div
              style={{
                height: 240,
                background: "#111",
                color: "#fff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              尚未啟動
            </div>
          )}
        </div>

        <div>
          <h3>cam1</h3>
          {cam1Url ? (
            <>
              <img
                src={cam1Url}
                alt="cam1"
                style={{
                  width: "100%",
                  border: "1px solid #ccc",
                  minHeight: 240,
                  objectFit: "contain",
                  background: "#111",
                }}
                onError={() => setCam1Error(true)}
                onLoad={() => setCam1Error(false)}
              />
              {cam1Error && (
                <p style={{ color: "red", marginTop: 8 }}>
                  cam1 畫面載入失敗
                </p>
              )}
            </>
          ) : (
            <div
              style={{
                height: 240,
                background: "#111",
                color: "#fff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              尚未啟動
            </div>
          )}
        </div>
      </div>
    </div>
  );
}