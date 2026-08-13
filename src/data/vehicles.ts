import suv from "@/assets/v-suv.jpg";
import sedan from "@/assets/v-sedan.jpg";
import pickup from "@/assets/v-pickup.jpg";
import van from "@/assets/v-van.jpg";
import moto from "@/assets/v-moto.jpg";
import crossover from "@/assets/v-crossover.jpg";

export type Category = "suvs" | "sedans" | "pickups" | "commercial" | "motorcycles";

export type Vehicle = {
  id: string;
  brand: string;
  model: string;
  category: Category;
  spec: { en: string; es: string };
  price: number;
  image: string;
};

export const vehicles: Vehicle[] = [
  {
    id: "pathfinder",
    brand: "Nissan",
    model: "Pathfinder Platinum",
    category: "suvs",
    spec: { en: "3.5L V6 · AWD · 7 seats", es: "3.5L V6 · AWD · 7 plazas" },
    price: 52900,
    image: suv,
  },
  {
    id: "escalade",
    brand: "Cadillac",
    model: "Escalade Sport",
    category: "suvs",
    spec: { en: "6.2L V8 · 4WD · 8 seats", es: "6.2L V8 · 4WD · 8 plazas" },
    price: 98400,
    image: crossover,
  },
  {
    id: "q50",
    brand: "Infiniti",
    model: "Q50 Red Sport",
    category: "sedans",
    spec: { en: "3.0L Twin-Turbo · 400 hp", es: "3.0L Biturbo · 400 hp" },
    price: 61200,
    image: sedan,
  },
  {
    id: "altima",
    brand: "Nissan",
    model: "Altima SR",
    category: "sedans",
    spec: { en: "2.0L VC-Turbo · CVT", es: "2.0L VC-Turbo · CVT" },
    price: 34500,
    image: sedan,
  },
  {
    id: "silverado",
    brand: "Chevrolet",
    model: "Silverado High Country",
    category: "pickups",
    spec: { en: "5.3L V8 · 4x4 · Tow 5.4t", es: "5.3L V8 · 4x4 · Arrastre 5.4t" },
    price: 71800,
    image: pickup,
  },
  {
    id: "frontier",
    brand: "Nissan",
    model: "Frontier PRO-4X",
    category: "pickups",
    spec: { en: "3.8L V6 · 4x4 · Off-road", es: "3.8L V6 · 4x4 · Todoterreno" },
    price: 46300,
    image: pickup,
  },
  {
    id: "express",
    brand: "Chevrolet",
    model: "Express Cargo 2500",
    category: "commercial",
    spec: { en: "Diesel · 12.5 m³ cargo", es: "Diésel · 12.5 m³ de carga" },
    price: 43900,
    image: van,
  },
  {
    id: "carry",
    brand: "Suzuki",
    model: "Carry Pro",
    category: "commercial",
    spec: { en: "1.5L · 940 kg payload", es: "1.5L · 940 kg de carga" },
    price: 21700,
    image: van,
  },
  {
    id: "mt09",
    brand: "Yamaha",
    model: "MT-09 SP",
    category: "motorcycles",
    spec: { en: "890cc · 117 hp · Quickshift", es: "890cc · 117 hp · Quickshift" },
    price: 12400,
    image: moto,
  },
  {
    id: "gsx",
    brand: "Suzuki",
    model: "GSX-8S",
    category: "motorcycles",
    spec: { en: "776cc parallel-twin · 82 hp", es: "776cc bicilíndrico · 82 hp" },
    price: 9800,
    image: moto,
  },
  {
    id: "vitara",
    brand: "Suzuki",
    model: "Grand Vitara AllGrip",
    category: "suvs",
    spec: { en: "1.5L Hybrid · AWD", es: "1.5L Híbrido · AWD" },
    price: 29900,
    image: crossover,
  },
  {
    id: "malibu",
    brand: "Chevrolet",
    model: "Malibu Premier",
    category: "sedans",
    spec: { en: "2.0L Turbo · 9-speed", es: "2.0L Turbo · 9 velocidades" },
    price: 32100,
    image: sedan,
  },
];

export const usedVehicles = [
  {
    id: "u1",
    brand: "Infiniti",
    model: "QX60 Luxe",
    year: 2022,
    km: 38400,
    price: 41900,
    image: crossover,
    spec: { en: "3.5L V6 · AWD · One owner", es: "3.5L V6 · AWD · Único dueño" },
  },
  {
    id: "u2",
    brand: "Chevrolet",
    model: "Tahoe LT",
    year: 2021,
    km: 52100,
    price: 47500,
    image: suv,
    spec: { en: "5.3L V8 · 7 seats · Certified", es: "5.3L V8 · 7 plazas · Certificado" },
  },
  {
    id: "u3",
    brand: "Nissan",
    model: "Sentra SR",
    year: 2023,
    km: 19700,
    price: 22800,
    image: sedan,
    spec: { en: "2.0L · CVT · Warranty", es: "2.0L · CVT · Con garantía" },
  },
];

export const brands = ["Nissan", "Chevrolet", "Cadillac", "Infiniti", "Suzuki", "Yamaha"];

export const locations = [
  {
    id: "l1",
    name: { en: "Downtown Flagship", es: "Sucursal Central" },
    address: "Av. John F. Kennedy 254, Santo Domingo",
    hours: { en: "Mon–Fri 8:00–19:00 · Sat 9:00–15:00", es: "Lun–Vie 8:00–19:00 · Sáb 9:00–15:00" },
    services: { en: "Showroom · Service · Parts", es: "Showroom · Servicio · Repuestos" },
  },
  {
    id: "l2",
    name: { en: "North Service Center", es: "Centro de Servicio Norte" },
    address: "Av. 27 de Febrero 1102, Santiago",
    hours: { en: "Mon–Fri 7:30–18:00 · Sat 8:00–13:00", es: "Lun–Vie 7:30–18:00 · Sáb 8:00–13:00" },
    services: { en: "Service · Bodywork · Paint", es: "Servicio · Chapistería · Pintura" },
  },
  {
    id: "l3",
    name: { en: "East Commercial Hub", es: "Centro Comercial Este" },
    address: "Autopista Las Américas Km 12, Santo Domingo Este",
    hours: { en: "Mon–Fri 8:00–18:00", es: "Lun–Vie 8:00–18:00" },
    services: { en: "Fleet · Commercial · Rapid Service", es: "Flotas · Comercial · Servicio Rápido" },
  },
];
