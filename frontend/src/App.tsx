import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "@/hooks/useTheme";
import { LanguageProvider } from "@/i18n/LanguageProvider";
import { Layout } from "@/components/layout/Layout";
import { HomePage } from "@/pages/HomePage";
import { InvestigationPage } from "@/pages/InvestigationPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <LanguageProvider>
        <ThemeProvider>
          <BrowserRouter>
            <Routes>
              <Route element={<Layout />}>
                <Route index element={<HomePage />} />
                <Route
                  path="investigation/:taskId"
                  element={<InvestigationPage />}
                />
                <Route path="*" element={<NotFoundPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </ThemeProvider>
      </LanguageProvider>
    </QueryClientProvider>
  );
}
