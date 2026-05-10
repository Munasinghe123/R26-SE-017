import React from 'react'
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useRef } from 'react';
import { useMemo } from 'react';

import requirements from '../Images/OurAgents/reqs.png'
import highlevel from '../Images/OurAgents/highlevel.png'
import lowlevel from '../Images/OurAgents/lowlevel.png'
import ui from '../Images/OurAgents/ui.png'

gsap.registerPlugin(ScrollTrigger);

function OurAgents({ className }) {

  const wrapRef = useRef(null);
  const listRef = useRef(null);
  const trackRef = useRef(null);


  useGSAP(() => {
    const ctx = gsap.context(() => {

      gsap.set(trackRef.current, { scaleY: 0, transformOrigin: "top" });

      ScrollTrigger.create({
        trigger: listRef.current,
        start: "top 75%",
        end: "bottom 25%",
        scrub: true,
        invalidateOnRefresh: true,
        onUpdate: (self) => {
          gsap.to(trackRef.current, { scaleY: self.progress, ease: "none" });
          wrapRef.current?.style?.setProperty(
            "--about-progress",
            `${Math.round(self.progress * 100)}%`
          );
        },
      });


      gsap.utils.toArray(".tl-item").forEach((el) => {
        const fromX = el.classList.contains("tl-left") ? -40 : 40;
        gsap.from(el, {
          x: fromX,
          opacity: 0,
          duration: 0.6,
          ease: "power2.out",
          scrollTrigger: {
            trigger: el,
            start: "top 85%",
            toggleActions: "play none none reverse",
          },
        });
      });
    }, wrapRef);

    return () => ctx.revert();
  }, []);

  const items = useMemo(
    () => [
      {
        key: "requirments",
        offset: null,
        node: (
          <div
            className="
              relative w-full max-w-sm mx-auto
              p-6 rounded-[32px]
              flex flex-col items-center gap-5

              bg-white/[0.06]
              backdrop-blur-2xl

              border border-cyan-400/20
              shadow-[0_0_30px_rgba(34,211,238,0.12)]

              overflow-hidden
            "
          >
            {/* glow layer */}
            <div className="
                  absolute inset-0
                  bg-gradient-to-br
                  from-cyan-400/10
                  via-transparent
                  to-blue-500/10
                  pointer-events-none
                " />

            <img
              src={requirements}
              className="
                relative z-10
                w-40 h-40
                rounded-full
                object-cover

                border border-cyan-300/30
                shadow-[0_0_25px_rgba(34,211,238,0.25)]
              "
            />

            <div className="relative z-10 text-center space-y-3">
              <h1 className="
                font-['Orbitron']
                text-2xl font-bold
                tracking-[0.15em]
                text-white
              ">
                Requirements Intelligence
              </h1>

              <p className="text-cyan-100/75 leading-relaxed">
                Transforms raw conversations into
                <br />
                structured requirements
              </p>
            </div>
          </div>
        ),
      },
      {
        key: "highlevel",
        offset: null,
        node: (
          <div
            className="
              relative w-full max-w-sm mx-auto
              p-6 rounded-[32px]

              flex flex-col items-center text-center gap-5

              bg-white/[0.06]
              backdrop-blur-2xl

              border border-cyan-400/20
              shadow-[0_0_30px_rgba(34,211,238,0.12)]

              overflow-hidden
            "
          >
            {/* holographic glow */}
            <div
              className="
                absolute inset-0
                bg-gradient-to-br
                from-cyan-400/10
                via-transparent
                to-blue-500/10
                pointer-events-none
              "
            />


            <img
              src={highlevel}
              className="
                  relative z-10
                  w-40 h-40
                  rounded-full
                  object-cover

                  border border-cyan-300/30
                  shadow-[0_0_25px_rgba(34,211,238,0.25)]
                "
            />

            <div className="relative z-10 space-y-3">
              <h1
                className="
        font-['Orbitron']
        text-2xl font-bold
        uppercase tracking-[0.15em]
        text-white
      "
              >
                High-Level Design
              </h1>

              <p className="text-cyan-100/75 leading-relaxed">
                Generates robust high-level architecture
                <br />
                and system design diagrams
              </p>
            </div>
          </div>
        ),
      }
      ,
      {
        key: "lowlevel",
        offset: "sm",
        node: (
          <div
            className="
              relative w-full max-w-sm mx-auto
              p-6 rounded-[32px]

              flex flex-col items-center text-center gap-5

              bg-white/[0.06]
              backdrop-blur-2xl

              border border-cyan-400/20
              shadow-[0_0_30px_rgba(34,211,238,0.12)]

              overflow-hidden
            "
          >
            {/* holographic glow */}
            <div
              className="
                absolute inset-0
                bg-gradient-to-br
                from-cyan-400/10
                via-transparent
                to-indigo-500/10
                pointer-events-none
              "
            />

            <img
              src={lowlevel}
              className="
                relative z-10
                w-40 h-40
                rounded-full
                object-cover

                border border-cyan-300/30
                shadow-[0_0_25px_rgba(34,211,238,0.25)]
              "
            />

            <div className="relative z-10 space-y-3">
              <h1
                className="
                  font-['Orbitron']
                  text-2xl font-bold
                  uppercase tracking-[0.15em]
                  text-white
                "
              >
                Low-Level Design
              </h1>

              <p className="text-cyan-100/75 leading-relaxed">
                Produces detailed component-level designs
                <br />
                and technical diagrams
              </p>
            </div>
          </div>
        ),
      },
      {
        key: "ui",
        offset: null,
        node: (
          <div
            className="
              relative w-full max-w-sm mx-auto
              p-6 rounded-[32px]

              flex flex-col items-center text-center gap-5

              bg-white/[0.06]
              backdrop-blur-2xl

              border border-cyan-400/20
              shadow-[0_0_20px_rgba(34,211,238,0.10)]

              overflow-hidden
            "
          >
            {/* holographic glow */}
            <div
              className="
                absolute inset-0
                bg-gradient-to-br
                from-cyan-400/10
                via-transparent
                to-violet-500/10
                pointer-events-none
              "
            />

            <img
              src={ui}
              className="
              relative z-10
              w-40 h-40
              rounded-full
              object-cover

              border border-cyan-300/30
              shadow-[0_0_25px_rgba(34,211,238,0.20)]
            "
            />

            <div className="relative z-10 space-y-3">
              <h1
                className="
                  font-['Orbitron']
                  text-2xl font-bold
                  uppercase tracking-[0.15em]
                  text-white
                "
              >
                UI/UX & Usability
              </h1>

              <p className="text-cyan-100/75 leading-relaxed">
                Creates intuitive wireframes and
                <br />
                user-centered interface designs
              </p>
            </div>
          </div>
        ),
      },
    ],
    []
  );


  return (
    <div className='relative scroll-section rounded-t-4xl  z-10 bg-[radial-gradient(ellipse_at_top,rgba(34,211,238,0.08)_0%,transparent_55%),linear-gradient(to_bottom,#102235_0%,#0b1726_22%,#050c15_55%,#000000_100%)] min-h-screen w-full'>

      <h1 className='text-white text-7xl uppercase font-bold w-full text-center pt-10'
        style={{ fontFamily: 'Orbitron, sans-serif' }}>Our <span className='text-cyan-300'>Agents</span>
      </h1>

      <section id="about" className="relative  px-5">
        <div className="container mx-auto w-full pt-6 pb-24">

          <div ref={wrapRef} className="relative md:mt-20 mt-10">
            <div className="hidden md:block pointer-events-none absolute left-1/2 -top-10 -bottom-10 -translate-x-1/2">
              <div className="absolute top-0 bottom-0 w-[4px] bg-white/10 rounded-full overflow-hidden">
                <div
                  ref={trackRef}
                  className="w-full h-full origin-top scale-y-0 bg-cyan-500"
                />
              </div>
            </div>


            {/* stack of rows */}
            <div ref={listRef} className="space-y-0 md:space-y-0 ">
              {items.map((item, i) => {
                const left = i % 2 === 0;
                const rowOffset =
                  item.offset === "lg" ? "md:pt-8" : item.offset === "sm" ? "md:pt-6" : "";

                return (
                  <div
                    key={item.key}
                    className={`grid md:grid-cols-[1fr_auto_1fr] grid-cols-1 md:gap-x-4  ${rowOffset} ${i !== 0 ? "-mt-16" : ""}`}
                  >
                    <div
                      className={`tl-item max-w-[40rem]  w-full ${left
                        ? "tl-left md:col-start-1 md:justify-self-end md:mr-2"
                        : "tl-right md:col-start-3 md:justify-self-start md:ml-2"
                        }`}
                    >
                      {item.node}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>


    </div>
  )
}

export default OurAgents
