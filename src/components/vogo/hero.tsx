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
          className="mt-8 w-full max-w-[950px] rounded-3xl bg-ivory p-2 shadow-[0_20px_50px_-12px_rgba(0,0,0,0.6)] lg:rounded-full"
        >
          <form
            onSubmit={(e) => e.preventDefault()}
            className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:flex lg:flex-row lg:items-center"
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 sm:col-span-2 lg:flex lg:flex-1 lg:gap-0">
              {SEARCH_FIELDS.map((f, i) => (
                <div key={f.label} className={`relative flex ${i === 0 ? "lg:flex-[1.3]" : i === 3 ? "lg:flex-[0.9]" : "lg:flex-1"}`}>
                  <label className="group flex w-full min-w-0 cursor-pointer flex-col justify-center rounded-2xl px-6 py-3 transition-colors hover:bg-black/5 lg:rounded-full">
                    <span className="text-[11px] font-bold uppercase tracking-widest text-charcoal/60">{f.label}</span>
                    <input
                      defaultValue={f.value}
                      aria-label={f.label}
                      className="mt-1 w-full truncate bg-transparent text-[16px] font-medium text-charcoal outline-none placeholder:text-charcoal/40"
                    />
                  </label>
                  {i < SEARCH_FIELDS.length - 1 && (
                    <div className="absolute right-0 top-1/2 hidden h-8 -translate-y-1/2 w-[1px] bg-charcoal/15 lg:block" />
                  )}
                </div>
              ))}
            </div>
            
            <div className="sm:col-span-2 lg:ml-2 lg:flex-shrink-0">
              <MagneticButton
                strength={8}
                onClick={() =>
                  document.getElementById("stays")?.scrollIntoView({ behavior: "smooth" })
                }
                className="flex h-[56px] w-full items-center justify-center rounded-2xl lg:rounded-full bg-vogo px-10 text-[13px] font-bold uppercase tracking-wider text-navy transition-all duration-300 hover:bg-navy hover:text-ivory lg:w-auto"
              >
                Search
              </MagneticButton>
            </div>
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
