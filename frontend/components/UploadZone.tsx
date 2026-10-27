"use client";

import { useCallback, useRef, useState } from "react";

const MAX_BYTES = 10 * 1024 * 1024;
const ACCEPTED = ["image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"];

interface Props {
  onFile: (file: File, previewUrl: string) => void;
  disabled?: boolean;
}

export default function UploadZone({ onFile, disabled }: Props) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const cameraRef = useRef<HTMLInputElement>(null);

  const validateAndSend = useCallback(
    (file: File | undefined | null) => {
      setError(null);
      if (!file) return;
      if (!ACCEPTED.includes(file.type)) {
        setError("Unsupported format. Use JPEG, PNG, WebP, GIF or BMP.");
        return;
      }
      if (file.size > MAX_BYTES) {
        setError("Image is larger than 10 MB. Please choose a smaller file.");
        return;
      }
      onFile(file, URL.createObjectURL(file));
    },
    [onFile]
  );

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload a bird photograph"
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        onClick={() => !disabled && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (!disabled) validateAndSend(e.dataTransfer.files?.[0]);
        }}
        className={`relative rounded-2xl border-2 border-dashed p-10 sm:p-14 text-center cursor-pointer transition ${
          dragging
            ? "border-forest-500 bg-forest-500/5"
            : "border-forest-700/25 hover:border-forest-500 hover:bg-forest-700/[0.03]"
        } ${disabled ? "opacity-60 pointer-events-none" : ""}`}
      >
        <div className="text-5xl mb-3" aria-hidden>
          📷
        </div>
        <p className="font-serif text-xl text-forest-800">
          Drag &amp; drop a bird photo
        </p>
        <p className="text-sm text-stone-warm mt-1">
          or click to browse — JPEG, PNG, WebP up to 10&nbsp;MB
        </p>

        <div className="mt-5 flex items-center justify-center gap-3">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              inputRef.current?.click();
            }}
            className="rounded-lg bg-forest-700 px-4 py-2 text-ivory-50 text-sm hover:bg-forest-600 transition"
          >
            Choose file
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              cameraRef.current?.click();
            }}
            className="rounded-lg border border-forest-700/30 px-4 py-2 text-forest-700 text-sm hover:bg-forest-700/5 transition"
          >
            Use camera
          </button>
        </div>

        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED.join(",")}
          className="hidden"
          onChange={(e) => validateAndSend(e.target.files?.[0])}
        />
        <input
          ref={cameraRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={(e) => validateAndSend(e.target.files?.[0])}
        />
      </div>

      {error && (
        <p
          role="alert"
          className="mt-3 text-sm text-accent-clay bg-accent-clay/10 rounded-lg px-3 py-2"
        >
          {error}
        </p>
      )}
    </div>
  );
}
