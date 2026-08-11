import { AnimatePresence, motion, useScroll, useMotionValueEvent } from "framer-motion";
import { useState } from "react";

const LINKS = ["Stays", "Destinations", "Types", "The Edit"];

export function SiteNav() {
  const { scrollY } = useScroll();
  const [compact, setCompact] = useState(false);
  const [open, setOpen] = useState(false);

  useMotionValueEvent(scrollY, "change", (v) => setCompact(v > 80));

  return (
    <motion.header
      className="fixed inset-x-0 top-0 z-50"
      initial={{ backgroundColor: "rgba(0,0,0,0)", backdropFilter: "blur(0px)", borderColor: "rgba(0,0,0,0)" }}
      animate={{
        backgroundColor: compact ? "color-mix(in oklab, var(--ivory) 78%, transparent)" : "rgba(0,0,0,0)",
        backdropFilter: compact ? "blur(14px)" : "blur(0px)",
        borderColor: compact ? "var(--border)" : "rgba(0,0,0,0)",
      }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      style={{ borderBottomWidth: 1 }}
    >
      <nav
        className={`mx-auto grid grid-cols-[minmax(0,1fr)_auto] items-center gap-6 px-6 transition-[padding,color] duration-500 md:px-10 lg:grid-cols-[1fr_auto_1fr] ${compact ? "py-4 text-charcoal" : "py-7 text-ivory"
          }`}
      >
        <a href="#top" className="flex min-w-0 items-center" aria-label="Vogo — Home">
          <img
            src="/vogo-logo.png"
            alt="Vogo"
            className="h-9 w-auto object-contain transition-all duration-500"
            style={{
              filter: compact
                ? "none"
                : "brightness(0) invert(1)",
            }}
          />
        </a>

        <ul className="hidden items-center gap-10 lg:flex">
          {LINKS.map((l) => (
            <li key={l}>
              <a
                href={`#${l.toLowerCase().replace(/\s+/g, "-")}`}
                className="eyebrow relative py-1 opacity-80 transition-opacity hover:opacity-100 after:absolute after:bottom-0 after:left-0 after:h-px after:w-full after:origin-right after:scale-x-0 after:bg-current after:transition-transform after:duration-500 hover:after:origin-left hover:after:scale-x-100"
              >
                {l}
              </a>
            </li>
          ))}
        </ul>

        <div className="hidden shrink-0 items-center justify-end gap-8 lg:flex">
          <a href="#search" className="eyebrow opacity-80 transition-opacity hover:opacity-100">
            Search
          </a>
          <a
            href="#search"
            className="eyebrow rounded-full bg-vogo px-5 py-2.5 text-navy transition-colors duration-300 hover:bg-navy hover:text-ivory"
          >
            Log in
          </a>
        </div>

        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="eyebrow justify-self-end lg:hidden"
          aria-expanded={open}
        >
          {open ? "Close" : "Menu"}
        </button>
      </nav>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden bg-ivory text-charcoal lg:hidden"
          >
            <ul className="flex flex-col gap-6 px-6 py-8">
              {[...LINKS, "Search", "Log in"].map((l) => (
                <li key={l}>
                  <a
                    href={`#${l.toLowerCase().replace(/\s+/g, "-")}`}
                    onClick={() => setOpen(false)}
                    className="font-display text-4xl"
                  >
                    {l}
                  </a>
                </li>
              ))}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
