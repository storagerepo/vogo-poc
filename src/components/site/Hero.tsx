import { motion, useScroll, useTransform } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { useRef } from "react";
import heroImg from "@/assets/hero.jpg";
import { useI18n } from "@/lib/i18n";
import { useTestDrive } from "./TestDriveContext";

export function Hero() {
  const { t } = useI18n();
  const { openModal } = useTestDrive();
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const scale = useTransform(scrollYProgress, [0, 1], [1.08, 1.0]);
  const opacity = useTransform(scrollYProgress, [0, 0.75], [1, 0]);
  const y = useTransform(scrollYProgress, [0, 1], ["0%", "15%"]);

  const ease = [0.16, 1, 0.3, 1] as const;

  return (
    <section id="top" ref={ref} className="relative min-h-[92svh] overflow-hidden bg-[#080808]" style={{ minHeight: "92svh" }}>
      {/* Background image with parallax */}
      <motion.div style={{ y, scale }} className="absolute inset-0 z-0 origin-center">
        <img
          src={heroImg}
          alt="Premium automotive vehicle"
          width={1920}
          height={1088}
          className="h-full w-full object-cover object-center"
        />
        {/* Dark overlays */}
        <div className="absolute inset-0 bg-[#080808]/30" />
        <div className="absolute inset-x-0 bottom-0 h-3/4 bg-gradient-to-t from-[#080808] via-[#080808]/60 to-transparent" />
        <div className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-[#080808]/60 to-transparent" />
      </motion.div>

      {/* Content */}
      <motion.div
        style={{ opacity }}
        className="relative z-10 mx-auto flex min-h-[92svh] max-w-[1400px] flex-col justify-end px-5 pb-20 pt-36 sm:px-8 sm:pb-24"
      >
        {/* Eyebrow */}
        <motion.span
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease }}
          className="eyebrow text-[#FFC72C] text-[11px] tracking-[0.3em]"
        >
          {t.hero.eyebrow}
        </motion.span>

        {/* Main title */}
        <motion.h1
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.1, ease }}
          className="display-xl mt-4 text-[14vw] leading-none text-white sm:text-[11vw] lg:text-[9.5rem] xl:text-[10rem]"
          style={{ textShadow: "0 4px 40px rgba(0,0,0,0.4)" }}
        >
          {t.hero.title.split("\n").map((line, i) => (
            <span key={i} className="block">
              {line}
            </span>
          ))}
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.28, ease }}
          className="mt-5 text-base text-white/60 sm:text-lg"
        >
          {t.hero.sub}
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.42, ease }}
          className="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center"
        >
          <a
            href="#vehicles"
            className="eyebrow group inline-flex items-center justify-center gap-2 bg-[#FFC72C] px-8 py-4 text-[#080808] font-bold tracking-widest transition-all hover:bg-white"
          >
            {t.hero.cta1}
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </a>
          <button
            onClick={() => openModal()}
            className="eyebrow inline-flex items-center justify-center border border-white/40 px-8 py-4 text-white tracking-widest transition-all hover:border-white hover:bg-white hover:text-[#080808]"
          >
            {t.hero.cta2}
          </button>
        </motion.div>
      </motion.div>
    </section>
  );
}
