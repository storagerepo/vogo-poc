import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { vehicles, type Category } from "@/data/vehicles";
import { Reveal } from "./Reveal";
import { useTestDrive } from "./TestDriveContext";

type Tab = "all" | Category;

export function VehiclesSection() {
  const { t, lang } = useI18n();
  const { openModal } = useTestDrive();
  const [tab, setTab] = useState<Tab>("all");

  const tabs: { key: Tab; label: string }[] = [
    { key: "all", label: t.vehicles.all },
    { key: "suvs", label: t.vehicles.suvs },
    { key: "sedans", label: t.vehicles.sedans },
    { key: "pickups", label: t.vehicles.pickups },
    { key: "commercial", label: t.vehicles.commercial },
    { key: "motorcycles", label: t.vehicles.motorcycles },
  ];

  const list = useMemo(
    () => (tab === "all" ? vehicles : vehicles.filter((v) => v.category === tab)),
    [tab],
  );

  const fmt = (n: number) =>
    new Intl.NumberFormat(lang === "es" ? "es-DO" : "en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(n);

  return (
    <section id="vehicles" className="bg-white py-20 sm:py-28">
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
        {/* Section header */}
        <Reveal>
          <h2 className="display-xl text-4xl text-[#080808] sm:text-5xl lg:text-6xl">
            {t.vehicles.title}
          </h2>
        </Reveal>

        {/* Category filters */}
        <Reveal delay={0.1}>
          <div className="mt-8 -mx-5 flex gap-0 overflow-x-auto px-5 pb-2 sm:mx-0 sm:px-0 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden border-b border-[#e8e8e8]">
            {tabs.map((tb) => (
              <button
                key={tb.key}
                onClick={() => setTab(tb.key)}
                className={`eyebrow shrink-0 border-b-2 px-5 py-4 text-[11px] tracking-[0.2em] transition-all duration-200 -mb-[2px] ${
                  tab === tb.key
                    ? "border-[#FFC72C] text-[#080808] font-bold"
                    : "border-transparent text-[#6b6b6b] hover:text-[#080808]"
                }`}
              >
                {tb.label}
              </button>
            ))}
          </div>
        </Reveal>

        {/* Vehicle grid */}
        <motion.div layout className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <AnimatePresence mode="popLayout">
            {list.map((v) => (
              <motion.article
                key={v.id}
                layout
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.96 }}
                transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
                className="group cursor-pointer overflow-hidden bg-[#f4f4f4]"
              >
                {/* Image — dominant */}
                <div className="relative aspect-[16/10] overflow-hidden">
                  <img
                    src={v.image}
                    alt={`${v.brand} ${v.model}`}
                    loading="lazy"
                    width={1200}
                    height={750}
                    className="h-full w-full object-cover transition-transform duration-[900ms] ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-105"
                  />
                  {/* Brand badge */}
                  <span className="absolute top-0 left-0 bg-[#080808] px-3 py-1.5">
                    <span className="eyebrow text-[10px] tracking-[0.2em] text-[#FFC72C]">
                      {v.brand}
                    </span>
                  </span>
                </div>

                {/* Info */}
                <div className="p-5 sm:p-6">
                  <h3 className="font-display text-2xl uppercase tracking-wide text-[#080808]">
                    {v.model}
                  </h3>
                  <p className="mt-1 text-xs text-[#6b6b6b]">{v.spec[lang]}</p>

                  <div className="mt-4 flex items-center justify-between">
                    <div>
                      <span className="eyebrow text-[10px] text-[#A0A0A0]">{t.vehicles.from}</span>
                      <p className="font-display text-2xl text-[#080808]">{fmt(v.price)}</p>
                    </div>
                    <div className="flex gap-2">
                      <a
                        href="#featured"
                        className="group/btn inline-flex items-center gap-1.5 bg-[#FFC72C] px-4 py-2.5 text-[11px] font-bold uppercase tracking-widest text-[#080808] transition-all hover:bg-[#080808] hover:text-white"
                      >
                        {t.vehicles.details}
                        <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover/btn:translate-x-0.5" />
                      </a>
                      <button
                        onClick={() => openModal(`${v.brand} ${v.model}`)}
                        className="eyebrow border border-[#e8e8e8] px-3 py-2.5 text-[11px] text-[#080808] transition-all hover:border-[#080808]"
                      >
                        {t.vehicles.testDrive}
                      </button>
                    </div>
                  </div>
                </div>
              </motion.article>
            ))}
          </AnimatePresence>
        </motion.div>
      </div>
    </section>
  );
}
