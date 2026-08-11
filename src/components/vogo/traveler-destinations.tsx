import alps from "@/assets/alps.jpg";
import amalfi from "@/assets/amalfi.jpg";
import bali from "@/assets/bali.jpg";
import maldives from "@/assets/maldives.jpg";
import paris from "@/assets/paris.jpg";
import prop1 from "@/assets/prop-1.jpg";
import prop2 from "@/assets/prop-2.jpg";
import prop3 from "@/assets/prop-3.jpg";
import prop4 from "@/assets/prop-4.jpg";
import tokyo from "@/assets/tokyo.jpg";
import { MaskLine, Reveal } from "@/components/vogo/reveal";

const CITIES = [
  { name: "New York", region: "New York, US", stays: "12,400 stays", img: paris },
  { name: "Miami", region: "Florida, US", stays: "8,120 stays", img: prop3 },
  { name: "San Diego", region: "California, US", stays: "6,940 stays", img: prop1 },
  { name: "Lake Tahoe", region: "California, US", stays: "3,210 stays", img: alps },
  { name: "Chicago", region: "Illinois, US", stays: "5,470 stays", img: tokyo },
  { name: "Gatlinburg", region: "Tennessee, US", stays: "4,180 stays", img: prop2 },
  { name: "Myrtle Beach", region: "South Carolina, US", stays: "7,050 stays", img: maldives },
  { name: "Orange Beach", region: "Alabama, US", stays: "2,860 stays", img: bali },
  { name: "Destin", region: "Florida, US", stays: "3,940 stays", img: prop4 },
  { name: "Hilton Head Island", region: "South Carolina, US", stays: "2,310 stays", img: amalfi },
];

/** Compact, SEO-friendly destination list with small thumbnails. */
export function TravelerDestinations() {
  return (
    <section aria-label="Popular destinations" className="border-t border-border bg-ivory py-20 text-charcoal md:py-28">
      <div className="mx-auto max-w-[1500px] px-6 md:px-10">
        <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
          <div>
            <p className="eyebrow text-navy-soft">Popular right now</p>
            <h2 className="mt-4 font-display text-[clamp(1.9rem,3.6vw,3.1rem)] leading-[1.06]">
              <MaskLine>Explore where travelers are staying</MaskLine>
            </h2>
          </div>
          <Reveal className="max-w-xs md:text-right">
            <p className="text-sm leading-relaxed text-muted-foreground">
              The cities and coastlines with the most bookings on Vogo this month.
            </p>
          </Reveal>
        </div>

        <ul className="mt-10 grid gap-x-8 gap-y-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {CITIES.map((c) => (
            <li key={c.name}>
              <a
                href="#stays"
                className="group flex items-center gap-4 border-b border-border py-3.5 transition-colors hover:border-navy/30"
              >
                <img
                  src={c.img}
                  alt=""
                  width={96}
                  height={96}
                  loading="lazy"
                  decoding="async"
                  className="h-12 w-12 shrink-0 rounded-lg object-cover"
                />
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-display text-xl leading-tight">{c.name}</span>
                  <span className="eyebrow block truncate text-muted-foreground">{c.stays}</span>
                </span>
                <span
                  aria-hidden
                  className="shrink-0 text-navy-soft opacity-0 transition-all duration-300 group-hover:translate-x-0.5 group-hover:opacity-100"
                >
                  →
                </span>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
