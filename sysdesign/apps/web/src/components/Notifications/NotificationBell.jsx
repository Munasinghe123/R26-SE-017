import React, { useState, useRef, useEffect } from "react";
import { Bell, CheckCheck, Sparkles, FolderGit2, Clock, RefreshCw } from "lucide-react";
import { useNotifications } from "../../context/NotificationContext";

export default function NotificationBell({
  placement = "bottom-right",
  isCollapsed = false,
  showLabel = false,
  className = "",
}) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);

  const {
    notifications,
    unreadCount,
    markAllAsRead,
    handleNotificationClick,
  } = useNotifications();

  // Close dropdown on outside click
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleOutsideClick);
    }
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [isOpen]);

  const formatTime = (isoString) => {
    if (!isoString) return "";
    try {
      const date = new Date(isoString);
      const now = new Date();
      const diffSecs = Math.floor((now - date) / 1000);

      if (diffSecs < 60) return "Just now";
      if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m ago`;
      if (diffSecs < 86400) return `${Math.floor(diffSecs / 3600)}h ago`;
      return date.toLocaleDateString();
    } catch {
      return "";
    }
  };

  return (
    <div className={`relative ${showLabel && !isCollapsed ? "w-full" : "inline-block"}`} ref={containerRef}>
      {/* Bell Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        title="Notifications"
        aria-label="View notifications"
        className={
          showLabel
            ? `flex items-center gap-3 transition-all duration-300 cursor-pointer ${
                isCollapsed
                  ? "mx-auto h-10 w-10 justify-center p-0 rounded-xl text-gray-400 hover:bg-white/5 hover:text-white"
                  : "w-full px-3.5 py-2.5 text-sm rounded-xl text-gray-400 hover:bg-white/5 hover:text-white"
              } ${className}`
            : `relative flex items-center justify-center transition-all duration-300 cursor-pointer ${
                isCollapsed
                  ? "h-10 w-10 rounded-xl text-gray-400 hover:bg-white/5 hover:text-white"
                  : "h-10 w-10 rounded-full border border-cyan-400/40 bg-white/5 backdrop-blur-md text-white hover:border-cyan-300 hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]"
              } ${className}`
        }
      >
        <div className="relative shrink-0 flex items-center justify-center">
          <Bell size={18} className={unreadCount > 0 ? "text-cyan-300" : "text-gray-400"} />

          {(!showLabel || isCollapsed) && unreadCount > 0 && (
            <span className="absolute -top-1.5 -right-1.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 px-1 text-[9px] font-bold text-black shadow-[0_0_8px_rgba(34,211,238,0.7)]">
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          )}
        </div>

        {showLabel && !isCollapsed && (
          <span className="text-gray-300 font-medium">Notifications</span>
        )}

        {showLabel && !isCollapsed && unreadCount > 0 && (
          <span className="ml-auto flex h-5 min-w-[20px] items-center justify-center rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 px-1.5 text-[10px] font-bold text-black shadow-[0_0_10px_rgba(34,211,238,0.6)] animate-pulse">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Notifications Dropdown */}
      {isOpen && (
        <div
          className={`absolute z-50 w-[calc(100vw-2rem)] sm:w-80 md:w-96 max-w-[380px] overflow-hidden rounded-2xl border border-cyan-400/30 bg-[#0B0F1E]/95 shadow-[0_0_40px_rgba(0,0,0,0.8)] backdrop-blur-xl animate-in fade-in zoom-in-95 duration-200 ${
            placement === "bottom-left"
              ? "left-0 top-full mt-2"
              : placement === "top-left"
              ? `${isCollapsed ? "left-12" : "left-0"} bottom-full mb-3`
              : placement === "top-right"
              ? "right-0 bottom-full mb-3"
              : "right-0 top-full mt-2"
          }`}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-white/10 px-4 py-3 bg-gradient-to-r from-cyan-950/40 via-transparent to-transparent">
            <div className="flex items-center gap-2">
              <span
                style={{ fontFamily: "Orbitron, sans-serif" }}
                className="text-xs font-bold uppercase tracking-wider text-white"
              >
                Notifications
              </span>
              {unreadCount > 0 && (
                <span className="rounded-full bg-cyan-400/20 border border-cyan-400/30 px-2 py-0.5 text-[10px] font-semibold text-cyan-300">
                  {unreadCount} new
                </span>
              )}
            </div>

            {unreadCount > 0 && (
              <button
                type="button"
                onClick={markAllAsRead}
                className="flex items-center gap-1 text-[11px] font-medium text-gray-400 hover:text-cyan-300 transition cursor-pointer"
              >
                <CheckCheck size={13} />
                <span>Mark all read</span>
              </button>
            )}
          </div>

          {/* List */}
          <div className="max-h-80 overflow-y-auto divide-y divide-white/5 custom-scrollbar">
            {notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 px-4 text-center text-gray-400">
                <Bell size={28} className="text-gray-600 mb-2 opacity-50" />
                <p className="text-xs font-semibold text-gray-300">No notifications yet</p>
                <p className="text-[11px] text-gray-500 mt-1">
                  You will be notified when assigned to projects
                </p>
              </div>
            ) : (
              notifications.map((item) => (
                <div
                  key={item.id}
                  onClick={() => {
                    handleNotificationClick(item);
                    setIsOpen(false);
                  }}
                  className={`group relative flex items-start gap-3 p-3.5 transition cursor-pointer hover:bg-cyan-500/10 ${
                    !item.is_read ? "bg-cyan-950/20" : "bg-transparent opacity-80 hover:opacity-100"
                  }`}
                >
                  {/* Status Indicator */}
                  <div className="mt-1 shrink-0">
                    {!item.is_read ? (
                      <span className="flex h-2.5 w-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
                    ) : (
                      <FolderGit2 size={14} className="text-gray-500" />
                    )}
                  </div>

                  {/* Notification Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-xs font-bold text-white group-hover:text-cyan-200 truncate">
                        {item.title}
                      </p>
                      <span className="flex items-center gap-1 text-[10px] text-gray-500 shrink-0">
                        <Clock size={10} />
                        {formatTime(item.created_at)}
                      </span>
                    </div>

                    <p className="mt-1 text-[11px] leading-relaxed text-gray-300 line-clamp-2">
                      {item.message}
                    </p>

                    <div className="mt-2 flex items-center gap-1.5 text-[10px] font-semibold text-cyan-400 group-hover:underline">
                      <RefreshCw size={10} />
                      <span>
                        {item.type === "REVIEW_REQUIREMENTS"
                          ? "Click to review requirements"
                          : item.type === "CLIENT_REVIEW_COMPLETED"
                          ? "Click to view project dashboard"
                          : "Click to refresh and view"}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
