import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { I18nProvider } from "./lib/i18n";
import { TestDriveProvider } from "./components/site/TestDriveContext";
import { TestDriveModal } from "./components/site/TestDriveModal";
import { Header } from "./components/site/Header";
import { Hero } from "./components/site/Hero";
import { Brands } from "./components/site/Brands";
import { VehiclesSection } from "./components/site/VehiclesSection";
import { Featured } from "./components/site/Featured";
import { Services } from "./components/site/Services";
import { Financing } from "./components/site/Financing";
import { UsedVehicles } from "./components/site/UsedVehicles";
import { About } from "./components/site/About";
import { Locations } from "./components/site/Locations";
import { FinalCTA } from "./components/site/FinalCTA";
import { Footer } from "./components/site/Footer";
import "./styles.css";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <I18nProvider>
        <TestDriveProvider>
          <Header />
          <main>
            <Hero />
            <Brands />
            <VehiclesSection />
            <Featured />
            <Services />
            <Financing />
            <UsedVehicles />
            <About />
            <Locations />
            <FinalCTA />
          </main>
          <Footer />
          <TestDriveModal />
        </TestDriveProvider>
      </I18nProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
