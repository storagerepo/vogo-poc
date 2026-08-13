import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import ctaImg from "@/assets/cta.jpg";
import { useI18n } from "@/lib/i18n";
import { useTestDrive } from "./TestDriveContext";

export function FinalCTA() {
  const { t } = useI18n();
  const { openModal } = useTestDrive();

  return (
    <section className="relative overflow-hidden bg-[#080808]">
      <motion.img
        src={ctaImg}
        alt="Night highway"
        loading="lazy"
        width={1920}
        height={900}
        initial={{ scale: 1.1 }}
        whileInView={{ scale: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 1.8, ease: [0.16, 1, 0.3, 1] }}
        className="absolute inset-0 h-full w-full object-cover opacity-50"
      />
      {/* Overlays */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#080808]/30 via-transparent to-[#080808]/60" />

      <div className="relative mx-auto flex max-w-[1400px] flex-col items-center px-5 py-32 text-center sm:px-8 sm:py-44">
        <motion.h2
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          className="display-xl max-w-3xl text-5xl text-white sm:text-6xl lg:text-8xl"
        >
          {t.final.title}
        </motion.h2>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.9, delay: 0.18, ease: [0.16, 1, 0.3, 1] }}
          className="mt-10 flex flex-col gap-3 sm:flex-row"
        >
          <a
            href="#vehicles"
            className="eyebrow group inline-flex items-center justify-center gap-2 bg-[#FFC72C] px-9 py-4 text-[11px] font-bold tracking-[0.25em] text-[#080808] transition-all hover:bg-white"
          >
            {t.final.cta1}
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </a>
          <button
            onClick={() => openModal()}
            className="eyebrow inline-flex items-center justify-center border border-white/40 px-9 py-4 text-[11px] tracking-[0.25em] text-white transition-all hover:border-white hover:bg-white hover:text-[#080808]"
          >
            {t.final.cta2}
          </button>
        </motion.div>
      </div>
    </section>
  );
}
