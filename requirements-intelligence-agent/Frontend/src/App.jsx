import React from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";

import Home from "./Pages/Home";
import Header from "./components/Header";
import StarBackground from "./components/StartBackGround";
import GetStarted from "./Pages/Get-Started";
import TestMeeting from "./Pages/Test-Meeting";
import Footer from "./components/Footer";
import ProjectDashboard from "./Pages/Protected/Dashboard/Project-Dashboard";
// import ProtectedRoute from "./components/ProtectedRoute";
import ClientRequirementsReview from "./Pages/client/ClientRequirementsReview";

function AppLayout() {
  const location = useLocation();

  const isMeetingUI = location.pathname === "/test-meeting";
  const userDashboardUI = location.pathname === "/welcome";
  const createProjectUI = location.pathname === "/create-project";
  const projectDashboard = location.pathname.startsWith("/project-dashboard");

  return (
    <>
      {!isMeetingUI && !projectDashboard && <StarBackground />}
      {!isMeetingUI && !projectDashboard && <Header />}

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/get-started" element={<GetStarted />} />
        <Route path="/test-meeting" element={<TestMeeting />} />

        {/* must be protected routes */}

        <Route path="/project-dashboard" element={<ProjectDashboard />} />
        <Route
          path="/project-dashboard/:projectId"
          element={<ProjectDashboard />}
        />
       

        <Route
          path="/client/review/:threadId"
          element={<ClientRequirementsReview />}
        />
      </Routes>

      {!isMeetingUI &&
        !userDashboardUI &&
        !createProjectUI &&
        !projectDashboard && <Footer />}
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
