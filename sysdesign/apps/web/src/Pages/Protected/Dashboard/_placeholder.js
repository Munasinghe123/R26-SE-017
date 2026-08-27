"""
ProjectDashboard.jsx — shows user's projects and their pipeline status.
Matches the Requirement Agent design system exactly.
"""
import React, { useEffect, useState } from "react"

const AGENT1 = import.meta?.env?.VITE_AGENT1_URL ?? "http://127.0.0.1:8001"
const ORCH   = import.meta?.env?.VITE_ORCHESTRATOR_URL ?? "http://127.0.0.1:8000"
