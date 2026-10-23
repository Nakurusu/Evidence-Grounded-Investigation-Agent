import { Sun, Moon, Sparkles } from "lucide-react";
import { useTheme } from "@/hooks/useTheme";
import { Link } from "react-router-dom";

export function Header() {
  const { theme, toggle } = useTheme();

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="flex h-14 items-center justify-between px-4 sm:px-6">
        <Link
          to="/"
          className="flex items-center gap-2 text-sm font-semibold text-foreground no-underline transition-opacity hover:opacity-80"
        >
          <Sparkles className="h-4 w-4 shrink-0 text-accent" />
          <span className="hidden sm:inline">Evidence-Grounded Agent</span>
          <span className="sm:hidden">EGIA</span>
        </Link>

        <div className="flex items-center gap-2">
          <button
            onClick={toggle}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border bg-surface text-muted-foreground transition-colors hover:bg-surface-elevated hover:text-foreground"
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
