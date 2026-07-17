import { useLanguage } from "@/i18n/LanguageProvider";
import type { Language } from "@/i18n/LanguageProvider";

const LABELS: Record<Language, string> = { zh: "中文", en: "EN" };

export function LanguageSwitcher() {
  const { lang, setLanguage } = useLanguage();

  const next = lang === "zh" ? "en" : "zh";

  return (
    <button
      onClick={() => setLanguage(next)}
      className="flex h-8 items-center rounded-md border border-border bg-surface px-2.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-surface-elevated hover:text-foreground"
      aria-label={`Switch language to ${next === "zh" ? "Simplified Chinese" : "English"}`}
    >
      {LABELS[lang]}
    </button>
  );
}
