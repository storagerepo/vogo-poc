import prop1 from "@/assets/prop-1.jpg";
import prop2 from "@/assets/prop-2.jpg";
import prop3 from "@/assets/prop-3.jpg";
import prop4 from "@/assets/prop-4.jpg";
import cabin from "@/assets/type-cabin.jpg";
import cottage from "@/assets/type-cottage.jpg";
import alps from "@/assets/alps.jpg";
import casaMare from "@/assets/casa-mare.jpg";
import { MaskLine, Reveal } from "@/components/vogo/reveal";

type Property = {
  tag: string;
  name: string;
  type: string;
  location: string;
  img: string;
  rating: string;
  verdict: string;
  reviews: string;
  partner: string;
  price: string;
};

const PROPERTIES: Property[] = [
  {
    tag: "Coastal",
    name: "The Pole House",
    type: "House",
    location: "Aireys Inlet, Australia",
    img: alps,
    rating: "9.0",
    verdict: "Outstanding",
    reviews: "1,204 reviews",
    partner: "Booking.com",
    price: "$$$$",
  },
  {
    tag: "City stay",
    name: "Maison Sixième",
    type: "Apartment",
    location: "Paris, France",
    img: prop2,
    rating: "9.4",
    verdict: "Exceptional",
    reviews: "862 reviews",
    partner: "Vrbo",
    price: "$$$",
  },
  {
    tag: "Overwater",
    name: "Lagoon Water Villa",
    type: "Resort",
    location: "North Atoll, Maldives",
    img: prop3,
    rating: "9.8",
    verdict: "Exceptional",
    reviews: "540 reviews",
    partner: "Expedia",
    price: "$$$$",
  },
  {
    tag: "Cliffside",
    name: "Casa Mare Terrazza",
    type: "Hotel",
    location: "Amalfi Coast, Italy",
    img: casaMare,
    rating: "9.7",
    verdict: "Exceptional",
    reviews: "1,041 reviews",
    partner: "Agoda",
    price: "$$$$",
  },
  {
    tag: "Jungle",
    name: "Ubud Palm Retreat",
    type: "Villa",
    location: "Bali, Indonesia",
    img: prop1,
    rating: "9.6",
    verdict: "Exceptional",
    reviews: "1,320 reviews",
    partner: "Agoda",
    price: "$$$",
  },
  {
    tag: "Old town",
    name: "Terrazza Marina Suites",
    type: "Boutique hotel",
    location: "Positano, Italy",
    img: prop4,
    rating: "9.2",
    verdict: "Outstanding",
    reviews: "704 reviews",
    partner: "Hotels.com",
    price: "$$$",
  },
  {
    tag: "Countryside",
    name: "Willow Lane Cottage",
    type: "Cottage",
    location: "Cotswolds, England",
    img: cottage,
    rating: "8.9",
    verdict: "Very good",
    reviews: "398 reviews",
    partner: "Novasol",
    price: "$$",
  },
  {
    tag: "Forest",
    name: "Northline Cabin",
    type: "Cabin",
    location: "Lake Tahoe, US",
    img: cabin,
    rating: "9.1",
    verdict: "Outstanding",
    reviews: "512 reviews",
    partner: "Evolve",
    price: "$$",
  },
];

function PropertyCard({ p }: { p: Property }) {
  return (
    <article
      data-cursor="grow"
      className="group flex w-[76vw] shrink-0 snap-center flex-col overflow-hidden rounded-[20px] border border-border bg-card shadow-[0_1px_2px_rgba(23,36,61,0.04)] transition-[transform,box-shadow] duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] hover:-translate-y-1 hover:shadow-[0_18px_40px_-22px_rgba(23,36,61,0.35)] sm:w-[46vw] lg:w-auto"
    >
      <div className="relative aspect-[4/3] overflow-hidden">
        <img
          src={p.img}
          alt={`${p.name} — ${p.type} in ${p.location}`}
          width={900}
          height={675}
          loading="lazy"
          decoding="async"
          className="h-full w-full object-cover transition-transform duration-[900ms] ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-[1.05]"
        />
        <span className="eyebrow absolute top-3.5 left-3.5 rounded-full bg-ivory/90 px-3 py-1.5 text-charcoal backdrop-blur-sm">
          {p.tag}
        </span>
        <span className="absolute top-3.5 right-3.5 flex items-center gap-2 rounded-full bg-navy px-3 py-1.5 text-ivory">
          <span className="font-display text-base leading-none">
            {p.rating}
            <span className="text-ivory/50"> / 10</span>
          </span>
          <span className="h-1.5 w-1.5 rounded-full bg-vogo" aria-hidden />
        </span>
      </div>

      <div className="flex flex-1 flex-col p-5">
        <p className="eyebrow text-navy-soft">
          {p.verdict} <span className="text-muted-foreground">· {p.reviews}</span>
        </p>
        <h3 className="mt-2 font-display text-2xl leading-tight">{p.name}</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          {p.type} in {p.location}
        </p>

        <div className="mt-4 flex items-center justify-between gap-3 border-t border-border pt-4">
          <div className="min-w-0">
            <p className="font-display text-lg leading-none tracking-wide">{p.price}</p>
            <p className="mt-1.5 truncate text-[0.7rem] tracking-[0.08em] text-muted-foreground uppercase">
              via {p.partner}
            </p>
          </div>
          <button
            type="button"
            className="eyebrow shrink-0 rounded-full bg-navy px-4 py-2.5 whitespace-nowrap text-ivory transition-colors duration-300 group-hover:bg-vogo group-hover:text-navy"
          >
            View Deal
          </button>
        </div>
      </div>
    </article>
  );
}

export function TrendingProperties() {
  return (
    <section id="stays" className="bg-ivory py-20 text-charcoal md:py-28">
      <div className="mx-auto max-w-[1500px] px-6 md:px-10">
        <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
          <div>
            <p className="eyebrow text-navy-soft">Trending now</p>
            <h2 className="mt-4 font-display text-[clamp(2rem,4vw,3.4rem)] leading-[1.06]">
              <MaskLine>Trending Properties</MaskLine>
            </h2>
          </div>
          <Reveal className="max-w-sm md:text-right">
            <p className="text-sm leading-relaxed text-muted-foreground">
              Discover top-rated stays — handpicked for exceptional quality, guest satisfaction, and unforgettable
              stays.
            </p>
          </Reveal>
        </div>

        <div className="hide-scrollbar mt-12 flex snap-x snap-mandatory gap-5 overflow-x-auto pb-4 lg:grid lg:grid-cols-4 lg:gap-6 lg:overflow-visible lg:pb-0">
          {PROPERTIES.map((p, i) => (
            <Reveal key={p.name} delay={(i % 4) * 0.05} className="flex lg:block">
              <PropertyCard p={p} />
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
