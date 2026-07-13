'use client';

import React, { useState } from 'react';

export default function DocumentationTabs() {
  const [activeTab, setActiveTab] = useState('rubric');

  const tabs = [
    { id: 'rubric', label: 'Rubric' },
    { id: 'novelties', label: 'Novelties' },
    { id: 'gaps', label: 'Research Gaps' },
    { id: 'convergence', label: 'Convergence' }
  ];

  return (
    <div className="bg-dark-card rounded-lg shadow-lg overflow-hidden border border-dark-hover">
      {/* Tab Navigation */}
      <div className="flex border-b border-dark-hover">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-4 py-3 font-semibold text-center transition ${
              activeTab === tab.id
                ? 'bg-primary-dark text-dark-bg'
                : 'bg-dark-hover text-text-secondary hover:text-text-primary hover:border-b-2 hover:border-primary'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="p-8 bg-dark-card text-text-primary">
        {/* Rubric Tab */}
        {activeTab === 'rubric' && (
          <div className="space-y-8">
            <div>
              <h2 className="text-2xl font-bold text-primary mb-6">Composite Scoring Formula</h2>
              <div className="bg-gray-900 text-white rounded-lg p-8 space-y-4">
                <div className="flex items-center justify-center space-x-4 text-2xl">
                  <div className="bg-green-900 px-4 py-3 rounded">
                    <div className="text-green-400 font-bold">ISO × 0.30</div>
                    <div className="text-xs text-green-300">Effectiveness · Efficiency · Satisfaction</div>
                  </div>
                  <span className="text-3xl font-bold">+</span>
                  <div className="bg-purple-900 px-4 py-3 rounded">
                    <div className="text-purple-400 font-bold">Nielsen × 0.30</div>
                    <div className="text-xs text-purple-300">10 Interaction heuristics</div>
                  </div>
                  <span className="text-3xl font-bold">+</span>
                  <div className="bg-blue-900 px-4 py-3 rounded">
                    <div className="text-blue-400 font-bold">WCAG × 0.40</div>
                    <div className="text-xs text-blue-300">POUR accessibility principles</div>
                  </div>
                  <span className="text-3xl font-bold">=</span>
                </div>
                <div className="text-center pt-4 border-t border-gray-700">
                  <div className="text-5xl font-bold text-yellow-400">0-100</div>
                  <div className="text-gray-300">Composite Score</div>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-xl font-bold text-primary mb-4">Sub-Metrics by Standard</h3>
              <div className="grid md:grid-cols-3 gap-6">
                {/* ISO 9241-11 */}
                <div className="bg-dark-bg border-2 border-green-700 rounded-lg p-6">
                  <div className="bg-green-900 text-green-300 font-semibold px-3 py-1 rounded-full inline-block mb-4 text-sm">30% weight</div>
                  <h4 className="font-bold text-green-400 mb-4">ISO 9241-11</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-text-secondary">Nav depth</span><span className="font-mono text-text-primary">0–4</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">Label pairing</span><span className="font-mono text-text-primary">0–4</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">Form completion</span><span className="font-mono text-text-primary">0–4</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">Heading hierarchy</span><span className="font-mono text-text-primary">0–4</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">Tab order</span><span className="font-mono text-text-primary">0–4</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">Button clarity</span><span className="font-mono text-text-primary">0–4</span></div>
                  </div>
                  <div className="text-xs text-neutral mt-4">Mean → normalised to 0–100</div>
                </div>

                {/* Nielsen Heuristics */}
                <div className="bg-dark-bg border-2 border-purple-700 rounded-lg p-6">
                  <div className="bg-purple-900 text-purple-300 font-semibold px-3 py-1 rounded-full inline-block mb-4 text-sm">30% weight</div>
                  <h4 className="font-bold text-purple-400 mb-2">Nielsen Heuristics</h4>
                  <p className="text-xs text-text-secondary mb-3">Curated 8-of-10 subset</p>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-text-secondary">H1 System status</span><span className="font-mono text-text-primary">0–4</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">H3 User control</span><span className="font-mono text-text-primary">0–4</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">H4 Consistency</span><span className="font-mono text-text-primary">0–4</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">H5 Error prevention</span><span className="font-mono text-text-primary">0–4</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">H6 Form input type</span><span className="font-mono text-text-primary">0–4</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">H8 Minimalist design</span><span className="font-mono text-text-primary">0–4</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">H9 Error messages</span><span className="font-mono text-text-primary">0–4</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">H10 Focus indicator</span><span className="font-mono text-text-primary">0–4</span></div>
                  </div>
                  <div className="text-xs text-neutral mt-4">Mean → normalised to 0–100</div>
                </div>

                {/* WCAG 2.2 */}
                <div className="bg-dark-bg border-2 border-cyan-700 rounded-lg p-6">
                  <div className="bg-cyan-900 text-cyan-300 font-semibold px-3 py-1 rounded-full inline-block mb-4 text-sm">40% weight — highest priority</div>
                  <h4 className="font-bold text-cyan-400 mb-4">WCAG 2.2</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-text-secondary">Axe-core violations</span><span className="font-mono text-text-primary">0–100</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">Alt text ratio</span><span className="font-mono text-text-primary">0–100</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">ARIA landmarks</span><span className="font-mono text-text-primary">0–100</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">Contrast (Tailwind)</span><span className="font-mono text-text-primary">0–100</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">html lang attribute</span><span className="font-mono text-text-primary">0/100</span></div>
                  </div>
                  <div className="text-xs text-neutral mt-4">axa×0.50 + alt×0.20 + landmark×0.15 + contrast×0.10 + lang×0.05</div>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-xl font-bold text-primary mb-4">Progressive Thresholds</h3>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-gray-900 text-white">
                      <th className="border border-gray-700 px-4 py-2 text-left">Iteration</th>
                      <th className="border border-gray-700 px-4 py-2 text-left">Target Threshold</th>
                      <th className="border border-gray-700 px-4 py-2 text-left">Action If Below</th>
                      <th className="border border-gray-700 px-4 py-2 text-left">Stop Condition</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="hover:bg-dark-hover">
                      <td className="border border-gray-300 px-4 py-3 font-semibold">1</td>
                      <td className="border border-gray-300 px-4 py-3"><span className="bg-red-100 text-red-800 px-2 py-1 rounded">≥ 65%</span></td>
                      <td className="border border-gray-300 px-4 py-3">Generate targeted refinement prompt</td>
                      <td className="border border-gray-300 px-4 py-3">—</td>
                    </tr>
                    <tr className="hover:bg-dark-hover">
                      <td className="border border-gray-300 px-4 py-3 font-semibold">2</td>
                      <td className="border border-gray-300 px-4 py-3"><span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded">≥ 75%</span></td>
                      <td className="border border-gray-300 px-4 py-3">Regenerate improved schema + re-evaluate</td>
                      <td className="border border-gray-300 px-4 py-3">—</td>
                    </tr>
                    <tr className="hover:bg-dark-hover">
                      <td className="border border-gray-300 px-4 py-3 font-semibold">3</td>
                      <td className="border border-gray-300 px-4 py-3"><span className="bg-green-100 text-green-800 px-2 py-1 rounded">≥ 85%</span></td>
                      <td className="border border-gray-300 px-4 py-3">Continue refinement</td>
                      <td className="border border-gray-300 px-4 py-3">Score ≥ 85% OR 5 iterations completed</td>
                    </tr>
                    <tr className="hover:bg-dark-hover">
                      <td className="border border-gray-300 px-4 py-3 font-semibold">4</td>
                      <td className="border border-gray-300 px-4 py-3"><span className="bg-green-100 text-green-800 px-2 py-1 rounded">≥ 85%</span></td>
                      <td className="border border-gray-300 px-4 py-3">Maintain threshold</td>
                      <td className="border border-gray-300 px-4 py-3">—</td>
                    </tr>
                    <tr className="hover:bg-dark-hover">
                      <td className="border border-gray-300 px-4 py-3 font-semibold">5</td>
                      <td className="border border-gray-300 px-4 py-3"><span className="bg-green-100 text-green-800 px-2 py-1 rounded">≥ 85%</span></td>
                      <td className="border border-gray-300 px-4 py-3">Final evaluation</td>
                      <td className="border border-gray-300 px-4 py-3">End of pipeline</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Novelties Tab */}
        {activeTab === 'novelties' && (
          <div className="space-y-8">
            <h2 className="text-2xl font-bold text-primary mb-6">Your Three Core Novelties</h2>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Novelty 1 */}
              <div className="bg-dark-bg border-2 border-blue-700 rounded-lg p-6">
                <span className="inline-block bg-blue-900 text-blue-300 px-3 py-1 rounded-full text-sm font-semibold mb-3">NOVELTY 1</span>
                <h3 className="text-xl font-bold text-blue-400 mb-3">Standards-integrated multi-criteria rubric</h3>
                <p className="text-text-secondary mb-4">A single quantitative scoring model that simultaneously applies ISO 9241 (30%), Nielsen's 10 heuristics (30%), and WCAG 2.2 POUR (40%) — weighted and combined into one 0–100 composite score per iteration.</p>
                <div className="bg-dark-bg p-3 rounded text-sm text-text-secondary border-l-4 border-blue-500">
                  <strong className="text-text-primary">Why existing tools don't cover it:</strong> No existing tool integrates all three internationally recognised frameworks without evaluation or iterative feedback loop refinement and measurable convergence.
                </div>
              </div>

              {/* Novelty 2 */}
              <div className="bg-dark-bg border-2 border-green-700 rounded-lg p-6">
                <span className="inline-block bg-green-900 text-green-300 px-3 py-1 rounded-full text-sm font-semibold mb-3">NOVELTY 2</span>
                <h3 className="text-xl font-bold text-green-400 mb-3">Threshold-driven convergence loop</h3>
                <p className="text-text-secondary mb-4">An automated iterative controller that progressively raises the pass threshold (65% → 75% → 85%) across up to 5 iterations, generating targeted LLM refinement prompts citing specific rubric violations until convergence is reached.</p>
                <div className="bg-dark-bg p-3 rounded text-sm text-text-secondary border-l-4 border-green-500">
                  <strong className="text-text-primary">Why existing tools don't cover it:</strong> All reviewed tools operate as one-shot systems. None applies progressive threshold escalation with automated feedback-loop refinement and measurable convergence.
                </div>
              </div>

              {/* Novelty 3 */}
              <div className="bg-dark-bg border-2 border-purple-700 rounded-lg p-6">
                <span className="inline-block bg-purple-900 text-purple-300 px-3 py-1 rounded-full text-sm font-semibold mb-3">NOVELTY 3</span>
                <h3 className="text-xl font-bold text-purple-400 mb-3">Full requirements-to-UI traceability</h3>
                <p className="text-text-secondary mb-4">End-to-end traceability matrix linking input FRs/NFRs and use cases through individual UI elements in the final prototype, alongside per-iteration convergence reports with score breakdowns per standard.</p>
                <div className="bg-dark-bg p-3 rounded text-sm text-text-secondary border-l-4 border-purple-500">
                  <strong className="text-text-primary">Why existing tools don't cover it:</strong> Existing tools provide no traceable connection between structured requirements and generated output elements. The traceability gap is explicitly identified in HCI literature as an open research problem.
                </div>
              </div>

              {/* Supporting Mechanism */}
              <div className="bg-dark-bg border-2 border-orange-700 rounded-lg p-6">
                <span className="inline-block bg-orange-900 text-orange-300 px-3 py-1 rounded-full text-sm font-semibold mb-3">SUPPORTING MECHANISM</span>
                <h3 className="text-xl font-bold text-orange-400 mb-3">Static HTML evaluation engine</h3>
                <p className="text-text-secondary mb-4">A zero-configuration Python evaluation engine using BeautifulSoup structural analysis + Axe-core, that produces consistent composite scores (±5%) for the same UI input across runs — no prior training or calibration required.</p>
                <div className="bg-dark-bg p-3 rounded text-sm text-text-secondary border-l-4 border-orange-500">
                  <strong className="text-text-primary">Architecture:</strong> Functional Python pipeline with LangChain for LLM inference (Groq API). No agentic graph orchestration (LangGraph). Direct function composition for planning → generation → evaluation workflow.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Research Gaps Tab */}
        {activeTab === 'gaps' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-primary mb-6">Research Gap Addressed</h2>

            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="bg-dark-bg border-b border-dark-hover">
                    <th className="border border-dark-hover px-4 py-3 text-left text-text-primary font-bold">Existing Approach</th>
                    <th className="border border-dark-hover px-4 py-3 text-left text-text-primary font-bold">Why It Fails</th>
                    <th className="border border-dark-hover px-4 py-3 text-left text-text-primary font-bold">What The System Addresses</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="hover:bg-dark-hover transition">
                    <td className="border border-dark-hover px-4 py-3 font-semibold text-text-primary">Uizard, Galileo AI, Figma AI</td>
                    <td className="border border-dark-hover px-4 py-3"><span className="text-red-400">No evaluation or iterative refinement — cannot guarantee usability compliance</span></td>
                    <td className="border border-dark-hover px-4 py-3"><span className="text-green-400">Iterative threshold-based loop converging to ≥85% composite score</span></td>
                  </tr>
                  <tr className="hover:bg-dark-hover transition">
                    <td className="border border-dark-hover px-4 py-3 font-semibold text-text-primary">GPT-4o critique, UICrit</td>
                    <td className="border border-dark-hover px-4 py-3"><span className="text-red-400">Qualitative feedback only — no quantitative scoring, moderate cross-run consistency</span></td>
                    <td className="border border-dark-hover px-4 py-3"><span className="text-green-400">Weighted rubric (ISO 30%, Nielsen 30%, WCAG 40%) producing a 0–100 numeric score</span></td>
                  </tr>
                  <tr className="hover:bg-dark-hover transition">
                    <td className="border border-dark-hover px-4 py-3 font-semibold text-text-primary">A11YN, Axe DevTools, WAVE</td>
                    <td className="border border-dark-hover px-4 py-3"><span className="text-red-400">Single-standard evaluation — ignores ISO 9241 effectiveness/efficiency and Nielsen heuristics</span></td>
                    <td className="border border-dark-hover px-4 py-3"><span className="text-green-400">Unified multi-standard rubric integrating three internationally recognised frameworks</span></td>
                  </tr>
                  <tr className="hover:bg-dark-hover transition">
                    <td className="border border-dark-hover px-4 py-3 font-semibold text-text-primary">Cursor, GitHub Copilot</td>
                    <td className="border border-dark-hover px-4 py-3"><span className="text-red-400">No usability scoring or accessibility verification — code assistance only</span></td>
                    <td className="border border-dark-hover px-4 py-3"><span className="text-green-400">Full pipeline: requirements → UI generation → evaluation → refinement → traceability report</span></td>
                  </tr>
                  <tr className="hover:bg-dark-hover transition">
                    <td className="border border-dark-hover px-4 py-3 font-semibold text-text-primary">Z-score, baseline calibration</td>
                    <td className="border border-dark-hover px-4 py-3"><span className="text-red-400">Requires historical calibration — impractical in dynamic development environments</span></td>
                    <td className="border border-dark-hover px-4 py-3"><span className="text-green-400">Zero-configuration agent — evaluates any UI immediately with no prior training data</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}