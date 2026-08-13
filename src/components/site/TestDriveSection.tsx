import { useI18n } from "@/lib/i18n";
import { Reveal, SectionHeading } from "./Reveal";
import { BookingForm } from "./BookingForm";

export function TestDriveSection() {
  const { t } = useI18n();
  return (
    <section id="testdrive" className="border-b border-border bg-background py-24 sm:py-32">
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
        <div className="grid grid-cols-1 gap-14 lg:grid-cols-[0.9fr_1.1fr] lg:gap-20">
          <SectionHeading eyebrow={t.testdrive.eyebrow} title={t.testdrive.title} sub={t.testdrive.sub} />
          <Reveal delay={0.1}>
            <div className="border border-border p-7 sm:p-10">
              <BookingForm />
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
