"""
ProjectDashboard.jsx — shows user's projects and their pipeline status.
Matches the Requirement Agent design system exactly.
"""
import React, { useEffect, useState } from "react"

const AGENT1 = import.meta?.env?.VITE_AGENT1_URL ?? ""
const ORCH   = import.meta?.env?.VITE_ORCHESTRATOR_URL ?? ""
