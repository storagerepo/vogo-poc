const PARTNERS = [
  "Agoda",
  "Booking.com",
  "AvantStay",
  "Evolve",
  "Expedia",
  "Hotels.com",
  "Novasol",
  "Outdoorsy",
  "Priceline",
  "RedAwning",
  "Vrbo",
];

/** Muted partner wordmark strip — Vogo compares prices across these sources. */
export function PartnerStrip() {
  return (
    <section aria-label="Booking partners" className="border-b border-border bg-ivory">
      <div className="mx-auto max-w-[1500px] px-6 py-10 md:px-10 md:py-12">
        <p className="eyebrow text-muted-foreground">
          Comparing <span className="text-charcoal">9.8+ million properties</span> across
        </p>
        <ul className="hide-scrollbar mt-6 flex items-center gap-x-10 gap-y-4 overflow-x-auto md:flex-wrap md:gap-x-12 md:overflow-visible">
          {PARTNERS.map((p) => (
            <li
              key={p}
              className="shrink-0 font-display text-xl whitespace-nowrap text-charcoal/40 transition-colors duration-500 hover:text-charcoal md:text-2xl"
            >
              {p}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
