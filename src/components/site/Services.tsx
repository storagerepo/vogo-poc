import { Wrench, Package, SprayCan, Tag, BadgeDollarSign, ArrowRight } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { Reveal } from "./Reveal";

const icons = [Wrench, Package, SprayCan, Tag, BadgeDollarSign];

export function Services() {
  const { t } = useI18n();
  return (
    <section id="services" className="bg-white">
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
        <Reveal>
          <div className="border-b border-[#e8e8e8] py-12">
            <h2 className="display-xl text-4xl text-[#080808] sm:text-5xl">
              {t.services.title}
            </h2>
          </div>
        </Reveal>

        {/* Service rows */}
        <div className="divide-y divide-[#e8e8e8]">
          {t.services.items.map((item, i) => {
            const Icon = icons[i] ?? Wrench;
            return (
              <Reveal key={item.t} delay={i * 0.06}>
                <a
                  href="#locations"
                  className="group flex items-center justify-between py-6 transition-colors hover:bg-[#FFC72C] -mx-5 px-5 sm:-mx-8 sm:px-8"
                >
                  <div className="flex items-center gap-5">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center border border-[#e8e8e8] bg-white transition-colors group-hover:border-[#080808] group-hover:bg-[#080808]">
                      <Icon
                        className="h-5 w-5 text-[#080808] transition-colors group-hover:text-[#FFC72C]"
                        strokeWidth={1.5}
                      />
                    </div>
                    <span className="font-display text-xl uppercase tracking-wide text-[#080808] sm:text-2xl">
                      {item.t}
                    </span>
                  </div>
                  <ArrowRight className="h-5 w-5 text-[#A0A0A0] transition-all group-hover:translate-x-1 group-hover:text-[#080808]" />
                </a>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
