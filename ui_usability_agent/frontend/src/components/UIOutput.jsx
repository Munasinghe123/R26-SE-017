export default function UIOutput({ generatedUI }) {
  return (
    <div className="bg-dark-card p-6 rounded-lg shadow-md border border-dark-hover">
      <h2 className="text-xl font-semibold mb-4 text-primary">Generated UI</h2>
      <div className="border border-dark-hover rounded-md h-72 overflow-hidden bg-dark-bg">
        {generatedUI ? (
          <iframe
            title="Generated UI Preview"
            className="w-full h-full"
            srcDoc={generatedUI}
            sandbox="allow-scripts allow-same-origin"
          />
        ) : (
          <p className="text-text-secondary p-4">No UI generated yet</p>
        )}
      </div>
    </div>
  );
}