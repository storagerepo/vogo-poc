import { useState } from "react";
import { ArrowUpRight, Clock, MapPin, Wrench } from "lucide-react";
import mapImg from "@/assets/map.jpg";
import { useI18n } from "@/lib/i18n";
import { locations } from "@/data/vehicles";
import { Reveal } from "./Reveal";

export function Locations() {
  const { t, lang } = useI18n();
  const defaultId = locations[0]?.id ?? "";
  const [activeId, setActiveId] = useState(defaultId);
  const active = locations.find((l) => l.id === activeId);

  return (
    <section id="locations" className="bg-white py-20 sm:py-28">
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
        <Reveal>
          <div className="border-b border-[#e8e8e8] pb-10">
            <h2 className="display-xl text-4xl text-[#080808] sm:text-5xl lg:text-6xl">
              {t.locations.title}
            </h2>
          </div>
        </Reveal>

        <div className="mt-8 grid grid-cols-1 gap-0 lg:grid-cols-[1fr_420px]">
          {/* Map */}
          <Reveal>
            <div className="relative h-[320px] overflow-hidden bg-[#080808] lg:h-full lg:min-h-[500px]">
              <img
                src={mapImg}
                alt={t.locations.map}
                loading="lazy"
                width={1400}
                height={900}
                className="h-full w-full object-cover opacity-60"
              />
              {/* Pulsing dot */}
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="relative flex h-5 w-5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#FFC72C] opacity-60" />
                  <span className="relative inline-flex h-5 w-5 rounded-full bg-[#FFC72C]" />
                </span>
              </div>
              {/* Active label */}
              <span className="eyebrow absolute bottom-0 left-0 bg-[#FFC72C] px-4 py-2.5 text-[10px] font-bold tracking-[0.2em] text-[#080808]">
                {active?.name[lang]}
              </span>
            </div>
          </Reveal>

          {/* Location list */}
          <div className="divide-y divide-[#e8e8e8] border border-[#e8e8e8] lg:border-l-0">
            {locations.map((l, i) => {
              const isActive = l.id === activeId;
              return (
                <Reveal key={l.id} delay={i * 0.08}>
                  <button
                    onClick={() => setActiveId(l.id)}
                    className={`group w-full p-6 text-left transition-colors sm:p-7 ${
                      isActive ? "bg-[#080808]" : "bg-white hover:bg-[#f4f4f4]"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <h3
                        className={`font-display text-xl uppercase tracking-wide ${
                          isActive ? "text-[#FFC72C]" : "text-[#080808]"
                        }`}
                      >
                        {l.name[lang]}
                      </h3>
                      {isActive && (
                        <span className="h-2 w-2 rounded-full bg-[#FFC72C] mt-2" />
                      )}
                    </div>
                    <ul className={`mt-3 space-y-2 text-sm ${isActive ? "text-white/60" : "text-[#6b6b6b]"}`}>
                      <li className="flex gap-2.5">
                        <MapPin className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${isActive ? "text-[#FFC72C]" : "text-[#FFC72C]"}`} strokeWidth={1.5} />
                        {l.address}
                      </li>
                      <li className="flex gap-2.5">
                        <Clock className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#FFC72C]" strokeWidth={1.5} />
                        {l.hours[lang]}
                      </li>
                      <li className="flex gap-2.5">
                        <Wrench className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#FFC72C]" strokeWidth={1.5} />
                        {l.services[lang]}
                      </li>
                    </ul>
                    <a
                      href="#locations"
                      className={`eyebrow mt-4 inline-flex items-center gap-1.5 text-[10px] font-bold tracking-[0.2em] transition-colors ${
                        isActive ? "text-[#FFC72C] hover:text-white" : "text-[#080808] hover:text-[#FFC72C]"
                      }`}
                      onClick={(e) => e.stopPropagation()}
                    >
                      {t.locations.directions}
                      <ArrowUpRight className="h-3 w-3" />
                    </a>
                  </button>
                </Reveal>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
