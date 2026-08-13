import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { useEffect } from "react";
import { useI18n } from "@/lib/i18n";
import { useTestDrive } from "./TestDriveContext";
import { BookingForm } from "./BookingForm";

export function TestDriveModal() {
  const { open, vehicle, closeModal } = useTestDrive();
  const { t } = useI18n();

  useEffect(() => {
    if (typeof document === "undefined") return;
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-end justify-center sm:items-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <button
            aria-label="Close"
            onClick={closeModal}
            className="absolute inset-0 bg-black/80"
          />
          <motion.div
            key={vehicle}
            initial={{ y: 40, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 20, opacity: 0 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="relative max-h-[92vh] w-full max-w-2xl overflow-y-auto bg-[#080808] p-7 sm:p-10"
          >
            <button
              onClick={closeModal}
              aria-label="Close"
              className="absolute right-5 top-5 text-white/40 transition-colors hover:text-[#FFC72C]"
            >
              <X className="h-5 w-5" />
            </button>
            <span className="eyebrow text-[10px] tracking-[0.3em] text-[#FFC72C]">{t.testdrive.eyebrow}</span>
            <h3 className="display-xl mt-4 text-3xl text-white sm:text-4xl">{t.testdrive.title}</h3>
            <p className="mt-3 text-sm text-white/50">{t.testdrive.sub}</p>
            <div className="mt-8">
              <BookingForm defaultVehicle={vehicle} />
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
