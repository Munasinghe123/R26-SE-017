import React, { useState } from 'react'
import axios from 'axios'
import audio from '../Images/audio.png'

function UploadAudio() {
    const [file, setFile] = useState(null)
    const [loading, setLoading] = useState(false)
    const [reviewLink, setReviewLink] = useState("")

    const handleUpload = async () => {
        if (!file) return;

        setLoading(true)

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await axios.post("http://127.0.0.1:8000/extract-requirements", formData, {
                headers: {
                    "Content-Type": "multipart/form-data"
                }
            });

            const data = res.data;

            const link = `${window.location.origin}/requirements-review/${data.meeting_id}`

            setReviewLink(link)
        } catch (err) {
            console.error(err);
        }

        setLoading(false)
    };

    return (
        <div className='relative h-screen w-full '>

            <div className='relative min-h-full w-full grid lg:grid-cols-2 grid-cols-1 xl:px-30 pb-5 pt-20'>
                <div className='flex items-start justify-center w-full h-full flex-col space-y-10'>
                    <h1 className='text-white text-6xl uppercase font-bold'
                        style={{ fontFamily: 'Orbitron, sans-serif' }}>Turn <span className='text-cyan-300'>Audio</span>  And <span className='text-cyan-300'>Documents</span> into intelligent <span className='text-cyan-300'> results</span>
                    </h1>
                    <div className='w-full max-w-md bg-gray-800/60 backdrop-blur-md border border-cyan-900 rounded-2xl p-8 shadow-xl'>

                        <label className='flex flex-col items-center justify-center w-full h-40 border-2 border-dashed border-gray-600 rounded-xl cursor-pointer hover:border-cyan-700 transition'>
                            <input
                                type="file"
                                className='hidden'
                                onChange={(e) => setFile(e.target.files[0])}
                            />

                            <p className='text-gray-400'>
                                {file ? file.name : "Click or drag audio file here"}
                            </p>
                        </label>

                        <button
                            onClick={handleUpload}
                            disabled={!file || loading}
                            className={`w-full mt-6 py-3 rounded-xl font-medium transition
                        ${!file || loading
                                    ? "bg-gray-600 text-white cursor-not-allowed"
                                    : "bg-cyan-700 hover:bg-cyan-800 text-white shadow-lg"
                                }`}
                        >
                            {loading ? "Processing..." : "Upload & Process"}
                        </button>

                        {reviewLink && (
                            <div className="mt-6 text-white">
                                <p className="mb-2">Requirements extracted!</p>

                                <p className="text-sm text-gray-400 mb-2">
                                    Share this link with client:
                                </p>

                                <div className="flex items-center gap-2">
                                    <input
                                        type="text"
                                        value={reviewLink}
                                        readOnly
                                        className="w-full px-3 py-2 rounded bg-gray-900 text-sm border border-gray-700"
                                    />

                                    <button
                                        onClick={() => navigator.clipboard.writeText(reviewLink)}
                                        className="px-4 py-2 bg-cyan-700 hover:bg-cyan-800 rounded"
                                    >
                                        Copy
                                    </button>
                                </div>
                            </div>
                        )}

                    </div>
                </div>

                <div className='overflow-hidden h-[85%] opacity-90 absolute bottom-0 right-20'>
                    <img
                        src={audio}
                        className='w-full h-full object-contain'
                    />
                </div>
            </div>
        </div>
    )
}

export default UploadAudio