import { useEffect, useMemo, useState } from "react";

import dashboardBg from "../assets/hlogo_al.png";
import workspaceOverlay from "../assets/work-space.svg";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

type CameraItem = {
  id: string;
  name: string;
  source: string;
  streamUrl?: string;
};

type CameraListResponse = {
  count: number;
  cameras: CameraItem[];
};

export default function DualYoloViewer() {
  const [cameras, setCameras] = useState<CameraItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  const gridClass = useMemo(() => {
    const n = cameras.length;
    if (n <= 1) return "grid-cols-1";
    if (n === 2) return "grid-cols-1 md:grid-cols-2";
    if (n === 3) return "grid-cols-1 md:grid-cols-2 xl:grid-cols-3";
    if (n <= 4) return "grid-cols-1 md:grid-cols-2 xl:grid-cols-2";
    if (n <= 6) return "grid-cols-1 md:grid-cols-2 xl:grid-cols-3";
    return "grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4";
  }, [cameras.length]);

  const fetchCameras = async () => {
    try {
      setLoading(true);
      setError("");

      const res = await fetch(`${BASE_URL}/yolo/cameras`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data: CameraListResponse = await res.json();
      setCameras(Array.isArray(data.cameras) ? data.cameras : []);
    } catch (err) {
      console.error(err);
      setError("無法取得鏡頭資料，請確認 FastAPI 是否有啟動 /cameras API");
      setCameras([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
  }, []);

  return (
    <div className="relative mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="absolute inset-0 z-0 overflow-hidden">
        <img
          src={workspaceOverlay}
          alt=""
          className="pointer-events-none absolute inset-0 z-[1] h-full w-full select-none object-cover"
        />
        <img
          src={dashboardBg}
          alt=""
          className="pointer-events-none absolute inset-0 z-[2] h-full w-full select-none object-cover object-center"
        />
        <div className="absolute inset-0 z-[3] bg-white/40 backdrop-blur-[1px]" />
      </div>

      <div className="relative z-10 mb-6 rounded-3xl border border-white/60 bg-white/70 p-4 shadow-xl shadow-slate-200/60 backdrop-blur-xl">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              動態鏡頭顯示
            </h1>
            <p className="mt-2 text-sm text-slate-600">
              從 FastAPI 自動取得鏡頭清單，幾個鏡頭就顯示幾個畫面框。
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={fetchCameras}
              className="rounded-xl bg-lime-400 px-4 py-2 text-sm font-semibold text-black shadow"
            >
              重新抓取鏡頭
            </button>
            <div className="rounded-xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700">
              目前鏡頭數：{cameras.length}
            </div>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="relative z-10 rounded-3xl border border-white/60 bg-white/80 p-10 text-center shadow-xl backdrop-blur-xl">
          <p className="text-slate-600">讀取鏡頭中...</p>
        </div>
      ) : error ? (
        <div className="relative z-10 rounded-3xl border border-red-200 bg-red-50/90 p-10 text-center shadow-xl backdrop-blur-xl">
          <p className="font-semibold text-red-600">{error}</p>
        </div>
      ) : cameras.length === 0 ? (
        <div className="relative z-10 rounded-3xl border border-slate-200 bg-white/80 p-10 text-center shadow-xl backdrop-blur-xl">
          <p className="text-slate-600">目前沒有可用鏡頭</p>
        </div>
      ) : (
        <div className={`relative z-10 grid gap-6 ${gridClass}`}>
          {cameras.map((camera) => (
            <div
              key={camera.id}
              className="overflow-hidden rounded-3xl border border-white/60 bg-white/80 shadow-xl backdrop-blur-xl"
            >
              <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
                <div>
                  <h2 className="text-base font-semibold text-slate-800">
                    {camera.name}
                  </h2>
                  <p className="text-xs text-slate-500">Source: {camera.source}</p>
                </div>

                <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">
                  在線中
                </span>
              </div>

              <div className="flex aspect-video min-h-[240px] items-center justify-center bg-slate-900 text-slate-300">
                {camera.streamUrl ? (
                  <img
                    src={camera.streamUrl}
                    alt={camera.name}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="text-center">
                    <p className="text-lg font-semibold">{camera.name}</p>
                    <p className="mt-2 text-sm text-slate-400">這裡會顯示鏡頭畫面</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}