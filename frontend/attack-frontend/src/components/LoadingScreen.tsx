const LoadingScreen = () => {
  return (
    <div className="fixed inset-0 z-[9999] overflow-hidden bg-slate-950">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(163,230,53,0.18),_transparent_35%),radial-gradient(circle_at_bottom,_rgba(255,255,255,0.08),_transparent_30%)]" />

      <div className="relative flex h-full w-full items-center justify-center px-6">
        <div className="flex flex-col items-center">
          <div className="relative mb-8">
            <div className="absolute inset-0 scale-150 rounded-full bg-lime-400/20 blur-3xl animate-pulse" />

            <div className="relative flex h-28 w-28 items-center justify-center rounded-full bg-gradient-to-br from-lime-300 via-lime-400 to-emerald-400 shadow-[0_0_80px_rgba(163,230,53,0.35)] animate-bounce">
              <div className="absolute top-7 flex items-center gap-4">
                <span className="h-2.5 w-2.5 rounded-full bg-slate-900" />
                <span className="h-2.5 w-2.5 rounded-full bg-slate-900" />
              </div>

              <div className="absolute bottom-7 h-3 w-8 rounded-full border-b-4 border-slate-900" />

              <div className="absolute -right-1 -top-1 h-5 w-5 rounded-full bg-white/70 animate-ping" />
            </div>

            <div className="absolute left-1/2 top-[112%] h-4 w-20 -translate-x-1/2 rounded-full bg-black/30 blur-md" />
          </div>

          <h2 className="text-xl font-bold tracking-wide text-white">
            載入中...
          </h2>

          <p className="mt-2 text-center text-sm leading-6 text-slate-300">
            正在喚醒你的智慧偵測小幫手 OBELISK
          </p>

          <div className="mt-6 flex items-end gap-2">
            <span className="h-3 w-3 animate-bounce rounded-full bg-lime-300 [animation-delay:0ms]" />
            <span className="h-3 w-3 animate-bounce rounded-full bg-lime-400 [animation-delay:150ms]" />
            <span className="h-3 w-3 animate-bounce rounded-full bg-emerald-300 [animation-delay:300ms]" />
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoadingScreen
