import { HeroSection } from "../components/HeroSection";
import { HandbookSection } from "../components/HandbookSection";
import { GlossarySection } from "../components/GlossarySection";

export function Home() {
  return (
    <>
      <HeroSection />
      <HandbookSection />
      <GlossarySection />
    </>
  );
}