import { Sparkles } from "lucide-react";
import { useT } from "@/i18n/LanguageProvider";
import { UploadZone } from "@/components/upload/UploadZone";

export function HomePage() {
  const t = useT();

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 py-16 sm:px-6 sm:py-20">
      <div className="flex w-full max-w-2xl flex-col items-center text-center animate-fade-in">
        {/* Icon */}
        <div className="mb-6 sm:mb-8 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-muted sm:h-14 sm:w-14">
          <Sparkles className="h-6 w-6 text-accent sm:h-7 sm:w-7" />
        </div>

        {/* Heading */}
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground sm:mb-4 sm:text-5xl">
          {t.home.heading}
        </h1>

        {/* Subtitle */}
        <p className="mb-8 max-w-lg text-sm leading-relaxed text-muted-foreground sm:mb-12 sm:text-base">
          {t.home.subtitle}
        </p>

        {/* Upload zone */}
        <UploadZone />

        {/* Feature hints */}
        <div className="mt-16 grid grid-cols-1 gap-4 sm:mt-20 sm:grid-cols-3 sm:gap-6">
          {(
            [
              "signals",
              "evidence",
              "narrative",
            ] as (keyof typeof t.home.features)[]
          ).map((key) => {
            const f = t.home.features[key];
            return (
              <div
                key={key}
                className="rounded-lg border border-border bg-surface p-4 text-left sm:p-5"
              >
                <h3 className="mb-1 text-sm font-semibold text-foreground">
                  {f.title}
                </h3>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {f.desc}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
