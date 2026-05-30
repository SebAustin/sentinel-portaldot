import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sentinel — Portaldot Treasury Copilot",
  description: "AI treasury intents secured by Portaldot multisig pallet",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen">
          <header className="border-b border-border bg-card/50 backdrop-blur">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
              <div>
                <p className="text-xs uppercase tracking-widest text-primary">Built with Portaldot</p>
                <h1 className="text-xl font-bold">Sentinel Treasury Copilot</h1>
              </div>
              <p className="hidden text-sm text-muted-foreground sm:block">
                Secured by multisig pallet · threshold 2-of-3
              </p>
            </div>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
