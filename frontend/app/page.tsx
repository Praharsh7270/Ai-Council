import { Navigation } from "@/components/landing/navigation"
import { HeroSection } from "@/components/landing/hero-section"
import { FeaturesSection } from "@/components/landing/features-section"
import { HowItWorksSection } from "@/components/landing/how-it-works-section"
import { OrchestrationVisualization } from "@/components/landing/orchestration-visualization"
import { DemoQueryInterface } from "@/components/landing/demo-query-interface"
import { CTASection } from "@/components/landing/cta-section"
import { Footer } from "@/components/landing/footer"

export default function Home() {
  return (
    <>
      <Navigation />
      <main className="min-h-screen">
        <HeroSection />
        <div id="features">
          <FeaturesSection />
        </div>
        <div id="how-it-works">
          <HowItWorksSection />
        </div>
        <OrchestrationVisualization />
        <div id="demo">
          <DemoQueryInterface />
        </div>
        <div id="pricing">
          <CTASection />
        </div>
      </main>
      <Footer />
    </>
  )
}

