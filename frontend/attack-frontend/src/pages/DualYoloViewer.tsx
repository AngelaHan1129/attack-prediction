import { useState } from "react";
import YoloViewer from "../components/YoloViewer";
import DualCameraViewer from "../components/DualCameraViewer";


import dashboardBg from '../assets/hlogo_al.png'
import workspaceOverlay from '../assets/work-space.svg'

type ViewMode = "single" | "dual";

export default function DualYoloViewer() {
  const [mode, setMode] = useState<ViewMode>("single");

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      
    <div className="absolute inset-0 z-0 overflow-hidden">
      <img
        src={workspaceOverlay}
        alt="workspace overlay"
        className="pointer-events-none absolute inset-0 z-[1] h-full w-full select-none object-cover"
      />
      <img
        src={dashboardBg}
        alt="dashboard background"
        className="pointer-events-none absolute inset-0 z-[2] h-full w-full select-none object-cover object-center"
      />
      <div className="absolute inset-0 z-[3] bg-white/40 backdrop-blur-[1px]" />
    </div>
      <div className="mb-6 rounded-3xl border border-white/60 bg-white/70 p-4 shadow-xl shadow-slate-200/60 backdrop-blur-xl">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              鏡頭模式切換
            </h1>
            <p className="mt-2 text-sm text-slate-600">
              可在單鏡頭與雙鏡頭模式之間切換，依需求選擇鏡頭方式。
            </p>
          </div>

          <div className="inline-flex rounded-2xl border border-slate-200 bg-slate-100 p-1 shadow-inner">
            <button
              onClick={() => setMode("single")}
              className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${
                mode === "single"
                  ? "bg-lime-400 text-black shadow"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              單鏡頭
            </button>

            <button
              onClick={() => setMode("dual")}
              className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${
                mode === "dual"
                  ? "bg-lime-400 text-black shadow"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              雙鏡頭
            </button>
          </div>
        </div>
      </div>

      <div className="rounded-3xl">
        {mode === "single" ? <YoloViewer /> : <DualCameraViewer />}
      </div>
    </div>
  );
}