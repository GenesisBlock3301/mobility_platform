// Marks a form label as required (red asterisk) or optional (muted text).
// Screen readers hear "(required)" instead of "star".

export type Marker = "required" | "optional";

export function FieldMarker({ marker }: { marker?: Marker }) {
  if (marker === "required") {
    return (
      <>
        <span aria-hidden="true" className="ml-0.5 text-stop">
          *
        </span>
        <span className="sr-only"> (required)</span>
      </>
    );
  }
  if (marker === "optional") {
    return <span className="font-normal text-muted"> (optional)</span>;
  }
  return null;
}
