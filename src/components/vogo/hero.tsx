import { motion, useScroll, useTransform } from "framer-motion";
import { Suspense, lazy, useEffect, useRef, useState } from "react";

import heroStill from "@/assets/hero.jpg";
import { MagneticButton } from "@/components/vogo/magnetic-button";
import { useIsDesktop, useReducedMotion } from "@/hooks/use-reduced-motion";

const HeroGlobe = lazy(() => import("@/components/vogo/hero-globe"));

const SEARCH_FIELDS = [
  { label: "Destination", value: "Where to?" },
  { label: "Check-in", value: "Add dates" },
  { label: "Check-out", value: "Add dates" },
  { label: "Guests", value: "2 guests" },
];


export function Hero() {
  const ref = useRef<HTMLElement>(null);
  const isDesktop = useIsDesktop(768);
  const reduced = useReducedMotion();
  const [mount3d, setMount3d] = useState(false);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], ["0%", "18%"]);
  const fade = useTransform(scrollYProgress, [0, 0.8], [1, 0]);

  useEffect(() => {
    // Lazy-load the globe only once the hero is idle and visible.
    const id = window.setTimeout(() => setMount3d(true), 600);
    return () => window.clearTimeout(id);
  }, []);

  return (
    <section ref={ref} id="top" className="relative h-[100svh] min-h-[640px] overflow-hidden bg-charcoal">
      {/* Cinematic ambient footage layer */}
      <motion.div className="film absolute inset-0" style={{ y }}>
        <img
          src={heroStill}
          alt="Cliffside villa above the Amalfi coast at golden hour"
          width={1920}
          height={1088}
          className={`h-full w-full object-cover ${reduced ? "" : "ken-burns"}`}
        />
        <div className="absolute inset-0 bg-charcoal/45" />
        <div className="absolute inset-x-0 bottom-0 h-2/5 bg-gradient-to-t from-charcoal/85 to-transparent" />
      </motion.div>

      {/* Interactive globe */}
      {/* <div className="pointer-events-none absolute inset-0 opacity-70 md:left-auto md:top-[-6%] md:w-[46%] md:opacity-90">
        {mount3d && isDesktop && (
          <Suspense fallback={null}>
            <HeroGlobe />
          </Suspense>
        )}
      </div> */}

      <motion.div
        style={{ opacity: fade }}
        className="relative z-10 mx-auto flex h-full max-w-[1500px] flex-col justify-end px-6 pb-14 text-ivory md:px-10 md:pb-20"
      >
        <div className="max-w-4xl">
          {/* <motion.p
            className="eyebrow text-ivory/70"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.2 }}
          >
            Vogo — Stays worth the journey
          </motion.p> */}

          <h1 className="mt-6 font-display text-[clamp(2.9rem,8.5vw,8.2rem)] leading-[0.94]">
            {["Go somewhere", "worth remembering."].map((line, i) => (
              <span key={line} className="block overflow-hidden pb-[0.06em]">
                <motion.span
                  className="block"
                  initial={{ y: "110%" }}
                  animate={{ y: "0%" }}
                  transition={{ duration: 1.3, delay: 0.25 + i * 0.12, ease: [0.16, 1, 0.3, 1] }}
                >
                  {i === 1 ? <em className="font-normal italic text-vogo">{line}</em> : line}
                </motion.span>
              </span>
            ))}
          </h1>

          <motion.p
            className="mt-6 max-w-md text-base leading-relaxed text-ivory/75 md:text-lg"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1.2, delay: 0.8 }}
          >
            The easy way to find your stay — compare every partner in one search.
          </motion.p>

          <motion.p
            className="eyebrow mt-6 flex items-center gap-3 text-ivory/70"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1.2, delay: 0.95 }}
          >
            <span className="h-2 w-2 rounded-full bg-vogo" aria-hidden />
            9.8+ million properties available
          </motion.p>
        </div>

        {/* Floating rounded search bar */}
        <motion.div
          id="search"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.1, delay: 1, ease: [0.16, 1, 0.3, 1] }}
          className="mt-10 w-full max-w-5xl rounded-3xl border border-ivory/20 bg-ivory p-2 text-charcoal shadow-[0_24px_60px_-24px_rgba(0,0,0,0.55)] lg:rounded-full"
        >
          <form
            onSubmit={(e) => e.preventDefault()}
            className="grid grid-cols-1 divide-y divide-border sm:grid-cols-2 sm:divide-x sm:divide-y-0 lg:grid-cols-[1.3fr_1fr_1fr_0.9fr_auto]"
          >
            {SEARCH_FIELDS.map((f) => (
              <label key={f.label} className="block min-w-0 px-5 py-3.5">
                <span className="eyebrow text-muted-foreground">{f.label}</span>
                <input
                  defaultValue={f.value}
                  aria-label={f.label}
                  className="mt-1 w-full truncate bg-transparent font-display text-lg text-charcoal outline-none placeholder:text-muted-foreground"
                />
              </label>
            ))}
            <MagneticButton
              strength={8}
              onClick={() =>
                document.getElementById("stays")?.scrollIntoView({ behavior: "smooth" })
              }
              className="eyebrow flex items-center justify-center gap-3 rounded-2xl bg-vogo px-9 py-4 text-navy transition-colors duration-300 hover:bg-navy hover:text-ivory sm:col-span-2 lg:col-span-1 lg:rounded-full"
            >
              Search <span aria-hidden>→</span>
            </MagneticButton>
          </form>
        </motion.div>

      </motion.div>

      <motion.span
        className="eyebrow absolute right-6 bottom-6 hidden text-ivory/50 md:block"
        animate={reduced ? {} : { opacity: [0.3, 0.8, 0.3] }}
        transition={{ duration: 3.2, repeat: Infinity }}
      >
        Scroll
      </motion.span>
    </section>
  );
}
