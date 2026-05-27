"use client";

import { UploadCloud } from "lucide-react";
import { useDropzone } from "react-dropzone";

interface Props {
  onFile: (file: File) => void;
  loading: boolean;
}

export default function UploadBox({ onFile, loading }: Props) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (files) => { if (files[0]) onFile(files[0]); },
    multiple: false,
    accept: { "text/plain": [".log", ".txt"] },
    maxSize: 10 * 1024 * 1024,
    disabled: loading,
  });

  return (
    <div
      {...getRootProps()}
      style={{
        width: "100%",
        minHeight: "220px",
        borderRadius: "24px",
        border: isDragActive ? "2px solid #33ff88" : "2px dashed rgba(0,255,170,0.4)",
        background: isDragActive ? "rgba(0,255,170,0.07)" : "rgba(10,20,15,0.45)",
        backdropFilter: "blur(18px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        gap: "14px",
        cursor: loading ? "not-allowed" : "pointer",
        transition: "0.25s ease",
        opacity: loading ? 0.6 : 1,
      }}
    >
      <input {...getInputProps()} />

      <div
        style={{
          width: "72px",
          height: "72px",
          borderRadius: "50%",
          background: "linear-gradient(135deg,#33ff88,#00c3ff)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <UploadCloud size={34} color="black" />
      </div>

      <div
        style={{
          fontSize: "28px",
          fontWeight: 800,
          background: "linear-gradient(to right,#33ff88,#00c3ff)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}
      >
        {loading ? "Analyzing..." : "Upload CI/CD Logs"}
      </div>

      <div style={{ color: "#888", fontSize: "16px", textAlign: "center" }}>
        {isDragActive ? "Drop it!" : "Drag & drop .log or .txt — max 10 MB"}
      </div>
    </div>
  );
}
