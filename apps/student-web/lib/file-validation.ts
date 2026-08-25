export type SolutionImageType = "image/jpeg" | "image/png" | "image/webp";

const maximumBytes = 10 * 1024 * 1024;

export function solutionImageType(value: string): SolutionImageType | null {
  if (value === "image/jpeg" || value === "image/png" || value === "image/webp") {
    return value;
  }
  return null;
}

export function validateSolutionImage(file: File): string | null {
  if (solutionImageType(file.type) === null) {
    return "Choose a JPEG, PNG, or WebP image.";
  }
  if (file.size < 1) {
    return "The selected image is empty.";
  }
  if (file.size > maximumBytes) {
    return "Choose an image no larger than 10 MB.";
  }
  return null;
}

export function formatFileSize(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${Math.round(size / 1024)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}
