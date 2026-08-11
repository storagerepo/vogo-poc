import { Destinations } from "@/components/vogo/destinations";
import { FinalCta, SiteFooter } from "@/components/vogo/final-cta";
import { Hero } from "@/components/vogo/hero";
import { PartnerStrip } from "@/components/vogo/partner-strip";
import { PropertyTypes } from "@/components/vogo/property-types";
import { SiteNav } from "@/components/vogo/site-nav";
import { TravelerDestinations } from "@/components/vogo/traveler-destinations";
import { TrendingProperties } from "@/components/vogo/trending-properties";

export default function App() {
  return (
    <main className="bg-ivory">
      <SiteNav />
      <Hero />
      {/* <PartnerStrip /> */}
      <TrendingProperties />
      <PropertyTypes />
      <Destinations />
      <TravelerDestinations />
      <FinalCta />
      <SiteFooter />
    </main>
  );
}
