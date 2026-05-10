import React from 'react'
import bro1 from '../Images/bro1.jpg';
import bro2 from '../Images/bro2.jpg';
import sis3 from '../Images/sis3.jpg';

import roboImage from '../Images/hero.png'


import { useNavigate } from 'react-router-dom';

function LandingPage() {

    const navigate = useNavigate()

    return (
        <div className='hero relative h-screen w-full grid grid-cols-2 bg-transparent z-0  xl:pl-30'>

            <div className='relative h-full flex items-start justify-center flex-col '>
                <div className='space-y-8 -mt-11'>
                    <h1 className='text-white text-7xl uppercase font-bold'
                        style={{ fontFamily: 'Orbitron, sans-serif' }}>From <span className='text-cyan-300'>Requirements</span>  to <span className='text-cyan-300'>Design </span>
                    </h1>
                    <p className='text-white/80 max-w-md text-base leading-relaxed'>
                        Turn raw requirements into structured SRS, LLD, HLD and wireframes ready to build, easy to understand, and delivered in seconds.
                    </p>

                    <div className='flex space-x-10'>
                        <button
                            onClick={() => navigate('/upload-audio')}
                            className="btn  px-6 py-3 text-sm uppercase tracking-wider font-medium">
                            Start Designing
                        </button>

                        <div className='flex items-center space-x-3'>
                            <button className="play-btn">
                                <svg viewBox="0 0 448 512" width="16">
                                    <path
                                        d="M424.4 214.7L72.4 6.6C43.8-10.3 0 6.1 0 47.9V464c0 37.5 40.7 60.1 72.4 41.3l352-208c31.4-18.5 31.5-64.1 0-82.6z"
                                        fill="currentColor"
                                    />
                                </svg>
                            </button>
                            <span className='text-white/80'> Watch Demo</span>
                        </div>
                    </div>
                </div>
                <div className="absolute bottom-16 flex items-center gap-10   text-white/70">

                    <div className="flex -space-x-3">
                        <img src={bro1} className="w-8 h-8 rounded-full border border-black" />
                        <img src={sis3} className="w-8 h-8 rounded-full border border-black" />
                        <img src={bro2} className="w-8 h-8 rounded-full border border-black" />
                    </div>

                    <p className="text-sm">
                        Trusted by <span className="text-white font-medium">100+ users</span>
                    </p>

                </div>

            </div>

            <div className='overflow-hidden h-[90%] absolute bottom-0 right-30'>
                <img
                    src={roboImage}
                    className='w-full h-full object-contain'
                />
            </div>

            {/* <div className='relative w-full flex items-center justify-center h-full'>
                <HeroCanvas />
            </div> */}
        </div>
    )
}

export default LandingPage
