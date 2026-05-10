import React from 'react'
import { Link } from 'react-router-dom'

function SignIn() {
    return (
        <div className='relative flex items-center justify-center h-screen w-full'>
            <Link to='/requirments-review'>
                <button className='bg-red-700 cursor-pointer'>review</button>
            </Link>

        </div>
    )
}

export default SignIn
