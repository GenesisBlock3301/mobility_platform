import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import Link from "next/link";
import { LogoMark } from "@/components/icons";
import { NavLinks } from "@/components/NavLinks";
import { api } from "@/lib/api";
import { getProfileId } from "@/lib/session";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], variable: "--font-space-grotesk", weight: ["500", "600", "700"] });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains-mono", weight: ["400", "500"] });

export const metadata: Metadata = {
  title: { default: "MobilityMatch", template: "%s · MobilityMatch" },
  description: "See which roles abroad fit you, and what stands in the way.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#ffffff",
};

async function shortlistCount(): Promise<number> {
  const id = await getProfileId();
  if (!id) return 0;
  try {
    return (await api.shortlistIds(id)).length;
  } catch {
    // The header must never break a page; the count is optional.
    return 0;
  }
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const count = await shortlistCount();
  return (
    <html lang="en" className={`${inter.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:rounded-lg focus:bg-surface focus:px-4 focus:py-2"
        >
          Skip to content
        </a>
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-line bg-surface px-4 py-3 sm:px-8">
          <Link href="/" className="flex min-h-11 items-center gap-2.5 font-display text-xl font-semibold text-ink">
            <LogoMark className="size-7 text-accent" />
            MobilityMatch
          </Link>
          <NavLinks shortlistCount={count} />
        </header>
        <div id="main">{children}</div>
        <footer className="mx-auto max-w-[1180px] px-4 pb-10 text-xs text-muted sm:px-8">
          Prototype for a technical assessment. All roles and organisations are fictional.
        </footer>
      </body>
    </html>
  );
}
