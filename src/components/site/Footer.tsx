import { Facebook, Instagram, Linkedin, Youtube } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { brands } from "@/data/vehicles";

export function Footer() {
  const { t, lang, setLang } = useI18n();

  const cols = [
    {
      title: t.footer.vehicles,
      links: [t.vehicles.suvs, t.vehicles.sedans, t.vehicles.pickups, t.vehicles.commercial, t.vehicles.motorcycles],
      href: "#vehicles",
    },
    { title: t.footer.brands, links: brands, href: "#brands" },
    { title: t.footer.services, links: t.services.items.map((s) => s.t), href: "#services" },
    {
      title: t.footer.company,
      links: [t.footer.about, t.footer.careers, t.footer.press, t.footer.news],
      href: "#about",
    },
  ];

  return (
    <footer className="bg-[#080808] pt-16 text-white">
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
        {/* Top row — brand + cols */}
        <div className="grid grid-cols-2 gap-10 border-b border-white/10 pb-14 md:grid-cols-3 lg:grid-cols-6">
          {/* Brand */}
          <div className="col-span-2 lg:col-span-2">
            <a href="#top" className="flex items-center gap-2.5">
              <img src="/logo.svg" alt="Santo Domingo Motors" className="h-10 w-10 object-contain border border-white/10" />
              <div className="flex flex-col font-display uppercase leading-[0.9] text-white">
                <span className="text-sm font-bold tracking-[0.05em]">Santo Domingo</span>
                <span className="text-[10px] tracking-[0.25em] text-[#FFC72C]">Motors</span>
              </div>
            </a>
            <p className="mt-3 max-w-xs text-sm text-white/40">{t.footer.tagline}</p>
            <div className="mt-6 flex gap-4">
              {[Instagram, Facebook, Youtube, Linkedin].map((Icon, i) => (
                <a
                  key={i}
                  href="#top"
                  aria-label="Social"
                  className="text-white/30 transition-colors hover:text-[#FFC72C]"
                >
                  <Icon className="h-[18px] w-[18px]" strokeWidth={1.5} />
                </a>
              ))}
            </div>
          </div>

          {/* Nav columns */}
          {cols.map((c) => (
            <div key={c.title}>
              <h4 className="eyebrow text-[10px] tracking-[0.2em] text-white/50">{c.title}</h4>
              <ul className="mt-4 space-y-2.5">
                {c.links.map((l) => (
                  <li key={l}>
                    <a
                      href={c.href}
                      className="text-sm text-white/40 transition-colors hover:text-[#FFC72C]"
                    >
                      {l}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Contact + language row */}
        <div className="grid grid-cols-1 gap-8 border-b border-white/10 py-10 sm:grid-cols-3">
          <div>
            <h4 className="eyebrow text-[10px] tracking-[0.2em] text-white/50">{t.footer.contact}</h4>
            <p className="mt-3 text-sm text-white/50">{t.footer.phone}</p>
            <p className="text-sm text-white/50">{t.footer.email}</p>
          </div>
          <div className="sm:col-span-2 sm:justify-self-end">
            {/* Language switcher */}
            <div className="flex items-center gap-1 text-[11px] font-semibold tracking-[0.15em]">
              {(["en", "es"] as const).map((l, i) => (
                <span key={l} className="flex items-center gap-1">
                  {i === 1 && <span className="text-white/20">|</span>}
                  <button
                    onClick={() => setLang(l)}
                    className={`uppercase transition-colors hover:text-[#FFC72C] ${
                      lang === l ? "text-[#FFC72C]" : "text-white/30"
                    }`}
                  >
                    {l}
                  </button>
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col gap-4 py-7 text-xs text-white/25 sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} Santo Domingo Motors. {t.footer.rights}</p>
          <div className="flex gap-6">
            <a href="#top" className="transition-colors hover:text-[#FFC72C]">{t.footer.privacy}</a>
            <a href="#top" className="transition-colors hover:text-[#FFC72C]">{t.footer.terms}</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
