import axios from "axios";

/**
 * Temporary Dev Helper:
 * Bypasses client review, creates the Orchestrator pipeline job directly,
 * and immediately triggers Agent 2 (HLD) generation.
 *
 * Can be safely deleted when dev testing is completed.
 */
export async function devForceStartHLD(meetingId, projectName = "SDLC Project") {
  const ORCHESTRATOR = import.meta.env.VITE_ORCHESTRATOR_URL || "http://127.0.0.1:8000";

  if (!meetingId) {
    throw new Error("No meetingId or projectId provided to devForceStartHLD.");
  }

  // 1. Fetch extracted requirements (instant)
  let reqData = {};
  try {
    const reqRes = await axios.get(`/requirements/${meetingId}`);
    reqData = reqRes.data?.requirements || reqRes.data?.final_requirements || {};
  } catch (err) {
    console.warn("Could not fetch requirements via /requirements, checking fallback:", err);
  }

  let functional_requirements =
    reqData.functional ||
    reqData.functional_requirements ||
    reqData.specified_requirements?.functional ||
    [];

  let non_functional_requirements =
    reqData.non_functional ||
    reqData.non_functional_requirements ||
    reqData.specified_requirements?.non_functional ||
    [];

  // 2. Create job on Orchestrator
  const jobPayload = {
    project_name: projectName || "SDLC Project",
    meeting_id: meetingId,
    functional_requirements,
    non_functional_requirements,
  };

  console.log("[DevBypass] Creating job with payload:", jobPayload);
  const jobRes = await axios.post(`${ORCHESTRATOR}/jobs`, jobPayload);
  const jobId = jobRes.data?.job_id;

  if (!jobId) {
    throw new Error("Orchestrator did not return a valid job_id.");
  }

  console.log(`[DevBypass] Job created: ${jobId}. Automatically starting HLD...`);

  // 3. Immediately trigger HLD stage (no pause / no manual confirmation needed)
  try {
    await axios.post(`${ORCHESTRATOR}/jobs/${jobId}/start-hld`);
    console.log("[DevBypass] HLD stage triggered successfully!");
  } catch (hldErr) {
    console.warn("[DevBypass] Notice on start-hld:", hldErr);
  }

  return jobId;
}
