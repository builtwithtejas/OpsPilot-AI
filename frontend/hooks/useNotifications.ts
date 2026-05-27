"use client";
import { useState, useEffect } from "react";
import type { Incident, Notification } from "@/types";
import { severityColor } from "@/utils/formatters";

export function useNotifications(incidents: Incident[]) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (incidents.length === 0) return;
    const notifs: Notification[] = incidents.slice(0, 8).map(inc => ({
      id: String(inc.id),
      title: inc.title,
      message: `${inc.severity} severity — ${inc.status}`,
      severity: inc.severity,
      timestamp: inc.created_at,
      read: inc.status === "Resolved" || inc.status === "Closed",
    }));
    setNotifications(notifs);
  }, [incidents]);

  const unreadCount = notifications.filter(n => !n.read).length;

  const markAllRead = () => setNotifications(prev => prev.map(n => ({ ...n, read: true })));

  return { notifications, unreadCount, open, setOpen, markAllRead };
}
