import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./Pages/Home";
import UploadAudio from "./Pages/UploadAudio";
import Header from "./components/Header";
import StarBackground from "./components/StartBackGround";
import RequirementReview from "./Pages/client/RequirementReview";
import GetStarted from "./Pages/Get-Started";
import SelectMode from "./Pages/Select-Mode";
import Footer from "./components/Footer";


function App() {
  return (
    <BrowserRouter>
      <StarBackground />
      <Header />

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/upload-audio" element={<UploadAudio />} />
        <Route path="/get-started" element={<GetStarted />} />
        <Route path="/select-mode" element={<SelectMode />} />

        <Route
          path="/requirements-review/:meetingId"
          element={<RequirementReview />}
        />
      </Routes>

      <Footer />
    </BrowserRouter>
  );
}

export default App;
