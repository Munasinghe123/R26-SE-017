import React from 'react'
import LandingPage from './LandingPage'
import WhyUs from './WhyUs'
import OurAgents from './OurAgents'
// import Pricing from './Pricing'
import Footer from '../components/Footer'

function Home() {
  return (
    <div>
      <LandingPage />
      <OurAgents className="scroll-section" />
      <WhyUs className="scroll-section" />
      {/* <Pricing className="scroll-section" /> */}
      {/* <Footer/> */}
    </div>
  );
}

export default Home