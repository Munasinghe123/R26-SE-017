import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from "react";
import { useSelector } from "react-redux";
import api from "../api/api";

const NotificationContext = createContext(null);

export function NotificationProvider({ children }) {
  const currentUser = useSelector((state) => state.user.userInfo);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [toastNotification, setToastNotification] = useState(null);
  const [loading, setLoading] = useState(false);

  // Keep track of which notification IDs have already triggered an in-app toast
  const alertedIdsRef = useRef(new Set());
  // Prevent alert on the very first historical load, unless it's recent unread
  const isFirstLoadRef = useRef(true);

  const fetchNotifications = useCallback(async () => {
    if (!currentUser?.id) {
      setNotifications([]);
      setUnreadCount(0);
      return;
    }

    try {
      const response = await api.get(`/notifications/user/${currentUser.id}`);
      const list = response.data?.notifications || [];
      const count = response.data?.unread_count || 0;

      setNotifications(list);
      setUnreadCount(count);

      // Check for any unread notifications that haven't been toasted yet
      const unreadList = list.filter((n) => !n.is_read);

      if (unreadList.length > 0) {
        // Find the newest unread notification not yet alerted
        const newestUnread = unreadList.find((n) => !alertedIdsRef.current.has(n.id));

        if (newestUnread) {
          alertedIdsRef.current.add(newestUnread.id);
          setToastNotification(newestUnread);

          // Trigger a custom event in case active dashboards want to react
          window.dispatchEvent(
            new CustomEvent("sysdesign:new-notification", { detail: newestUnread })
          );
        }
      }

      isFirstLoadRef.current = false;
    } catch (error) {
      console.warn("Failed to fetch notifications:", error);
    }
  }, [currentUser?.id]);

  // Polling every 5 seconds for in-app notifications
  useEffect(() => {
    if (!currentUser?.id) return;

    fetchNotifications();

    const interval = setInterval(() => {
      fetchNotifications();
    }, 5000);

    return () => clearInterval(interval);
  }, [currentUser?.id, fetchNotifications]);

  // Mark single notification as read
  const markAsRead = async (notificationId) => {
    try {
      await api.patch(`/notifications/${notificationId}/read`);
    } catch (err) {
      // Fallback try post if patch fails
      try {
        await api.post(`/notifications/${notificationId}/read`);
      } catch (e) {
        console.warn("Mark read failed:", e);
      }
    }

    setNotifications((prev) =>
      prev.map((n) => (n.id === notificationId ? { ...n, is_read: true } : n))
    );
    setUnreadCount((prev) => Math.max(0, prev - 1));

    if (toastNotification?.id === notificationId) {
      setToastNotification(null);
    }
  };

  // Mark all notifications as read
  const markAllAsRead = async () => {
    if (!currentUser?.id) return;
    try {
      await api.post(`/notifications/user/${currentUser.id}/read-all`);
    } catch (err) {
      console.warn("Mark all read failed:", err);
    }

    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadCount(0);
    setToastNotification(null);
  };

  // When user clicks the notification: mark as read, then refresh the page
  const handleNotificationClick = async (notification) => {
    if (!notification) return;

    // 1. Mark as read on the backend
    try {
      await api.patch(`/notifications/${notification.id}/read`);
    } catch (err) {
      console.warn("Could not mark notification read before refresh:", err);
    }

    // 2. Dismiss the toast
    setToastNotification(null);

    // 3. Refresh the page as requested ("when the client clicks the notification the page refreshes")
    if (notification.project_id) {
      const isReview = notification.type === "REVIEW_REQUIREMENTS";
      const targetPath = `/project-dashboard/${notification.project_id}`;
      const targetUrl = isReview ? `${targetPath}?review=true` : targetPath;

      if (window.location.pathname + window.location.search === targetUrl) {
        window.location.reload();
      } else {
        window.location.href = targetUrl;
      }
    } else {
      window.location.reload();
    }
  };

  const dismissToast = () => {
    setToastNotification(null);
  };

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        toastNotification,
        markAsRead,
        markAllAsRead,
        handleNotificationClick,
        dismissToast,
        refetchNotifications: fetchNotifications,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error("useNotifications must be used within a NotificationProvider");
  }
  return context;
}
