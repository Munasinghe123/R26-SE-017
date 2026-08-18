
export default function ProjectDashboard() {

    return(
        <>
            <div className="flex flex-col items-center justify-center h-screen">
                <h1 className="text-4xl font-bold text-white mb-4">Welcome to the Dashboard</h1>
                <p className="text-lg text-gray-300">This is a protected route accessible only to authenticated users.</p>
            </div>
        </>
    )
}