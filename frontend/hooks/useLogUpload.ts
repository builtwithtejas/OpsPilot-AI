"use client";

import { useState } from "react";
import { analyzeLogFile } from "@/lib/api";
import type { AnalyzeResult } from "@/types";

interface State {
  result: AnalyzeResult | null;
  loading: boolean;
  error: string | null;
}

export function useLogUpload() {
  const [state, setState] = useState<State>({ result: null, loading: false, error: null });

  async function upload(file: File) {
    setState({ result: null, loading: true, error: null });
    try {
      const result = await analyzeLogFile(file);
      setState({ result, loading: false, error: null });
    } catch (err) {
      setState({ result: null, loading: false, error: err instanceof Error ? err.message : "Upload failed" });
    }
  }

  return { ...state, upload };
}
