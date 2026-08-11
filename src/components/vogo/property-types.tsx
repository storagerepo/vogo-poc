import alps from "@/assets/alps.jpg";
import casaMare from "@/assets/casa-mare.jpg";
import maldives from "@/assets/maldives.jpg";
import prop1 from "@/assets/prop-1.jpg";
import prop2 from "@/assets/prop-2.jpg";
import prop3 from "@/assets/prop-3.jpg";
import prop4 from "@/assets/prop-4.jpg";
import bnb from "@/assets/type-bnb.jpg";
import cabin from "@/assets/type-cabin.jpg";
import cottage from "@/assets/type-cottage.jpg";
import motel from "@/assets/type-motel.jpg";
import { MaskLine, Reveal } from "@/components/vogo/reveal";

const TYPES = [
  { name: "House", stays: "412k stays", img: alps },
  { name: "Apartment", stays: "1.2m stays", img: prop2 },
  { name: "Hotel", stays: "2.4m stays", img: prop4 },
  { name: "Motel", stays: "86k stays", img: motel },
  { name: "Villa", stays: "154k stays", img: prop1 },
  { name: "Cottage", stays: "63k stays", img: cottage },
  { name: "Cabin", stays: "48k stays", img: cabin },
  { name: "Resort", stays: "118k stays", img: maldives },
  { name: "Bed & Breakfast", stays: "97k stays", img: bnb },
  { name: "Vacation Rental", stays: "780k stays", img: prop3 },
];

export function PropertyTypes() {
  return (
    <section id="types" className="border-y border-border bg-ivory-dim py-20 text-charcoal md:py-28">
      <div className="mx-auto max-w-[1500px] px-6 md:px-10">
        <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
          <div>
            <p className="eyebrow text-navy-soft">Top property types</p>
            <h2 className="mt-4 font-display text-[clamp(2rem,4vw,3.4rem)] leading-[1.06]">
              <MaskLine>Explore stays by type</MaskLine>
            </h2>
          </div>
          <Reveal className="max-w-xs md:text-right">
            <p className="text-sm leading-relaxed text-muted-foreground">
              From a city apartment to a cabin at the end of a forest road.
            </p>
          </Reveal>
        </div>
      </div>

      <div className="hide-scrollbar mt-12 flex snap-x snap-mandatory gap-4 overflow-x-auto px-6 pb-4 md:gap-5 md:px-10">
        {TYPES.map((t) => (
          <a
            key={t.name}
            href="#stays"
            data-cursor="grow"
            className="group relative block h-[260px] w-[62vw] shrink-0 snap-start overflow-hidden rounded-[20px] bg-charcoal sm:w-[38vw] lg:h-[300px] lg:w-[22vw]"
          >
            <img
              src={t.img}
              alt={t.name}
              width={700}
              height={600}
              loading="lazy"
              decoding="async"
              className="h-full w-full object-cover transition-transform duration-[900ms] ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-[1.06]"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-navy/85 via-navy/25 to-navy/0" />
            <div className="absolute inset-x-0 bottom-0 flex items-end justify-between gap-3 p-5 text-ivory">
              <div className="min-w-0">
                <h3 className="truncate font-display text-2xl leading-tight">{t.name}</h3>
                <p className="eyebrow mt-1.5 text-ivory/65">{t.stays}</p>
              </div>
              <span
                aria-hidden
                className="shrink-0 text-vogo transition-transform duration-500 group-hover:translate-x-1"
              >
                →
              </span>
            </div>
          </a>
        ))}
        <div aria-hidden className="w-2 shrink-0 md:w-6" />
      </div>

      <div className="mx-auto mt-6 max-w-[1500px] px-6 md:px-10">
        <p className="eyebrow text-muted-foreground">Scroll for more types →</p>
      </div>

    </section>
  );
}
