import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";

const items = [
  { key: "accessories" as const, href: "#services" },
  { key: "app" as const, href: "#top" },
  { key: "services" as const, href: "#services" },
  { key: "branches" as const, href: "#locations" },
  { key: "financing" as const, href: "#financing" },
];

export function QuickAccess() {
  const { t } = useI18n();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="relative z-20 bg-[#080808] border-y border-white/10"
    >
      <div className="mx-auto max-w-[1400px] px-0">
        {/* Horizontal scrollable on mobile, flex on desktop */}
        <div className="-mx-0 flex overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {items.map((item, i) => (
            <a
              key={item.key}
              href={item.href}
              className={`group relative flex shrink-0 flex-1 flex-col items-center justify-center gap-1.5 border-r border-white/10 px-6 py-5 text-center transition-all duration-300 hover:bg-[#FFC72C] last:border-r-0 min-w-[140px] sm:min-w-0 ${
                i === 0 ? "bg-[#FFC72C] text-[#080808]" : "text-white/70 hover:text-[#080808]"
              }`}
            >
              <span
                className={`eyebrow text-[10px] tracking-[0.2em] transition-colors font-bold ${
                  i === 0 ? "text-[#080808]" : "group-hover:text-[#080808]"
                }`}
              >
                {t.quickAccess[item.key]}
              </span>
            </a>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
