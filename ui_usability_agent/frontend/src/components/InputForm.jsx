'use client';

import React from 'react';

export default function InputForm({ requirements, onRequirementsChange, onPlan, loading }) {
  const handleFileUpload = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        onRequirementsChange(reader.result);
      }
    };
    reader.readAsText(file);
  };

  const handleSubmit = () => {
    onPlan();
  };

  return (
    <div className="bg-dark-card p-6 rounded-lg shadow-md border border-dark-hover">
      <h2 className="text-xl font-semibold mb-4 text-primary">Input Requirements</h2>
      <textarea
        className="w-full h-40 p-3 bg-dark-bg border border-dark-hover rounded-md text-text-primary focus:outline-none focus:ring-2 focus:ring-primary placeholder-neutral"
        placeholder="Enter JSON requirements..."
        value={requirements}
        onChange={(e) => onRequirementsChange(e.target.value)}
      />
      <label className="block text-sm text-text-secondary mt-3">
        Upload requirements JSON
      </label>
      <input
        type="file"
        accept="application/json"
        onChange={handleFileUpload}
        className="mt-1 block w-full text-sm text-text-secondary"
      />
      <button
        className="mt-4 bg-primary text-black px-6 py-2 rounded-md hover:bg-primary-light transition font-semibold"
        onClick={handleSubmit}
        disabled={loading}
      >
        {loading ? 'Planning...' : 'Run Planning'}
      </button>
    </div>
  );
}