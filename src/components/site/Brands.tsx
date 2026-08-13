import { useI18n } from "@/lib/i18n";
import { brands } from "@/data/vehicles";
import { Reveal } from "./Reveal";

export function Brands() {
  const { t } = useI18n();
  return (
    <section id="brands" className="bg-[#080808] border-b border-white/10">
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
        <Reveal>
          <p className="eyebrow py-10 text-center text-[10px] tracking-[0.3em] text-white/30">
            {t.brands.title}
          </p>
        </Reveal>

        <div className="-mx-5 flex overflow-x-auto border-t border-white/10 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:mx-0 sm:grid sm:grid-cols-6">
          {brands.map((b, i) => (
            <Reveal key={b} delay={i * 0.07}>
              <a
                href="#vehicles"
                className="group flex h-24 shrink-0 min-w-[140px] items-center justify-center border-r border-white/10 transition-all duration-300 hover:bg-[#FFC72C] sm:min-w-0 sm:h-28"
              >
                <span className="font-display text-2xl font-normal uppercase tracking-[0.15em] text-white/25 transition-all duration-300 group-hover:text-[#080808] group-hover:scale-105 sm:text-3xl">
                  {b}
                </span>
              </a>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
