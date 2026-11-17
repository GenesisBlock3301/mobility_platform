"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/profile", label: "Profile" },
  { href: "/matches", label: "Matches" },
  { href: "/shortlist", label: "Shortlist" },
];

export function NavLinks({ shortlistCount }: { shortlistCount: number }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Main" className="flex flex-wrap gap-1">
      {LINKS.map((link) => {
        const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
        return (
          <Link
            key={link.href}
            href={link.href}
            aria-current={active ? "page" : undefined}
            className={`inline-flex min-h-11 items-center gap-2 rounded-lg px-3.5 font-medium ${
              active ? "bg-accent-soft font-semibold text-accent-strong" : "text-muted hover:text-ink"
            }`}
          >
            {link.label}
            {link.href === "/shortlist" && shortlistCount > 0 && (
              <span className="min-w-[22px] rounded-full bg-accent px-1.5 text-center text-xs font-semibold leading-[22px] text-white">
                {shortlistCount}
                <span className="sr-only"> saved</span>
              </span>
            )}
          </Link>
        );
      })}
    </nav>
  );
}
