// ui_usability_agent/evaluator/axe_runner.js
const { JSDOM } = require('jsdom');
const fs = require('fs');

async function runAxe(htmlString) {
  if (!htmlString || !htmlString.trim()) {
    return { violations: [] };
  }

  try {
    const dom = new JSDOM(htmlString);
    const { window } = dom;

    // Set globals for axe-core
    global.window = window;
    global.document = window.document;

    // Require axe after setting globals
    const axe = require('axe-core');

    // Inject axe-core into the window
    window.eval(axe.source);

    const results = await axe.run();
    
    return {
      violations: results.violations,
      passes: results.passes.length,
      incomplete: results.incomplete.length
    };
  } catch (error) {
    console.error('Axe error:', error.message);
    return { violations: [], error: error.message };
  }
}

// CLI mode for Python
if (require.main === module) {
  const html = fs.readFileSync(process.argv[2], 'utf8');
  runAxe(html).then(result => {
    console.log(JSON.stringify(result));
  });
}

module.exports = { runAxe };