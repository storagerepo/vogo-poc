import alps from "@/assets/alps.jpg";
import amalfi from "@/assets/amalfi.jpg";
import bali from "@/assets/bali.jpg";
import maldives from "@/assets/maldives.jpg";
import paris from "@/assets/paris.jpg";
import tokyo from "@/assets/tokyo.jpg";
import { MaskLine, Reveal } from "@/components/vogo/reveal";

type Destination = {
  name: string;
  country: string;
  img: string;
  stays: string;
  from: string;
};

const FEATURED: Destination[] = [
  { name: "Amalfi", country: "Italy", img: amalfi, stays: "4,120 stays", from: "from €210" },
  { name: "Bali", country: "Indonesia", img: bali, stays: "9,480 stays", from: "from €90" },
];

const SMALL: Destination[] = [
  { name: "Tokyo", country: "Japan", img: tokyo, stays: "6,960 stays", from: "from €130" },
  { name: "Maldives", country: "Indian Ocean", img: maldives, stays: "1,540 stays", from: "from €480" },
  { name: "Paris", country: "France", img: paris, stays: "12,100 stays", from: "from €165" },
  { name: "Swiss Alps", country: "Switzerland", img: alps, stays: "2,880 stays", from: "from €240" },
];

function Card({ d, large = false }: { d: Destination; large?: boolean }) {
  return (
    <a
      href="#stays"
      data-cursor="grow"
      className={`group relative block overflow-hidden rounded-[20px] bg-charcoal ${
        large ? "h-[340px] md:h-[420px]" : "h-[210px] md:h-[240px]"
      }`}
    >
      <img
        src={d.img}
        alt={`${d.name}, ${d.country}`}
        width={1200}
        height={900}
        loading="lazy"
        decoding="async"
        className="h-full w-full object-cover transition-transform duration-[900ms] ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-[1.05]"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-navy/85 via-navy/25 to-navy/0" />
      <div className="absolute inset-x-0 bottom-0 flex items-end justify-between gap-3 p-5 text-ivory md:p-6">
        <div className="min-w-0">
          <p className="eyebrow text-ivory/60">{d.country}</p>
          <h3 className={`mt-1.5 font-display leading-tight ${large ? "text-4xl md:text-5xl" : "text-2xl"}`}>
            {d.name}
          </h3>
          <p className="eyebrow mt-2 flex flex-wrap items-center gap-x-2.5 text-ivory/75">
            <span className="text-vogo">{d.stays}</span>
            <span aria-hidden className="text-ivory/30">
              ·
            </span>
            {d.from}
          </p>
        </div>
        <span
          aria-hidden
          className="shrink-0 text-vogo opacity-0 transition-all duration-500 group-hover:translate-x-1 group-hover:opacity-100"
        >
          →
        </span>
      </div>
    </a>
  );
}

export function Destinations() {
  return (
    <section id="destinations" className="bg-ivory py-20 text-charcoal md:py-28">
      <div className="mx-auto max-w-[1500px] px-6 md:px-10">
        <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
          <div>
            <p className="eyebrow text-navy-soft">Destinations</p>
            <h2 className="mt-4 font-display text-[clamp(2rem,4vw,3.4rem)] leading-[1.06]">
              <MaskLine>Recommended destinations</MaskLine>
            </h2>
          </div>
          <Reveal className="max-w-xs md:text-right">
            <p className="text-sm leading-relaxed text-muted-foreground">
              Where Vogo travelers are booking right now — with live availability from every partner.
            </p>
          </Reveal>
        </div>

        <div className="mt-12 grid gap-5 lg:grid-cols-2">
          {FEATURED.map((d, i) => (
            <Reveal key={d.name} delay={i * 0.05}>
              <Card d={d} large />
            </Reveal>
          ))}
        </div>

        <div className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {SMALL.map((d, i) => (
            <Reveal key={d.name} delay={i * 0.04}>
              <Card d={d} />
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
