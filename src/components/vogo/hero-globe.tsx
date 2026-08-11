import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

import { useReducedMotion } from "@/hooks/use-reduced-motion";

const MARKERS: { name: string; lat: number; lon: number }[] = [
  { name: "Bali", lat: -8.4, lon: 115.2 },
  { name: "Tokyo", lat: 35.7, lon: 139.7 },
  { name: "Amalfi", lat: 40.6, lon: 14.6 },
  { name: "Maldives", lat: 3.2, lon: 73.2 },
];

const R = 1.35;

function toVec(lat: number, lon: number, r = R) {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -r * Math.sin(phi) * Math.cos(theta),
    r * Math.cos(phi),
    r * Math.sin(phi) * Math.sin(theta),
  );
}

function Globe({ reduced }: { reduced: boolean }) {
  const group = useRef<THREE.Group>(null);
  const markers = useMemo(() => MARKERS.map((m) => ({ ...m, pos: toVec(m.lat, m.lon, R * 1.01) })), []);

  const dots = useMemo(() => {
    // Fibonacci sphere of fine points — a drawn, engraved-looking globe.
    const count = 1600;
    const arr = new Float32Array(count * 3);
    const golden = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < count; i++) {
      const y = 1 - (i / (count - 1)) * 2;
      const radius = Math.sqrt(Math.max(0, 1 - y * y));
      const theta = golden * i;
      arr.set([Math.cos(theta) * radius * R, y * R, Math.sin(theta) * radius * R], i * 3);
    }
    return arr;
  }, []);

  useFrame((state, delta) => {
    if (!group.current) return;
    if (!reduced) group.current.rotation.y += delta * 0.07;
    const { x, y } = state.pointer;
    group.current.rotation.x += (y * 0.28 - group.current.rotation.x) * 0.04;
    group.current.position.x += (x * 0.12 - group.current.position.x) * 0.04;
  });

  return (
    <group ref={group}>
      <points>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[dots, 3]} />
        </bufferGeometry>
        <pointsMaterial size={0.013} color="#f7f5ef" transparent opacity={0.55} sizeAttenuation />
      </points>

      <mesh>
        <sphereGeometry args={[R * 0.995, 48, 48]} />
        <meshBasicMaterial color="#17243d" transparent opacity={0.62} />
      </mesh>

      <mesh>
        <sphereGeometry args={[R * 1.001, 24, 18]} />
        <meshBasicMaterial color="#f7f5ef" wireframe transparent opacity={0.08} />
      </mesh>

      {markers.map((m) => (
        <group key={m.name} position={m.pos}>
          <mesh>
            <sphereGeometry args={[0.022, 12, 12]} />
            <meshBasicMaterial color="#ffd400" />
          </mesh>
          <mesh>
            <ringGeometry args={[0.045, 0.052, 32]} />
            <meshBasicMaterial color="#ffd400" transparent opacity={0.5} side={THREE.DoubleSide} />
          </mesh>
        </group>
      ))}
    </group>
  );
}

export default function HeroGlobe() {
  const reduced = useReducedMotion();

  return (
    <Canvas
      className="!absolute inset-0"
      dpr={[1, 1.6]}
      gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
      camera={{ position: [0, 0, 4.9], fov: 40 }}
      frameloop={reduced ? "demand" : "always"}
    >
      <Globe reduced={reduced} />
    </Canvas>
  );
}
