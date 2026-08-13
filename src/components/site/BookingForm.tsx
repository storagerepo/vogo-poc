import { useState, type FormEvent } from "react";
import { Check } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { vehicles, locations } from "@/data/vehicles";

export function BookingForm({
  tone = "dark",
  defaultVehicle = "",
}: {
  tone?: "light" | "dark";
  defaultVehicle?: string;
}) {
  const { t, lang } = useI18n();
  const [done, setDone] = useState(false);
  const dark = tone === "dark";

  const field = dark
    ? "w-full border-b border-white/15 bg-transparent py-3 text-sm text-white outline-none transition-colors placeholder:text-white/20 focus:border-[#FFC72C]"
    : "w-full border-b border-[#e8e8e8] bg-transparent py-3 text-sm text-[#080808] outline-none transition-colors placeholder:text-[#A0A0A0] focus:border-[#FFC72C]";
  const label = `eyebrow mb-1 block text-[10px] tracking-[0.2em] ${dark ? "text-white/40" : "text-[#A0A0A0]"}`;

  function submit(e: FormEvent) {
    e.preventDefault();
    setDone(true);
  }

  if (done) {
    return (
      <div
        className={`flex items-center gap-3 border p-6 ${
          dark ? "border-white/15 text-white" : "border-[#e8e8e8] text-[#080808]"
        }`}
      >
        <span className="flex h-9 w-9 items-center justify-center bg-[#FFC72C] text-[#080808]">
          <Check className="h-4 w-4" />
        </span>
        <p className="text-sm">{t.testdrive.success}</p>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="grid grid-cols-1 gap-6 sm:grid-cols-2">
      <div>
        <label className={label} htmlFor="td-name">{t.testdrive.name}</label>
        <input id="td-name" required className={field} placeholder="—" />
      </div>
      <div>
        <label className={label} htmlFor="td-email">{t.testdrive.email}</label>
        <input id="td-email" type="email" required className={field} placeholder="—" />
      </div>
      <div>
        <label className={label} htmlFor="td-phone">{t.testdrive.phone}</label>
        <input id="td-phone" type="tel" required className={field} placeholder="—" />
      </div>
      <div>
        <label className={label} htmlFor="td-vehicle">{t.testdrive.vehicle}</label>
        <select id="td-vehicle" defaultValue={defaultVehicle} className={`${field} ${dark ? "[&>option]:text-foreground" : ""}`}>
          <option value="">{t.testdrive.select}</option>
          {vehicles.map((v) => (
            <option key={v.id} value={`${v.brand} ${v.model}`}>
              {v.brand} {v.model}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className={label} htmlFor="td-date">{t.testdrive.date}</label>
        <input id="td-date" type="date" required className={field} />
      </div>
      <div>
        <label className={label} htmlFor="td-loc">{t.testdrive.location}</label>
        <select id="td-loc" className={`${field} ${dark ? "[&>option]:text-foreground" : ""}`}>
          {locations.map((l) => (
            <option key={l.id} value={l.id}>
              {l.name[lang]}
            </option>
          ))}
        </select>
      </div>
      <div className="sm:col-span-2">
        <button
          type="submit"
          className={`eyebrow w-full px-8 py-4 text-[11px] font-bold tracking-[0.25em] transition-all sm:w-auto ${
            dark
              ? "bg-[#FFC72C] text-[#080808] hover:bg-white"
              : "bg-[#080808] text-white hover:bg-[#FFC72C] hover:text-[#080808]"
          }`}
        >
          {t.testdrive.cta}
        </button>
      </div>
    </form>
  );
}
