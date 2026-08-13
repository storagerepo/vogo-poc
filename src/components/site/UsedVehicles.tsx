import { ArrowRight } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { usedVehicles } from "@/data/vehicles";
import { Reveal } from "./Reveal";

export function UsedVehicles() {
  const { t, lang } = useI18n();

  const fmt = (n: number) =>
    new Intl.NumberFormat(lang === "es" ? "es-DO" : "en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(n);

  return (
    <section id="used" className="bg-[#f4f4f4] py-20 sm:py-28">
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
        {/* Heading */}
        <Reveal>
          <div className="flex items-end justify-between border-b border-[#e8e8e8] pb-8">
            <h2 className="display-xl text-4xl text-[#080808] sm:text-5xl lg:text-6xl">
              {t.used.title}
            </h2>
            <p className="hidden text-sm text-[#A0A0A0] sm:block">{t.used.sub}</p>
          </div>
        </Reveal>

        {/* Cards */}
        <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-3">
          {usedVehicles.map((v, i) => (
            <Reveal key={v.id} delay={i * 0.1}>
              <article className="group overflow-hidden bg-white">
                {/* Image */}
                <div className="relative aspect-[16/10] overflow-hidden">
                  <img
                    src={v.image}
                    alt={`${v.brand} ${v.model}`}
                    loading="lazy"
                    width={1200}
                    height={750}
                    className="h-full w-full object-cover transition-transform duration-[900ms] ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-105"
                  />
                  {/* Certified badge */}
                  <span className="eyebrow absolute left-0 top-0 bg-[#FFC72C] px-3 py-1.5 text-[10px] font-bold tracking-[0.2em] text-[#080808]">
                    {t.used.certified}
                  </span>
                </div>

                {/* Info */}
                <div className="p-5 sm:p-6">
                  <span className="eyebrow text-[10px] tracking-[0.2em] text-[#A0A0A0]">
                    {v.year} · {v.km.toLocaleString(lang === "es" ? "es-DO" : "en-US")} {t.used.km}
                  </span>
                  <h3 className="mt-2 font-display text-2xl uppercase text-[#080808]">
                    {v.brand} {v.model}
                  </h3>
                  <div className="mt-4 flex items-center justify-between">
                    <p className="font-display text-2xl text-[#080808]">{fmt(v.price)}</p>
                    <a
                      href="#testdrive"
                      className="eyebrow group/link inline-flex items-center gap-1.5 text-[11px] font-bold tracking-widest text-[#080808] transition-colors hover:text-[#FFC72C]"
                    >
                      {t.used.details}
                      <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover/link:translate-x-0.5" />
                    </a>
                  </div>
                </div>
              </article>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
