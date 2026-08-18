import React from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";

import Home from "./Pages/Home";
import UploadAudio from "./Pages/UploadAudio";
import Header from "./components/Header";
import StarBackground from "./components/StartBackGround";
import RequirementReview from "./Pages/client/RequirementReview";
import GetStarted from "./Pages/Get-Started";
import SelectMode from "./Pages/Select-Mode";
import TestMeeting from "./Pages/Test-Meeting";
import UserDashboard from "./Pages/protected/Dashboard/User-Dashboard";
import Footer from "./components/Footer";
import ProjectDashboard from "./Pages/Protected/Dashboard/Project-Dashboard";
import CreateProject from "./Pages/Protected/Create-Project";
// import ProtectedRoute from "./components/ProtectedRoute";

function AppLayout() {
  const location = useLocation();

  const isMeetingUI = location.pathname === "/test-meeting";
  const userDashboardUI = location.pathname === "/user-dashboard";
  const createProjectUI = location.pathname === "/create-project";

  return (
    <>
      {!isMeetingUI && <StarBackground />}
      {!isMeetingUI && <Header />}

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/upload-audio" element={<UploadAudio />} />
        <Route path="/get-started" element={<GetStarted />} />
        <Route path="/select-mode" element={<SelectMode />} />
        <Route path="/test-meeting" element={<TestMeeting />} />

        {/* must be protected routes */}
        <Route path="/user-dashboard" element={<UserDashboard />} />
        <Route path="/project-dashboard" element={<ProjectDashboard />} />
        <Route path="/create-project" element={<CreateProject />} />
        <Route
          path="/requirements-review/:meetingId"
          element={<RequirementReview />}
        />
      </Routes>

      {!isMeetingUI && !userDashboardUI && !createProjectUI && <Footer />}
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}

export default App;
