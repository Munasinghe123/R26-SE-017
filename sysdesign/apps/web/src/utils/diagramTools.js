/**
 * diagramTools.js — deterministic helpers for the Architecture Review diagram studio.
 *
 * - generateMermaid:  hardened Mermaid generator (safe unique IDs, escaped labels,
 *                     every connector endpoint guaranteed to exist as a node).
 * - lcsDiff:          real LCS line diff (git-style) between any two diagram versions.
 * - renderMermaidSvg: client-side Mermaid rendering (no third-party network call).
 */

const cleanText = (s) =>
  String(s ?? "")
    .replace(/["'`<>\[\]{}()|#;\\]/g, "")
    .replace(/\s+/g, " ")
    .trim();

const baseId = (s) => {
  const id = String(s ?? "").replace(/[^a-zA-Z0-9]/g, "_").replace(/_+/g, "_").replace(/^_|_$/g, "");
  return id || "x";
};

/** Build a unique, Mermaid-safe identifier ("n_" prefix avoids reserved words such as `end`). */
function uniqueId(prefix, raw, used) {
  let id = `${prefix}_${baseId(raw)}`;
  let i = 2;
  while (used.has(id)) id = `${prefix}_${baseId(raw)}_${i++}`;
  used.add(id);
  return id;
}

const connEnds = (c) => ({
  from: (c.from_component || c.from || c.source || "").toString().trim(),
  to: (c.to_component || c.to || c.target || "").toString().trim(),
  label: cleanText(c.connector_type || c.type || c.protocol || ""),
});

export function generateMermaid(architecture) {
  if (!architecture) return "flowchart TD\n    n_empty[\"No architecture selected\"]";

  const comps = (architecture.components || []).filter((c) => (c.name || "").trim());
  const conns =
    (architecture.connectors?.length ? architecture.connectors : null) ||
    (architecture.interactions?.length ? architecture.interactions : null) ||
    [];

  const used = new Set();
  const nodeIdByName = new Map();
  const groups = new Map(); // lower(layer) -> { title, nodes: [] }

  comps.forEach((c) => {
    const name = c.name.trim();
    if (nodeIdByName.has(name)) return;
    const id = uniqueId("n", name, used);
    nodeIdByName.set(name, id);
    const layerRaw = (c.layer || c.boundary || "Core").toString().trim() || "Core";
    const key = layerRaw.toLowerCase();
    if (!groups.has(key)) groups.set(key, { title: cleanText(layerRaw) || "Core", nodes: [] });
    groups.get(key).nodes.push({ id, label: cleanText(name) || id });
  });

  const lines = ["flowchart TD"];
  groups.forEach((g, key) => {
    const gid = uniqueId("g", key, used);
    lines.push(`    subgraph ${gid}["${g.title}"]`);
    g.nodes.forEach((n) => lines.push(`        ${n.id}["${n.label}"]`));
    lines.push("    end");
  });

  // Connector endpoints that don't match a declared component still get a node.
  const ensureNode = (name) => {
    if (nodeIdByName.has(name)) return nodeIdByName.get(name);
    const id = uniqueId("n", name, used);
    nodeIdByName.set(name, id);
    lines.push(`    ${id}["${cleanText(name) || id}"]`);
    return id;
  };

  const seen = new Set();
  conns.forEach((c) => {
    const { from, to, label } = connEnds(c);
    if (!from || !to || from === to) return;
    const a = ensureNode(from);
    const b = ensureNode(to);
    const isAsync = /async|event|message|queue|publish|subscribe/i.test(label);
    const key = `${a}>${b}>${label}`;
    if (seen.has(key)) return;
    seen.add(key);
    const arrow = isAsync ? (label ? `-. ${label} .->` : "-.->") : label ? `-->|${label}|` : "-->";
    lines.push(`    ${a} ${arrow} ${b}`);
  });

  return lines.join("\n");
}

/** Normalise code coming from JSON ("\\n" literals) into real newlines. */
export function normalizeCode(code) {
  return String(code || "").replace(/\\n/g, "\n").replace(/\r\n/g, "\n");
}

/** True when text is plausible PlantUML source. */
export function looksLikePlantUML(code) {
  if (!code || typeof code !== "string") return false;
  const t = code.trim();
  if (t.startsWith("{") || t.startsWith("[")) return false;
  const low = t.toLowerCase();
  return low.includes("@startuml") && low.includes("@enduml");
}

/**
 * Git-style line diff using a longest-common-subsequence table.
 * Returns [{ type: "same" | "add" | "del", text, oldNo, newNo }].
 */
export function lcsDiff(oldText, newText) {
  const a = normalizeCode(oldText).split("\n");
  const b = normalizeCode(newText).split("\n");
  const n = a.length;
  const m = b.length;

  const dp = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }

  const out = [];
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (a[i] === b[j]) {
      out.push({ type: "same", text: a[i], oldNo: i + 1, newNo: j + 1 });
      i++;
      j++;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      out.push({ type: "del", text: a[i], oldNo: i + 1, newNo: null });
      i++;
    } else {
      out.push({ type: "add", text: b[j], oldNo: null, newNo: j + 1 });
      j++;
    }
  }
  while (i < n) {
    out.push({ type: "del", text: a[i], oldNo: i + 1, newNo: null });
    i++;
  }
  while (j < m) {
    out.push({ type: "add", text: b[j], oldNo: null, newNo: j + 1 });
    j++;
  }
  return out;
}

export function diffStats(diff) {
  return diff.reduce(
    (acc, d) => {
      if (d.type === "add") acc.added++;
      else if (d.type === "del") acc.removed++;
      return acc;
    },
    { added: 0, removed: 0 }
  );
}

let mermaidPromise = null;
async function getMermaid() {
  if (!mermaidPromise) {
    mermaidPromise = import("mermaid").then((mod) => {
      const mermaid = mod.default;
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "strict",
        theme: "dark",
        flowchart: { htmlLabels: false, curve: "basis" },
      });
      return mermaid;
    });
  }
  return mermaidPromise;
}

/** Validate Mermaid syntax locally. Returns null when valid, otherwise an error message. */
export async function validateMermaid(code) {
  try {
    const mermaid = await getMermaid();
    await mermaid.parse(code);
    return null;
  } catch (e) {
    return String(e?.message || e);
  }
}

let renderCounter = 0;
/** Render Mermaid code to an SVG string entirely in the browser. */
export async function renderMermaidSvg(code) {
  const mermaid = await getMermaid();
  const { svg } = await mermaid.render(`mmd-render-${Date.now()}-${renderCounter++}`, code);
  return svg;
}
