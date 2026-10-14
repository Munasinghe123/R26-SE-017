import React, { useEffect } from "react";
import { Bell, Sparkles, X, ArrowRight, RefreshCw } from "lucide-react";
import { useNotifications } from "../../context/NotificationContext";

export default function NotificationToast() {
  const { toastNotification, handleNotificationClick, dismissToast } = useNotifications();

  useEffect(() => {
    if (!toastNotification) return;

    // Auto dismiss after 14 seconds if user doesn't click
    const timer = setTimeout(() => {
      dismissToast();
    }, 14000);

    return () => clearTimeout(timer);
  }, [toastNotification, dismissToast]);

  if (!toastNotification) return null;

  return (
    <div
      className="fixed top-6 right-6 z-[9999] max-w-md w-[calc(100vw-3rem)] animate-in slide-in-from-top-5 fade-in duration-300"
      role="alert"
      aria-live="assertive"
    >
      <div
        onClick={() => handleNotificationClick(toastNotification)}
        className="group relative cursor-pointer overflow-hidden rounded-2xl border border-cyan-400/50 bg-[#0B0F1E]/95 p-5 shadow-[0_0_35px_rgba(34,211,238,0.35)] backdrop-blur-xl transition-all duration-300 hover:border-cyan-300 hover:shadow-[0_0_50px_rgba(34,211,238,0.55)] hover:scale-[1.01]"
      >
        {/* Glowing backdrop streak */}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-blue-500/10 to-transparent opacity-80" />
        <div className="pointer-events-none absolute -top-10 -right-10 h-28 w-28 rounded-full bg-cyan-500/20 blur-2xl group-hover:bg-cyan-400/30 transition-all duration-500" />

        <div className="relative z-10 flex items-start gap-4">
          {/* Pulsing Bell Icon */}
          <div className="relative mt-0.5 flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-cyan-400/40 bg-cyan-950/70 text-cyan-300 shadow-[0_0_15px_rgba(34,211,238,0.3)]">
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-400" />
            </span>
            <Bell size={20} className="animate-bounce" />
          </div>

          {/* Text Content */}
          <div className="flex-1 min-w-0 pr-6">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 rounded-full border border-cyan-400/40 bg-cyan-400/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-cyan-300">
                <Sparkles size={10} /> In-App Notification
              </span>
            </div>

            <h4
              style={{ fontFamily: "Orbitron, sans-serif" }}
              className="mt-1.5 text-sm font-bold text-white tracking-wide truncate group-hover:text-cyan-200 transition-colors"
            >
              {toastNotification.title || "New Project Assigned"}
            </h4>

            <p className="mt-1 text-xs leading-relaxed text-gray-300 line-clamp-2">
              {toastNotification.message}
            </p>

            {/* Click to action prompt */}
            <div className="mt-3 flex items-center gap-2 text-xs font-semibold text-cyan-300 group-hover:text-white transition-colors">
              <RefreshCw size={13} className="animate-spin text-cyan-400" style={{ animationDuration: "3s" }} />
              <span>
                {toastNotification.type === "REVIEW_REQUIREMENTS"
                  ? "Click to review requirements"
                  : toastNotification.type === "CLIENT_REVIEW_COMPLETED"
                  ? "Click to view project dashboard"
                  : "Click to refresh and view project"}
              </span>
              <ArrowRight size={13} className="group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Dismiss button */}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              dismissToast();
            }}
            className="absolute top-3 right-3 rounded-lg p-1.5 text-gray-400 hover:text-white hover:bg-white/10 transition cursor-pointer"
            aria-label="Dismiss notification"
          >
            <X size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
