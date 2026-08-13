import { motion } from "framer-motion";
import type { ReactNode } from "react";

export function Reveal({
  children,
  delay = 0,
  y = 28,
  className,
}: {
  children: ReactNode;
  delay?: number;
  y?: number;
  className?: string;
}) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.8, delay, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </motion.div>
  );
}

export function SectionHeading({
  eyebrow,
  title,
  sub,
  tone = "light",
  align = "left",
}: {
  eyebrow?: string;
  title: string;
  sub?: string;
  tone?: "light" | "dark";
  align?: "left" | "center";
}) {
  const dark = tone === "dark";
  return (
    <Reveal className={align === "center" ? "text-center" : ""}>
      {eyebrow && (
        <span
          className={`eyebrow block ${dark ? "text-accent" : "text-accent"}`}
        >
          {eyebrow}
        </span>
      )}
      <h2
        className={`display-xl mt-5 max-w-4xl text-4xl sm:text-5xl lg:text-6xl ${
          align === "center" ? "mx-auto" : ""
        } ${dark ? "text-ink-foreground" : "text-foreground"}`}
      >
        {title}
      </h2>
      {sub && (
        <p
          className={`mt-5 max-w-xl text-base leading-relaxed ${
            align === "center" ? "mx-auto" : ""
          } ${dark ? "text-ink-muted" : "text-muted-foreground"}`}
        >
          {sub}
        </p>
      )}
    </Reveal>
  );
}
