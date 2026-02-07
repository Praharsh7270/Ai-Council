"use client"

import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"

export function CTASection() {
  return (
    <section className="py-20 sm:py-32">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl rounded-2xl bg-gradient-to-r from-primary/10 via-primary/5 to-primary/10 p-8 text-center sm:p-12 lg:p-16">
          <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            Ready to Experience Smarter AI?
          </h2>
          <p className="mx-auto mb-8 max-w-2xl text-lg text-muted-foreground">
            Join thousands of users leveraging multi-agent orchestration for better results at lower costs.
            Start with our free demo or create an account today.
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button size="lg" className="w-full sm:w-auto">
              Get Started Free
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button size="lg" variant="outline" className="w-full sm:w-auto">
              View Documentation
            </Button>
          </div>
          <p className="mt-6 text-sm text-muted-foreground">
            No credit card required • 3 free demo queries • Full access to orchestration visualization
          </p>
        </div>
      </div>
    </section>
  )
}
