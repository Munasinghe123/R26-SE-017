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
import ProjectDashboard from "./Pages/Protected/Dashboard/Project-Dashboard";
import UserDashboard from "./Pages/Protected/Dashboard/User-Dashboard";
import CreateProject from "./Pages/Protected/Create-Project";
import ClientDashboard from "./Pages/Client/ClientDashboard";
import ClientRequirementReview from "./Pages/Client/ClientRequirementReview";
import Footer from "./components/Footer";

// ── New Pipeline Pages ─────────────────────────────────────────────────────
import PipelineDashboard  from "./Pages/Protected/Pipeline/PipelineDashboard";
import ArchitectureReview from "./Pages/Protected/Pipeline/ArchitectureReview";
import LLDReview          from "./Pages/Protected/Pipeline/LLDReview";
import UIReview           from "./Pages/Protected/Pipeline/UIReview";
import DesignArtifacts    from "./Pages/Protected/Pipeline/DesignArtifacts";
import SRSDownload        from "./Pages/Protected/Pipeline/SRSDownload";

function AppLayout() {
  const location = useLocation();

  // Pages where we suppress the shared shell (Header / StarBackground / Footer)
  const isMeetingUI      = location.pathname === "/test-meeting";
  const isUserDashboard  = location.pathname === "/user-dashboard";
  const isCreateProject  = location.pathname === "/create-project";

  // Pipeline pages get the StarBackground but no Footer (they're full-screen experiences)
  const isPipelinePage   = location.pathname.startsWith("/pipeline/");

  return (
    <>
      {!isMeetingUI && <StarBackground />}
      {!isMeetingUI && <Header />}

      <Routes>
        {/* ── Public ────────────────────────────────────────────────── */}
        <Route path="/"             element={<Home />} />
        <Route path="/upload-audio" element={<UploadAudio />} />
        <Route path="/get-started"  element={<GetStarted />} />
        <Route path="/select-mode"  element={<SelectMode />} />
        <Route path="/test-meeting" element={<TestMeeting />} />

        {/* ── Protected — Dashboard ─────────────────────────────────── */}
        <Route path="/user-dashboard"    element={<UserDashboard />} />
        <Route path="/project-dashboard" element={<ProjectDashboard />} />
        <Route path="/client-dashboard"  element={<ClientDashboard />} />
        <Route path="/create-project"    element={<CreateProject />} />

        {/* ── Client Requirements Portal & Review Routes ───────────── */}
        <Route
          path="/client/requirements/:meetingId"
          element={<ClientRequirementReview />}
        />
        <Route
          path="/client/requirements"
          element={<ClientRequirementReview />}
        />
        <Route
          path="/client-review/:meetingId"
          element={<ClientRequirementReview />}
        />

        {/* ── Protected — Requirements Review (Agent 1 output) ─────── */}
        <Route
          path="/requirements-review/:meetingId"
          element={<RequirementReview />}
        />
        <Route
          path="/project/:projectId/upload"
          element={<UploadAudio />}
        />
        <Route
          path="/project/:projectId/requirements-review/:meetingId"
          element={<RequirementReview />}
        />
        <Route
          path="/project/:projectId/pipeline/:jobId"
          element={<PipelineDashboard />}
        />


        {/* ── Protected — Full Pipeline Flow ────────────────────────── */}
        {/* 1. Real-time pipeline tracker (SSE) */}
        <Route
          path="/pipeline/:jobId"
          element={<PipelineDashboard />}
        />
        {/* 2. HLD quality review + accept/reject */}
        <Route
          path="/pipeline/:jobId/architecture"
          element={<ArchitectureReview />}
        />
        {/* 2b. LLD detailed review & 3-model expert analysis */}
        <Route
          path="/pipeline/:jobId/lld"
          element={<LLDReview />}
        />
        {/* 2c. UI/UX Usability Suite & interactive prototype sandbox */}
        <Route
          path="/pipeline/:jobId/ui"
          element={<UIReview />}
        />
        {/* 3. Tabbed design artifacts viewer */}
        <Route
          path="/pipeline/:jobId/artifacts"
          element={<DesignArtifacts />}
        />
        {/* 4. SRS document summary + download */}
        <Route
          path="/pipeline/:jobId/srs"
          element={<SRSDownload />}
        />
      </Routes>

      {/* Footer: hide on meeting, dashboard, create-project, and pipeline pages */}
      {!isMeetingUI && !isUserDashboard && !isCreateProject && !isPipelinePage && (
        <Footer />
      )}
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
