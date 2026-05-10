import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import axios from "axios"

export default function RequirementReview() {
    const { meetingId } = useParams()
    const [requirements, setRequirements] = useState(null)
    const [feedback, setFeedback] = useState("")
    const [loading, setLoading] = useState(false)
    const [feedBackModal, setFeedBackModal] = useState(false)


    const fetchRequirements = async () => {
        try {
            console.log("use effect fired")
            const res = await axios.get(`http://127.0.0.1:8000/requirements/${meetingId}`)
            setRequirements(res.data.requirements)
            console.log("returned reqs", res.data.requirements)
        } catch (err) {
            console.error(err)
            setRequirements({ functional: [], non_functional: [] })
        }
    }

    useEffect(() => {

        if (meetingId) {
            fetchRequirements()
        }
    }, [meetingId])

    if (!requirements) return <div>Loading...</div>

    const handleRefine = async () => {
        if (!feedback.trim()) return

        setLoading(true)

        try {
            const res = await axios.post("http://127.0.0.1:8000/refine-reqs", {

                feedback: feedback,
                requirements: requirements,
                meetingId: meetingId
            })

            console.log("refined reqs", res.data.requirements)
            await fetchRequirements()

            setFeedback("")
        } catch (err) {
            console.error(err)
        }

        setLoading(false)
    }

    const handleApprove = async () => {

        try {
            setLoading(true)

            const res = await axios.post(
                "http://127.0.0.1:8000/approve-reqs",
                {
                    meeting_id: meetingId
                }
            )
          
            alert("Requirments approved successfully!")

        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    return (
        <>
            <div className="min-h-screen w-full pt-28 pb-10">

                <div className="flex h-full w-full  justify-center">
                    <div className="relative w-full max-w-4xl mx-auto p-8 rounded-3xl 
                            bg-[#0f172a] border border-white/10 shadow-2xl 
                            backdrop-blur-xl text-white space-y-8 overflow-hidden">


                        <div className="relative z-10">
                            <h2 className="text-2xl font-bold mb-5 text-cyan-300 tracking-wide">
                                Functional Requirements
                            </h2>

                            {requirements.functional?.length === 0 ? (
                                <p className="text-gray-400 italic">
                                    No functional requirements
                                </p>
                            ) : (
                                <div className="space-y-3">
                                    {requirements.functional?.map((r, index) => (
                                        <div
                                            key={r.id}
                                            className="p-4 rounded-2xl 
                        bg-white/5 border border-white/10
                        hover:border-cyan-400/40
                        hover:bg-cyan-400/5
                        transition-all duration-300"
                                        >
                                            <p className="text-gray-200 leading-relaxed">
                                                <span className="text-cyan-300 font-semibold mr-2">
                                                    {index + 1}.
                                                </span>
                                                {r.description}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>


                        {/* <div className="relative z-10">
                            <h2 className="text-2xl font-bold mb-5 text-purple-300 tracking-wide">
                                Non-Functional Requirements
                            </h2>

                            {requirements.non_functional?.length === 0 ? (
                                <p className="text-gray-400 italic">
                                    No non-functional requirements
                                </p>
                            ) : (
                                <div className="space-y-3">
                                    {requirements.non_functional?.map((r, index) => (
                                        <div
                                            key={r.id}
                                            className="p-4 rounded-2xl 
                        bg-white/5 border border-white/10
                        hover:border-purple-400/40
                        hover:bg-purple-400/5
                        transition-all duration-300"
                                        >
                                            <p className="text-gray-200 leading-relaxed">
                                                <span className="text-purple-300 font-semibold mr-2">
                                                    {index + 1}.
                                                </span>
                                                {r.description}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div> */}


                        <div className="relative z-10 flex justify-end gap-4 pt-4">
                            <button
                                className=" px-5 py-2 
                                text-sm font-medium uppercase tracking-[2px]
                                bg-cyan-200 text-black
                                border border-cyan-200
                                rounded-full
                                backdrop-blur-md
                                overflow-hidden
                                transition-all duration-300
                                hover:border-cyan-400/60
                                hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]"

                                onClick={(e) => setFeedBackModal(true)}
                            >
                                Reject
                            </button>

                            <button
                                className=" px-5 py-2 
                            text-sm font-medium uppercase tracking-[2px]
                            text-white
                            border border-cyan-200
                            rounded-full
                            bg-white/5 backdrop-blur-md
                            overflow-hidden
                            transition-all duration-300
                            hover:border-cyan-400/60
                            hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]"

                                onClick={handleApprove}
                            >
                                Approve
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {
                feedBackModal && (
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-md 
        flex items-center justify-center z-50 px-4">

                        {/* Modal */}
                        <div
                            className="relative w-full max-w-2xl 
                bg-[#0f172a] border border-white/10
                rounded-3xl shadow-2xl overflow-hidden"
                        >

                            {/* Glow Effects */}
                            <div className="absolute top-0 left-0 w-72 h-72 bg-cyan-500/10 blur-3xl rounded-full" />
                            <div className="absolute bottom-0 right-0 w-72 h-72 bg-purple-500/10 blur-3xl rounded-full" />

                            {/* Header */}
                            <div className="relative z-10 p-8 border-b border-white/10">
                                <h2 className="text-3xl font-bold text-white">
                                    Requirement Refinement
                                </h2>

                                <p className="mt-3 text-gray-400 leading-relaxed">
                                    Provide feedback to refine the generated software requirements.
                                    The system will regenerate the requirement set based on your
                                    suggestions and corrections.
                                </p>
                            </div>


                            <div className="relative z-10 p-8 space-y-5">

                                <div>
                                    <label className="block mb-3 text-sm uppercase tracking-[2px] text-cyan-300 font-medium">
                                        Feedback
                                    </label>

                                    <textarea
                                        value={feedback}
                                        onChange={(e) => setFeedback(e.target.value)}
                                        placeholder="Example: Add user authentication requirements, improve scalability constraints, clarify reporting features..."
                                        className="w-full h-48 p-5 rounded-2xl 
                            bg-white/5 border border-white/10
                            text-white placeholder:text-gray-500
                            outline-none resize-none
                            focus:border-cyan-400/50
                            focus:bg-cyan-400/5
                            transition-all duration-300"
                                    />
                                </div>

                                {/* Info Box */}
                                <div className="p-4 rounded-2xl bg-cyan-500/5 border border-cyan-400/10">
                                    <p className="text-sm text-gray-300 leading-relaxed">
                                        The refinement process uses AI-assisted requirement analysis
                                        to regenerate Functional and Non-Functional Requirements
                                        according to stakeholder feedback.
                                    </p>
                                </div>

                                {/* Buttons */}
                                <div className="flex justify-end gap-4 pt-2">

                                    <button
                                        className=" px-5 py-2 
                            text-sm font-medium uppercase tracking-[2px]
                            text-white
                            border border-red-300
                            rounded-full
                            bg-red/5 backdrop-blur-md
                            overflow-hidden cursor-pointer hover:border-red-300/60
                            transition-all duration-300
                           "
                                        onClick={(e) => setFeedBackModal(false)}
                                    >
                                        Cancel
                                    </button>

                                    <button
                                        className=" px-5 py-2 
                            text-sm font-medium uppercase tracking-[2px]
                            text-white
                            border border-cyan-200
                            rounded-full
                            bg-white/5 backdrop-blur-md
                            overflow-hidden
                            transition-all duration-300
                            hover:border-cyan-400/60 cursor-pointer
                           "
                                        onClick={handleRefine}
                                    >
                                        {loading ? "Refining..." : "Refine Requirements"}
                                    </button>

                                </div>
                            </div>
                        </div>
                    </div>
                )
            }
        </>
    )

}