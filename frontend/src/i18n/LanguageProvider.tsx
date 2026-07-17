import {
  createContext,
  useContext,
  useEffect,
  type ReactNode,
} from "react";
import type { Translations } from "./translations";
import zh from "./zh";

interface LanguageContextValue {
  t: Translations;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    document.documentElement.lang = "zh-CN";
  }, []);

  return (
    <LanguageContext.Provider value={{ t: zh }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useT(): Translations {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error("useT must be used within a LanguageProvider");
  }
  return ctx.t;
}
