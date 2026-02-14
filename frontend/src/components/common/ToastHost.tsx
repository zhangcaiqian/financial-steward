import { useEffect, useRef, useState } from "react";

type ToastState = {
  id: number;
  message: string;
};

const EVENT_NAME = "app:api-error";
const AUTO_HIDE_MS = 3200;

export default function ToastHost() {
  const [toast, setToast] = useState<ToastState | null>(null);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent).detail as { message?: string } | undefined;
      const message = detail?.message;
      if (!message) return;
      setToast({ id: Date.now(), message });
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
      }
      timerRef.current = window.setTimeout(() => setToast(null), AUTO_HIDE_MS);
    };

    window.addEventListener(EVENT_NAME, handler as EventListener);
    return () => {
      window.removeEventListener(EVENT_NAME, handler as EventListener);
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
      }
    };
  }, []);

  if (!toast) return null;

  return (
    <div className="toast-host" role="status" aria-live="polite">
      <div className="toast toast-error">
        <span>{toast.message}</span>
        <button aria-label="关闭" onClick={() => setToast(null)}>
          <i className="fa-solid fa-xmark" />
        </button>
      </div>
    </div>
  );
}
