import { motion, useMotionValue, useSpring } from "framer-motion";
import { useEffect, useState } from "react";

import { useIsDesktop, useReducedMotion } from "@/hooks/use-reduced-motion";

/** Desktop-only editorial cursor: a thin ring that grows over interactive elements. */
export function CustomCursor() {
  const isDesktop = useIsDesktop();
  const reduced = useReducedMotion();
  const [active, setActive] = useState(false);
  const [visible, setVisible] = useState(false);
  const raw = { x: useMotionValue(-100), y: useMotionValue(-100) };
  const x = useSpring(raw.x, { stiffness: 500, damping: 40, mass: 0.4 });
  const y = useSpring(raw.y, { stiffness: 500, damping: 40, mass: 0.4 });

  useEffect(() => {
    if (!isDesktop || reduced) return;
    const move = (e: PointerEvent) => {
      raw.x.set(e.clientX);
      raw.y.set(e.clientY);
      setVisible(true);
      const el = e.target as HTMLElement | null;
      setActive(!!el?.closest("a, button, [data-cursor='grow']"));
    };
    const leave = () => setVisible(false);
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerleave", leave);
    return () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerleave", leave);
    };
  }, [isDesktop, reduced, raw.x, raw.y]);

  if (!isDesktop || reduced) return null;

  return (
    <motion.div
      aria-hidden
      className="pointer-events-none fixed top-0 left-0 z-[100] mix-blend-difference"
      style={{ x, y }}
    >
      <motion.div
        className="rounded-full border border-ivory"
        animate={{
          width: active ? 56 : 16,
          height: active ? 56 : 16,
          opacity: visible ? 1 : 0,
          x: active ? -28 : -8,
          y: active ? -28 : -8,
        }}
        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      />
    </motion.div>
  );
}
