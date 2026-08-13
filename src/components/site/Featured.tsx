import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import featuredImg from "@/assets/featured.jpg";
import { useI18n } from "@/lib/i18n";
import { Reveal } from "./Reveal";
import { useTestDrive } from "./TestDriveContext";

export function Featured() {
  const { t } = useI18n();
  const { openModal } = useTestDrive();

  return (
    <section id="featured" className="bg-[#080808]">
      <div className="grid grid-cols-1 lg:grid-cols-[60fr_40fr]">
        {/* Image — 60% */}
        <motion.div
          initial={{ opacity: 0, scale: 1.06 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          className="relative min-h-[280px] overflow-hidden lg:min-h-[680px]"
        >
          <img
            src={featuredImg}
            alt="Nissan Pathfinder"
            loading="lazy"
            width={1408}
            height={1008}
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-transparent to-[#080808]/40" />
        </motion.div>

        {/* Info — 40% */}
        <div className="flex items-center bg-[#080808] px-7 py-16 sm:px-12 lg:px-14 lg:py-20">
          <div className="w-full">
            <Reveal>
              <span className="eyebrow text-[10px] tracking-[0.3em] text-[#FFC72C]">
                {t.featured.eyebrow}
              </span>
              <p className="mt-4 font-display text-4xl uppercase tracking-wide text-white/40">
                {t.featured.brand}
              </p>
              <h2 className="display-xl text-6xl text-white sm:text-7xl lg:text-8xl">
                {t.featured.title}
              </h2>
              <p className="mt-4 text-base text-white/50">{t.featured.sub}</p>
            </Reveal>

            {/* Specs grid */}
            <div className="mt-10 grid grid-cols-2 gap-px bg-white/10">
              {t.featured.specs.map((s, i) => (
                <Reveal key={s.k} delay={0.08 * i}>
                  <div className="bg-[#080808] p-5">
                    <span className="eyebrow text-[10px] tracking-[0.2em] text-white/30">{s.k}</span>
                    <p className="mt-1.5 font-display text-2xl uppercase text-white">{s.v}</p>
                  </div>
                </Reveal>
              ))}
            </div>

            {/* CTAs */}
            <Reveal delay={0.2}>
              <div className="mt-10 flex flex-col gap-3 sm:flex-row">
                <a
                  href="#vehicles"
                  className="eyebrow group inline-flex items-center justify-center gap-2 bg-[#FFC72C] px-7 py-4 text-[11px] font-bold tracking-widest text-[#080808] transition-all hover:bg-white"
                >
                  {t.featured.cta1}
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </a>
                <button
                  onClick={() => openModal("Nissan Pathfinder Platinum")}
                  className="eyebrow inline-flex items-center justify-center border border-white/20 px-7 py-4 text-[11px] tracking-widest text-white transition-all hover:border-white/60"
                >
                  {t.featured.cta2}
                </button>
              </div>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}
