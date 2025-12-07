import React from "react";

interface MarkdownRendererProps {
  content: string;
}

/**
 * Simple Markdown Renderer for Mixer Reports
 * Supports:
 * - Headers: # ## ### (converted to HTML with neon styling)
 * - Bold: **text**
 * - Code blocks: ```
 * - Lists: - and *
 * - Links: [text](url)
 * - Dividers: ---
 */
export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const parseMarkdown = (markdown: string) => {
    const lines = markdown.split("\n");
    const elements: React.ReactNode[] = [];
    let codeBlock = false;
    let codeContent = "";

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Code block
      if (line.startsWith("```")) {
        if (!codeBlock) {
          codeBlock = true;
          codeContent = "";
        } else {
          codeBlock = false;
          elements.push(
            <pre
              key={`code-${i}`}
              className="bg-gray-100 border border-gray-300 rounded p-3 my-2 overflow-x-auto text-xs text-gray-800 font-mono"
            >
              {codeContent}
            </pre>
          );
        }
        continue;
      }

      if (codeBlock) {
        codeContent += line + "\n";
        continue;
      }

      // Skip empty lines
      if (!line.trim()) {
        elements.push(<div key={`empty-${i}`} className="h-1" />);
        continue;
      }

      // Divider
      if (line.startsWith("---")) {
        elements.push(
          <hr key={`divider-${i}`} className="border-gray-300 my-3" />
        );
        continue;
      }

      // Headers
      if (line.startsWith("###")) {
        const title = line.replace(/^#+\s*/, "").replace(/\*/g, "");
        elements.push(
          <h3
            key={`h3-${i}`}
            className="text-sm font-bold text-blue-600 mt-3 mb-2 tracking-widest"
          >
            {title}
          </h3>
        );
        continue;
      }

      if (line.startsWith("##")) {
        const title = line.replace(/^#+\s*/, "").replace(/\*/g, "");
        elements.push(
          <h2
            key={`h2-${i}`}
            className="text-base font-bold text-blue-700 mt-4 mb-2 tracking-widest"
          >
            {title}
          </h2>
        );
        continue;
      }

      if (line.startsWith("#")) {
        const title = line.replace(/^#+\s*/, "").replace(/\*/g, "");
        elements.push(
          <h1
            key={`h1-${i}`}
            className="text-lg font-bold text-blue-800 mt-4 mb-2 tracking-widest"
          >
            {title}
          </h1>
        );
        continue;
      }

      // List items
      if (line.startsWith("- ") || line.startsWith("* ")) {
        const item = line.replace(/^[-*]\s*/, "");
        elements.push(
          <div
            key={`list-${i}`}
            className="text-xs text-gray-700 ml-4 my-1 flex gap-2"
          >
            <span className="text-blue-500 flex-shrink-0">▸</span>
            <span>{parseLineFormatting(item)}</span>
          </div>
        );
        continue;
      }

      // Regular paragraphs
      if (line.trim()) {
        elements.push(
          <p
            key={`p-${i}`}
            className="text-xs text-gray-700 my-1 leading-relaxed"
          >
            {parseLineFormatting(line)}
          </p>
        );
      }
    }

    return elements;
  };

  const parseLineFormatting = (line: string): React.ReactNode => {
    // Split by bold markers and create elements
    const parts = line.split(/(\*\*.*?\*\*)/g);

    return parts.map((part, idx) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        // Bold text
        const text = part.slice(2, -2);
        return (
          <strong key={idx} className="text-blue-600 font-bold">
            {text}
          </strong>
        );
      }
      return <span key={idx}>{part}</span>;
    });
  };

  return (
    <div className="text-xs text-black bg-white p-4 rounded space-y-1">
      {parseMarkdown(content)}
    </div>
  );
}
