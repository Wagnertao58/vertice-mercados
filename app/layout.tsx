import type { Metadata } from "next";
import "./globals.css";
import "./phase1.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://vertice-mercados.wagnertao58.chatgpt.site"),
  title: "Vértice — Inteligência de Mercado",
  description: "Dashboard para análise de ativos brasileiros, americanos e BDRs.",
  openGraph: {
    title: "Vértice — Inteligência de Mercado",
    description: "Inteligência de mercado, risco e BDRs.",
    images: [{ url: "/og.png", width: 1792, height: 921, alt: "Vértice — Inteligência de mercado, risco e BDRs" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Vértice — Inteligência de Mercado",
    description: "Inteligência de mercado, risco e BDRs.",
    images: ["/og.png"],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}
