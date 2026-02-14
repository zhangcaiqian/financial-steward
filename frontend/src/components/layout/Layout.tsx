import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import ToastHost from "../common/ToastHost";

const STORAGE_KEY = "fs-sidebar-collapsed";

export default function Layout() {
  const [collapsed, setCollapsed] = useState(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === "true";
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(collapsed));
  }, [collapsed]);

  return (
    <div className="app-shell">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((prev) => !prev)} />
      <main className="main">
        <div className="content">
          <Outlet />
        </div>
      </main>
      <ToastHost />
    </div>
  );
}
