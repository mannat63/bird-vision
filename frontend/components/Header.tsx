import Link from "next/link";

export default function Header() {
  return (
    <header className="border-b border-forest-700/10 bg-ivory-50/80 backdrop-blur sticky top-0 z-30">
      <div className="mx-auto max-w-6xl px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <span className="text-2xl" aria-hidden>
            🪶
          </span>
          <span>
            <span className="font-serif text-xl text-forest-800 tracking-tight">
              BirdVision AI
            </span>
            <span className="hidden sm:block text-[11px] text-stone-warm -mt-1">
              Identify the wild. Understand the world.
            </span>
          </span>
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          <Link
            href="/"
            className="px-3 py-2 rounded-md text-forest-700 hover:bg-forest-700/5 transition"
          >
            Discover
          </Link>
          <Link
            href="/insights"
            className="px-3 py-2 rounded-md text-forest-700 hover:bg-forest-700/5 transition"
          >
            Model Insights
          </Link>
          <a
            href="https://ebird.org"
            target="_blank"
            rel="noreferrer"
            className="px-3 py-2 rounded-md text-stone-warm hover:text-forest-700 transition"
          >
            eBird ↗
          </a>
        </nav>
      </div>
    </header>
  );
}
