import { useState } from "react";
import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { Reveal } from "./Reveal";

export function Financing() {
  const { t, lang } = useI18n();
  const [price, setPrice] = useState(52900);
  const [down, setDown] = useState(10000);
  const [term, setTerm] = useState(60);
  const [rate, setRate] = useState(8.5);
  const [result, setResult] = useState<{ monthly: number; financed: number; interest: number } | null>(
    null,
  );

  const fmt = (n: number) =>
    new Intl.NumberFormat(lang === "es" ? "es-DO" : "en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(Math.max(0, Math.round(n)));

  function calculate() {
    const financed = Math.max(0, price - down);
    const r = rate / 100 / 12;
    const monthly = r === 0 ? financed / term : (financed * r) / (1 - Math.pow(1 + r, -term));
    setResult({ monthly, financed, interest: monthly * term - financed });
  }

  const inputCls =
    "w-full border-b border-white/15 bg-transparent py-3 font-display text-3xl uppercase text-white outline-none transition-colors focus:border-[#FFC72C] placeholder:text-white/20";
  const labelCls = "eyebrow text-[10px] tracking-[0.25em] text-white/40";

  return (
    <section id="financing" className="bg-[#080808] py-20 sm:py-28">
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
        <div className="grid grid-cols-1 gap-14 lg:grid-cols-2 lg:gap-20">
          {/* Left — headline */}
          <Reveal>
            <span className="eyebrow text-[10px] tracking-[0.3em] text-[#FFC72C]">
              {t.financing.eyebrow}
            </span>
            <h2 className="display-xl mt-4 text-5xl text-white sm:text-6xl lg:text-7xl">
              {t.financing.title}
            </h2>
            <p className="mt-5 text-base text-white/40">{t.financing.sub}</p>

            {/* Yellow accent line */}
            <div className="mt-8 h-0.5 w-16 bg-[#FFC72C]" />
          </Reveal>

          {/* Right — calculator */}
          <Reveal delay={0.1}>
            <div className="border border-white/10 p-7 sm:p-10">
              <div className="grid grid-cols-1 gap-7 sm:grid-cols-2">
                <div>
                  <label className={labelCls} htmlFor="fin-price">{t.financing.price}</label>
                  <input
                    id="fin-price"
                    type="number"
                    min={0}
                    value={price}
                    onChange={(e) => setPrice(Number(e.target.value))}
                    className={inputCls}
                  />
                </div>
                <div>
                  <label className={labelCls} htmlFor="fin-down">{t.financing.down}</label>
                  <input
                    id="fin-down"
                    type="number"
                    min={0}
                    value={down}
                    onChange={(e) => setDown(Number(e.target.value))}
                    className={inputCls}
                  />
                </div>
                <div>
                  <label className={labelCls} htmlFor="fin-term">{t.financing.term}</label>
                  <input
                    id="fin-term"
                    type="number"
                    min={12}
                    max={96}
                    value={term}
                    onChange={(e) => setTerm(Math.max(1, Number(e.target.value)))}
                    className={inputCls}
                  />
                </div>
                <div>
                  <label className={labelCls} htmlFor="fin-rate">{t.financing.rate}</label>
                  <input
                    id="fin-rate"
                    type="number"
                    step="0.1"
                    min={0}
                    value={rate}
                    onChange={(e) => setRate(Number(e.target.value))}
                    className={inputCls}
                  />
                </div>
              </div>

              <button
                onClick={calculate}
                className="eyebrow mt-10 w-full bg-[#FFC72C] px-8 py-4 text-[11px] font-bold tracking-[0.25em] text-[#080808] transition-all hover:bg-white"
              >
                {t.financing.calc}
              </button>

              {result && (
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                  className="mt-8 border-t border-white/10 pt-8"
                >
                  <span className={labelCls}>{t.financing.monthly}</span>
                  <p className="mt-2 font-display text-5xl uppercase text-[#FFC72C] sm:text-6xl">
                    {fmt(result.monthly)}
                  </p>
                  <div className="mt-6 grid grid-cols-2 gap-6">
                    <div>
                      <span className={labelCls}>{t.financing.financed}</span>
                      <p className="mt-1 font-display text-xl uppercase text-white">{fmt(result.financed)}</p>
                    </div>
                    <div>
                      <span className={labelCls}>{t.financing.totalInterest}</span>
                      <p className="mt-1 font-display text-xl uppercase text-white">{fmt(result.interest)}</p>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
