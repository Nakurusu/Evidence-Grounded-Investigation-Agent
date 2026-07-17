import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { Translations } from "./translations";
import zh from "./zh";
import en from "./en";

export type Language = "zh" | "en";

const TRANSLATIONS: Record<Language, Translations> = { zh, en };
const STORAGE_KEY = "ida-lang";

function getInitialLanguage(): Language {
  if (typeof window === "undefined") return "zh";
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "zh" || stored === "en") return stored;
  return "zh";
}

interface LanguageContextValue {
  lang: Language;
  t: Translations;
  setLanguage: (lang: Language) => void;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Language>(getInitialLanguage);

  const setLanguage = useCallback((next: Language) => {
    setLang(next);
    localStorage.setItem(STORAGE_KEY, next);
  }, []);

  // Sync <html lang="..."> for accessibility
  useEffect(() => {
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
  }, [lang]);

  const value: LanguageContextValue = {
    lang,
    t: TRANSLATIONS[lang],
    setLanguage,
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

/** Hook: returns the translations object for the current language. */
export function useT(): Translations {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error("useT must be used within a LanguageProvider");
  }
  return ctx.t;
}

/** Hook: returns full language context (lang + setter + translations). */
export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return ctx;
}
