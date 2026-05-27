"use client";

import { useState } from "react";

export function useClipboard(resetAfterMs = 2000) {
  const [copied, setCopied] = useState<string | null>(null);

  function copy(text: string) {
    void navigator.clipboard.writeText(text).then(() => {
      setCopied(text);
      setTimeout(() => setCopied(null), resetAfterMs);
    });
  }

  return { copied, copy };
}
