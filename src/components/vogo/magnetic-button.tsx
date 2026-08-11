import { motion, useMotionValue, useSpring } from "framer-motion";
import { useRef, type ReactNode } from "react";

import { useReducedMotion } from "@/hooks/use-reduced-motion";

type Props = {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
  strength?: number;
};

/** Button whose label leans toward the cursor — subtle, controlled magnetism. */
export function MagneticButton({ children, className = "", onClick, strength = 14 }: Props) {
  const ref = useRef<HTMLButtonElement>(null);
  const reduced = useReducedMotion();
  const x = useSpring(useMotionValue(0), { stiffness: 180, damping: 18 });
  const y = useSpring(useMotionValue(0), { stiffness: 180, damping: 18 });

  return (
    <motion.button
      ref={ref}
      type="button"
      onClick={onClick}
      className={className}
      style={{ x, y }}
      onPointerMove={(e) => {
        if (reduced || !ref.current) return;
        const r = ref.current.getBoundingClientRect();
        x.set(((e.clientX - (r.left + r.width / 2)) / r.width) * strength * 2);
        y.set(((e.clientY - (r.top + r.height / 2)) / r.height) * strength * 2);
      }}
      onPointerLeave={() => {
        x.set(0);
        y.set(0);
      }}
    >
      {children}
    </motion.button>
  );
}
