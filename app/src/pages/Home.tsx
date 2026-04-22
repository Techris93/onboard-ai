import { Suspense, lazy } from "react";
import Navigation from "../components/Navigation";
import AgentSystemSection from "../sections/AgentSystemSection";
import CapabilitiesSection from "../sections/CapabilitiesSection";
import CatalogSection from "../sections/CatalogSection";
import Footer from "../sections/Footer";
import HeroSection from "../sections/HeroSection";
import IntegrationSection from "../sections/IntegrationSection";
import OnboardingSection from "../sections/OnboardingSection";
import PilotSection from "../sections/PilotSection";
import PlatformSection from "../sections/PlatformSection";
import ProcessSection from "../sections/ProcessSection";
import ScoreSection from "../sections/ScoreSection";
import UseCasesSection from "../sections/UseCasesSection";

const OceanCanvas = lazy(() => import("../components/ocean/OceanCanvas"));

export default function Home() {
  return (
    <>
      <Suspense fallback={null}>
        <OceanCanvas />
      </Suspense>
      <Navigation />
      <div className="page-shell">
        <HeroSection />
        <OnboardingSection />
        <CatalogSection />
        <CapabilitiesSection />
        <ProcessSection />
        <PlatformSection />
        <IntegrationSection />
        <AgentSystemSection />
        <UseCasesSection />
        <ScoreSection />
        <PilotSection />
        <Footer />
      </div>
    </>
  );
}
