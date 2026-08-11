import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";

import finalStill from "@/assets/final-cta.jpg";
import { MagneticButton } from "@/components/vogo/magnetic-button";
import { MaskLine } from "@/components/vogo/reveal";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

export function FinalCta() {
  const ref = useRef<HTMLElement>(null);
  const reduced = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], ["-8%", "8%"]);

  return (
    <section id="the-edit" ref={ref} className="relative h-[78svh] min-h-[520px] overflow-hidden bg-charcoal">
      <motion.div className="film absolute inset-0" style={{ y }}>
        <img
          src={finalStill}
          alt="Empty coastal road at golden hour"
          width={1920}
          height={1088}
          loading="lazy"
          decoding="async"
          className={`h-full w-full object-cover ${reduced ? "" : "ken-burns"}`}
        />
        <div className="absolute inset-0 bg-charcoal/50" />
      </motion.div>

      <div className="relative z-10 mx-auto flex h-full max-w-[1500px] flex-col items-start justify-center px-6 text-ivory md:px-10">
        <p className="eyebrow text-ivory/60">The Vogo Edit</p>
        <h2 className="mt-5 max-w-3xl font-display text-[clamp(2.4rem,6vw,5.4rem)] leading-[0.98]">
          <MaskLine>Find a stay</MaskLine>
          <MaskLine delay={0.08}>
            worth the <em className="font-normal italic text-vogo">trip</em>.
          </MaskLine>
        </h2>
        <MagneticButton className="eyebrow mt-10 rounded-full bg-vogo px-9 py-4 text-navy transition-colors hover:bg-ivory hover:text-charcoal">
          Explore stays →
        </MagneticButton>
      </div>
    </section>
  );
}

export function SiteFooter() {
  return (
    <footer className="bg-navy text-ivory">
      <div className="mx-auto grid max-w-[1500px] items-center gap-6 px-6 py-6 md:grid-cols-[minmax(0,1fr)_auto] md:px-10">
        <img src="/vogo-logo.png" alt="Vogo" className="h-8 w-auto object-contain brightness-0 invert" />
        <p className="eyebrow text-ivory/50">© {new Date().getFullYear()} — Stays worth the journey</p>
      </div>
    </footer>
  );
}
