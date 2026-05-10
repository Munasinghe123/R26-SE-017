import React, { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import roboarm from '../Images/WhyUs/roboarm.png'
import arm from '../Images/WhyUs/arm.png'
import why from '../Images/WhyUs/why.png'

gsap.registerPlugin(ScrollTrigger)

function WhyUs({ className }) {
  const sectionRef = useRef(null)
  const roboRef = useRef(null)
  const armRef = useRef(null)
  const whyRef = useRef(null)
  const titleRef = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 80%',
          toggleActions: 'play reverse play reverse',
        },
      })

      // Title fades down
      tl.fromTo(
        titleRef.current,
        { opacity: 0, y: 60 },
        { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out' }
      )

      // Robo arm slides in from left
      tl.fromTo(
        roboRef.current,
        { x: '-100%', opacity: 0 },
        { x: '0%', opacity: 1, duration: 2, ease: 'power3.out' },
        '-=0.4'
      )

      // Human arm slides in from right
      tl.fromTo(
        armRef.current,
        { x: '100%', opacity: 0 },
        { x: '0%', opacity: 1, duration: 2, ease: 'power3.out' },
        '<' // same time as robo arm
      )

      // Center image emerges from middle (scale + fade)
    //   tl.fromTo(
    //     whyRef.current,
    //     { opacity: 0, scale: 0.6, y: 40 },
    //     { opacity: 0.8, scale: 1, y: 0, duration: 2, ease: 'back.out(1.4)' },
    //     '<'
    //   )
     }, sectionRef)

    return () => ctx.revert()
  }, [])

  return (
    <div
      ref={sectionRef}
      className={`scroll-section relative z-10 h-screen bg-black w-full overflow-hidden ${className || ''}`}
    >
      <div className='flex items-center justify-center w-full'>
        <h1
          ref={titleRef}
          className='text-white text-7xl uppercase font-bold w-full text-center pt-10 max-w-3xl'
          style={{ fontFamily: 'Orbitron, sans-serif' }}
        >
          Let Our <span className='text-cyan-300'>Agents</span> Do{' '}
          <span className='text-cyan-300'>Your Work</span>
        </h1>
      </div>

      <div className='flex items-center justify-center w-full h-full'>

        <img
          ref={roboRef}
          src={roboarm}
          className='absolute z-0 left-0 -bottom-20 h-full object-cover'
        />

        <img
          ref={whyRef}
          src={why}
          className='absolute z-0 bottom-16 left-1/2 -translate-x-1/2 h-96 object-contain opacity-80'
        />

        <img
          ref={armRef}
          src={arm}
          className='absolute z-0 right-0 -bottom-20 h-full object-cover'
        />
      </div>
    </div>
  )
}

export default WhyUs