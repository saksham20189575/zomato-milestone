import { Sparkles } from "lucide-react";

export function Hero() {
  return (
    <header className="mb-8 text-center">
      <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.06] px-4 py-1.5 text-[0.65rem] font-semibold uppercase tracking-[0.12em] text-gray-400">
        <Sparkles className="h-3 w-3" />
        Discover the future of dining
      </div>
      <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl md:text-[3.2rem] md:leading-tight">
        TasteTrail <span className="font-semibold text-gray-500">AI</span>
      </h1>
      <p className="mx-auto mt-4 max-w-lg text-base leading-relaxed text-gray-400">
        Personalized restaurant discovery powered by AI and real-world dining preferences.
      </p>
    </header>
  );
}
