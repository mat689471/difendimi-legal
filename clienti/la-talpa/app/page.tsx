import Navbar from "@/components/navbar";
import Hero from "@/components/hero";
import ServicesBento from "@/components/services-bento";
import BeforeAfter from "@/components/before-after";
import ReviewsMarquee from "@/components/reviews-marquee";
import QuoteWizard from "@/components/quote-wizard";
import SiteFooter from "@/components/site-footer";
import FloatingContact from "@/components/floating-contact";

export default function Page() {
  return (
    <>
      <Navbar />
      <main id="contenuto">
        <Hero />
        <ServicesBento />
        <BeforeAfter />
        <ReviewsMarquee />
        <QuoteWizard />
      </main>
      <SiteFooter />
      <FloatingContact />
    </>
  );
}
