"use client";

import { useMemo } from "react";
import katex from "katex";

export interface MathTextProps {
  content: string;
  className?: string;
}

/**
 * Safely parses markdown/math strings containing $...$ (inline) or $$...$$ (block)
 * and renders KaTeX mathematical expressions safely.
 */
export function MathText({ content, className = "" }: MathTextProps) {
  const renderedElements = useMemo(() => {
    if (!content) return null;

    // Split by $$...$$ first, then $...$
    const parts: { type: "text" | "inline-math" | "block-math"; value: string }[] = [];

    // Regex for block $$...$$ or inline $...$
    const mathRegex = /(\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$)/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = mathRegex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        parts.push({
          type: "text",
          value: content.slice(lastIndex, match.index),
        });
      }

      const matchStr = match[0];
      if (matchStr.startsWith("$$") && matchStr.endsWith("$$")) {
        parts.push({
          type: "block-math",
          value: matchStr.slice(2, -2).trim(),
        });
      } else if (matchStr.startsWith("$") && matchStr.endsWith("$")) {
        parts.push({
          type: "inline-math",
          value: matchStr.slice(1, -1).trim(),
        });
      }

      lastIndex = match.index + matchStr.length;
    }

    if (lastIndex < content.length) {
      parts.push({
        type: "text",
        value: content.slice(lastIndex),
      });
    }

    return parts.map((part, index) => {
      if (part.type === "block-math") {
        try {
          const html = katex.renderToString(part.value, {
            displayMode: true,
            throwOnError: false,
          });
          return (
            <span
              key={index}
              className="block my-2 text-center overflow-x-auto"
              dangerouslySetInnerHTML={{ __html: html }}
            />
          );
        } catch {
          return <span key={index}>{part.value}</span>;
        }
      }

      if (part.type === "inline-math") {
        try {
          const html = katex.renderToString(part.value, {
            displayMode: false,
            throwOnError: false,
          });
          return (
            <span
              key={index}
              className="inline-block px-0.5 align-baseline"
              dangerouslySetInnerHTML={{ __html: html }}
            />
          );
        } catch {
          return <span key={index}>{part.value}</span>;
        }
      }

      // Plain text with line breaks preserved
      return (
        <span key={index} className="whitespace-pre-wrap">
          {part.value}
        </span>
      );
    });
  }, [content]);

  return <div className={`leading-relaxed ${className}`}>{renderedElements}</div>;
}
