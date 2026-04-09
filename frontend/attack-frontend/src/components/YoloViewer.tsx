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
  const [stopping, setStopping] = useState(false);
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
    } catch {
      setError("無法連線到後端");
    } finally {
      setLoading(false);
    }
  };

  const stopYolo = async () => {
    if (!taskId) return;

    try {
      setStopping(true);

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
      setStopping(false);
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
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="mb-6 rounded-3xl border border-white/60 bg-white/70 p-6 shadow-xl shadow-slate-200/60 backdrop-blur-xl">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              單鏡頭 YOLO 即時畫面
            </h1>
            <p className="mt-2 text-sm text-slate-600">
              啟動後將持續從後端抓取最新偵測結果，並即時更新畫面。
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={startYolo}
              disabled={loading || stopping}
              className="inline-flex items-center justify-center rounded-xl bg-lime-400 px-5 py-3 text-sm font-semibold text-black shadow-md shadow-lime-400/30 transition hover:bg-lime-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "啟動中..." : "啟動偵測"}
            </button>

            <button
              onClick={stopYolo}
              disabled={!taskId || loading || stopping}
              className="inline-flex items-center justify-center rounded-xl bg-red-500 px-5 py-3 text-sm font-semibold text-white shadow-md shadow-red-500/20 transition hover:bg-red-400 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {stopping ? "停止中..." : "停止偵測"}
            </button>
          </div>
        </div>

        <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
          <div className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm text-slate-700">
            <span className="mr-2 h-2.5 w-2.5 rounded-full bg-emerald-500" />
            {taskId ? `Task ID: ${taskId}` : "尚未啟動任務"}
          </div>

          <div className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm text-slate-700">
            Source: 0
          </div>
        </div>

        {error && (
          <div className="mt-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
            {error}
          </div>
        )}
      </div>

      <div className="overflow-hidden rounded-3xl border border-slate-200/80 bg-white/80 shadow-2xl shadow-slate-200/70 backdrop-blur-xl">
        <div className="flex items-center justify-between border-b border-slate-200/80 px-5 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">即時監看畫面</h2>
            <p className="mt-1 text-sm text-slate-500">
              解析度依後端 snapshot 更新頻率顯示
            </p>
          </div>

          <div className="rounded-full bg-slate-900 px-3 py-1 text-xs font-medium text-white">
            {taskId ? "RUNNING" : "IDLE"}
          </div>
        </div>

        <div className="p-4 sm:p-6">
          <div className="relative flex min-h-[320px] items-center justify-center overflow-hidden rounded-2xl border border-slate-200 bg-slate-950 sm:min-h-[420px] lg:min-h-[540px]">
            {taskId ? (
              <img
                src={imageUrl}
                alt="YOLO stream"
                className="h-full w-full object-contain"
              />
            ) : (
              <div className="flex flex-col items-center justify-center px-6 text-center">
                <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 text-2xl text-white">
                  📷
                </div>
                <h3 className="text-lg font-semibold text-white">尚未啟動任務</h3>
                <p className="mt-2 max-w-md text-sm leading-6 text-slate-300">
                  請先點擊上方「啟動 YOLO」，後端開始寫入最新偵測畫面後，這裡會自動更新。
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}