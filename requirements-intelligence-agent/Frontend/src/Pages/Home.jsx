import React from 'react'
import LandingPage from './LandingPage'
import WhyUs from './WhyUs'
import OurAgents from './OurAgents'
import Pricing from './Pricing'
import Footer from '../components/Footer'
import { useEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

function Home() {

  useEffect(() => {
    const sections = gsap.utils.toArray(".scroll-section");

    // Pin the hero
    const t = ScrollTrigger.create({
      trigger: ".hero",
      start: "top top",
      end: () => `+=${sections.reduce((acc, el) => acc + el.offsetHeight, 0)}`,
      pin: true,
      pinSpacing: false,
    });

    // Fade out the landing page as first scroll-section arrives
    const fadeOut = gsap.to(".hero", {
      opacity: 0,
      ease: "none",
      scrollTrigger: {
        trigger: ".scroll-section",   // first scroll-section entering triggers it
        start: "top 90%",             // start fading when section is near bottom of viewport
        end: "top 30%",               // fully faded by the time it reaches 30%
        scrub: true,                  // ties opacity directly to scroll position
      }
    });

    return () => {
      t.kill();
      fadeOut.kill();
    };
  }, []);

  return (
    <div>
      <LandingPage />                        
      <OurAgents className="scroll-section" />
      <WhyUs className="scroll-section" />
      <Pricing className="scroll-section" />
      <Footer />
    </div>
  );
}

export default Home