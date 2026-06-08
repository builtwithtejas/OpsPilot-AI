"use client";

import { useState, useCallback } from "react";
import type { ToastItem, ToastType } from "@/components/Toast";

export function useToast() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const add = useCallback((message: string, type: ToastType = "success", duration = 3500) => {
    const id = crypto.randomUUID(); // M FIX: use cryptographically unique IDs instead of Math.random()
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
  }, []);

  const remove = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return { toasts, add, remove };
}
