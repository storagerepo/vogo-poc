import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import heritageImg from "@/assets/heritage.jpg";
import { useI18n } from "@/lib/i18n";
import { Reveal } from "./Reveal";

export function About() {
  const { t } = useI18n();
  return (
    <section id="about" className="bg-[#080808] py-20 sm:py-28">
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2 lg:gap-16">
          {/* Image */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
            className="relative aspect-[4/3] overflow-hidden"
          >
            <img
              src={heritageImg}
              alt="Historic SDM showroom"
              loading="lazy"
              width={1400}
              height={1000}
              className="h-full w-full object-cover grayscale"
            />
            {/* Year overlay */}
            <span className="eyebrow absolute bottom-0 left-0 bg-[#FFC72C] px-4 py-3 text-[11px] font-bold tracking-[0.2em] text-[#080808]">
              EST. 1920
            </span>
          </motion.div>

          {/* Text */}
          <div>
            <Reveal>
              <span className="eyebrow text-[10px] tracking-[0.3em] text-[#FFC72C]">
                {t.about.eyebrow}
              </span>
              <h2 className="display-xl mt-4 text-5xl text-white sm:text-6xl lg:text-7xl">
                {t.about.title.split("\n").map((line, i) => (
                  <span key={i} className="block">
                    {line}
                  </span>
                ))}
              </h2>
              <p className="mt-5 text-sm text-white/50">{t.about.sub}</p>
            </Reveal>

            {/* Stats */}
            <div className="mt-10 grid grid-cols-2 gap-px bg-white/10 sm:grid-cols-4 lg:grid-cols-2 xl:grid-cols-4">
              {t.about.stats.map((s, i) => (
                <Reveal key={s.l} delay={i * 0.08}>
                  <div className="bg-[#080808] p-5">
                    <p className="font-display text-3xl uppercase text-[#FFC72C]">{s.v}</p>
                    <span className="eyebrow mt-1 block text-[10px] tracking-[0.2em] text-white/30">
                      {s.l}
                    </span>
                  </div>
                </Reveal>
              ))}
            </div>

            {/* Our Story link */}
            <Reveal delay={0.15}>
              <a
                href="#about"
                className="eyebrow group mt-8 inline-flex items-center gap-2 text-[11px] font-bold tracking-[0.2em] text-[#FFC72C] transition-colors hover:text-white"
              >
                {t.about.ourStory}
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </a>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}
