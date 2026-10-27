import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-xl px-4 py-24 text-center">
      <p className="text-5xl" aria-hidden>
        🪶
      </p>
      <h1 className="font-serif text-3xl text-forest-800 mt-4">
        This page flew away
      </h1>
      <p className="text-stone-deep mt-2">
        The page you were looking for could not be found.
      </p>
      <Link
        href="/"
        className="inline-block mt-6 rounded-lg bg-forest-700 px-5 py-2.5 text-ivory-50 text-sm hover:bg-forest-600 transition"
      >
        Back to Discover
      </Link>
    </main>
  );
}
