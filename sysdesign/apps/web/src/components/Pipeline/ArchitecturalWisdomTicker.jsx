import React, { useState, useEffect } from "react";
import { Quote } from "lucide-react";

const ARCHITECTURAL_TRUTHS = [
  {
    quote: "There are no right or wrong architectures, only architectures that are more or less fit for a given purpose.",
    author: "Martin Fowler",
    title: "Chief Scientist, Thoughtworks · Author of Patterns of Enterprise Application Architecture",
    tag: "Context Is King",
  },
  {
    quote: "Architecture is not about making the 'right' choice; it's about choosing which trade-offs you can live with. If you don't know the trade-offs, you don't understand the architecture.",
    author: "Mark Richards & Neal Ford",
    title: "Authors of Fundamentals of Software Architecture",
    tag: "The Law of Trade-Offs",
  },
  {
    quote: "The First Law of Software Architecture: Everything in software architecture is a trade-off. (And if an architect thinks they've found something that isn't a trade-off, they just haven't figured out what the catch is yet.)",
    author: "Mark Richards",
    title: "Enterprise Software Architect & Author",
    tag: "First Law of Architecture",
  },
];

export default function ArchitecturalWisdomTicker({ className = "" }) {
  const [index, setIndex] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      // 1. Fade out
      setVisible(false);
      setTimeout(() => {
        // 2. Change quote
        setIndex((prev) => (prev + 1) % ARCHITECTURAL_TRUTHS.length);
        // 3. Fade in
        setVisible(true);
      }, 500);
    }, 6500);

    return () => clearInterval(interval);
  }, []);

  const current = ARCHITECTURAL_TRUTHS[index];

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-cyan-400/20 bg-gradient-to-r from-cyan-950/40 via-[#07131b]/60 to-black/80 backdrop-blur-md p-5 shadow-[0_0_30px_rgba(34,211,238,0.08)] ${className}`}
    >
      <div className="flex items-start gap-3.5">
        <div className="shrink-0 p-2 rounded-xl bg-cyan-500/10 border border-cyan-400/30 text-cyan-300">
          <Quote size={18} className="rotate-180" />
        </div>

        <div
          className={`flex-1 transition-all duration-500 transform ${
            visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"
          }`}
        >
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-400 font-bold px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-400/20">
              {current.tag}
            </span>
            <span className="text-[10px] text-white/30 font-mono tracking-wider">
              Truth #{index + 1} of {ARCHITECTURAL_TRUTHS.length}
            </span>
          </div>

          <p className="text-sm md:text-base font-serif italic text-white/90 leading-relaxed">
            "{current.quote}"
          </p>

          <div className="mt-2.5 flex flex-wrap items-center gap-2 text-xs">
            <span className="font-semibold text-cyan-300">{current.author}</span>
            <span className="text-white/30">·</span>
            <span className="text-white/50 text-[11px]">{current.title}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
