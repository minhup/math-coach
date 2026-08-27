"use client";

import Image from "next/image";
import { ChangeEvent, useEffect, useRef, useState } from "react";

import { ApiError, completeUpload, presignUpload, putSignedUpload, type Upload } from "../lib/api";
import { formatFileSize, solutionImageType, validateSolutionImage } from "../lib/file-validation";

type UploadPhase = "idle" | "selected" | "presigning" | "uploading" | "verifying" | "success";

type UploadWorkspaceProps = {
  onContinue?: (upload: Upload) => void;
};

export function UploadWorkspace({ onContinue }: UploadWorkspaceProps = {}) {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [phase, setPhase] = useState<UploadPhase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [completedUpload, setCompletedUpload] = useState<Upload | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (previewUrl === null) {
      return;
    }
    return () => URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  function selectFile(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    setCompletedUpload(null);
    if (selected === null) {
      setFile(null);
      setPreviewUrl(null);
      setPhase("idle");
      return;
    }
    const validationError = validateSolutionImage(selected);
    if (validationError !== null) {
      setFile(null);
      setPreviewUrl(null);
      setError(validationError);
      setPhase("idle");
      event.target.value = "";
      return;
    }
    setError(null);
    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
    setPhase("selected");
  }

  function chooseReplacement() {
    inputRef.current?.click();
  }

  async function upload() {
    if (file === null) {
      return;
    }
    setError(null);
    try {
      const contentType = solutionImageType(file.type);
      if (contentType === null) {
        setError("Choose a JPEG, PNG, or WebP image.");
        return;
      }
      setPhase("presigning");
      const signed = await presignUpload({
        contentType,
        fileName: file.name,
        sizeBytes: file.size,
      });
      setPhase("uploading");
      await putSignedUpload(signed.uploadUrl, file);
      setPhase("verifying");
      const completed = await completeUpload(signed.uploadId);
      setCompletedUpload(completed);
      setPhase("success");
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "The image could not be uploaded. Check the connection and retry.",
      );
      setPhase("selected");
    }
  }

  const busy = phase === "presigning" || phase === "uploading" || phase === "verifying";
  const progressLabel =
    phase === "presigning"
      ? "Preparing a secure upload…"
      : phase === "uploading"
        ? "Uploading your image…"
        : "Verifying the stored image…";

  return (
    <section className="upload-panel" aria-labelledby="upload-title">
      <div className="upload-heading">
        <div>
          <p className="eyebrow">Step 1 of 4</p>
          <h2 id="upload-title">Add your solution</h2>
          <p>Use an existing photo for this internal foundation.</p>
        </div>
        <span className="safe-badge">Synthetic only</span>
      </div>

      <input
        accept="image/jpeg,image/png,image/webp"
        className="file-input"
        id="solution-image"
        onChange={selectFile}
        ref={inputRef}
        type="file"
      />

      {file === null || previewUrl === null ? (
        <div className="empty-upload">
          <div className="empty-upload-inner">
            <div className="paper-icon" aria-hidden="true">
              x²
            </div>
            <h3>Choose a paper-solution image</h3>
            <p>Keep the page flat, well lit, and fully visible. Camera capture comes later.</p>
            <label className="file-button" htmlFor="solution-image" tabIndex={0}>
              Choose image
            </label>
            <p className="file-help">JPEG, PNG, or WebP · up to 10 MB</p>
          </div>
        </div>
      ) : (
        <div className="preview-grid">
          <div className="preview-frame">
            <Image
              alt="Preview of the selected paper solution"
              className="preview-image"
              fill
              sizes="(min-width: 900px) 45vw, 90vw"
              src={previewUrl}
              unoptimized
            />
          </div>
          <div className="preview-details">
            <p className="file-name" title={file.name}>
              {file.name}
            </p>
            <p className="file-meta">
              {file.type.replace("image/", "").toUpperCase()} · {formatFileSize(file.size)}
            </p>
            <div className="preview-actions">
              <button className="primary-button" disabled={busy} onClick={upload} type="button">
                {phase === "success" ? "Upload again" : error ? "Retry upload" : "Upload solution"}
              </button>
              <button
                className="secondary-button"
                disabled={busy}
                onClick={chooseReplacement}
                type="button"
              >
                Choose a different image
              </button>
            </div>
            {busy ? (
              <div className="progress-card" aria-live="polite">
                <span className="spinner" aria-hidden="true" />
                <strong>{progressLabel}</strong>
              </div>
            ) : null}
            {phase === "success" && completedUpload ? (
              <div className="success-card" aria-live="polite">
                <strong>Image received and verified</strong>
                <span>Ready for validated server-side transcription.</span>
                {onContinue ? (
                  <button
                    className="secondary-button"
                    onClick={() => onContinue(completedUpload)}
                    type="button"
                  >
                    Use this upload
                  </button>
                ) : null}
              </div>
            ) : null}
          </div>
        </div>
      )}
      {error ? (
        <p className="upload-error" role="alert">
          {error}
        </p>
      ) : null}
    </section>
  );
}
