"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import clsx from "clsx";

export function ThemeToggle() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const stored = document.documentElement.getAttribute("data-theme");
    if (stored === "light") setTheme("light");
  }, []);

  function toggle() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    if (next === "dark") {
      document.documentElement.removeAttribute("data-theme");
    } else {
      document.documentElement.setAttribute("data-theme", "light");
    }
    localStorage.setItem("lumi-theme", next);
  }

  return (
    <button
      onClick={toggle}
      className={clsx(
        "flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-xs text-[var(--text-muted)] transition-all hover:bg-[var(--bg-hover)] hover:text-[var(--text)]"
      )}
    >
      {theme === "dark" ? <Sun size={14} className="opacity-50" /> : <Moon size={14} className="opacity-50" />}
      {theme === "dark" ? "Light mode" : "Dark mode"}
    </button>
  );
}
