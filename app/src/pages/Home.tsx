import { Suspense, lazy } from "react";
import Navigation from "../components/Navigation";
import Footer from "../sections/Footer";
import HeroSection from "../sections/HeroSection";
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
        <ProcessSection />
        <PlatformSection />
        <UseCasesSection />
        <ScoreSection />
        <Footer />
      </div>
    </>
  );
}
