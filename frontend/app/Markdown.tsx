"use client";

import React from "react";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { parseMarkdown } from "./parseMarkdown";

type Props = { markdown: string };

const Markdown: React.FC<Props> = ({ markdown }) => {
  const tokens = React.useMemo(() => parseMarkdown(markdown), [markdown]);

  return (
    <ScrollArea className="max-h-[80vh] w-full space-y-4">
      {tokens.map((t, i) => {
        switch (t.type) {
          case "heading":
            const Tag = `h${t.level}` as keyof React.JSX.IntrinsicElements;
            const sizeClass =
              t.level === 1
                ? "text-md-h1"
                : t.level === 2
                ? "text-md-h2"
                : t.level === 3
                ? "text-md-h3"
                : t.level === 4
                ? "text-md-h4"
                : t.level === 5
                ? "text-md-h5"
                : "text-md-h6";
            return (
              <Tag key={i} className={`${sizeClass} font-bold my-2`}>
                {t.content}
              </Tag>
            );
          case "code":
            return (
              <ScrollArea
                key={i}
                className="flex flex-nowrap overflow-x-auto bg-slate-800 rounded-sm text-slate-200"
              >
                <pre className="p-3 text-md-code">
                  <div className="flex-none w-10">
                    <code>{t.content}</code>
                  </div>
                  <ScrollBar orientation="horizontal" />
                </pre>
              </ScrollArea>
            );
          case "ul":
            return (
              <ul
                key={i}
                className="list-disc pl-6 space-y-1 text-md-ul my-2"
              >
                {t.items.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            );
          case "ol":
            return (
              <ol
                key={i}
                className="list-decimal pl-6 space-y-1 text-md-ol my-2"
              >
                {t.items.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ol>
            );
          case "p":
            return (
              <p key={i} className="whitespace-pre-wrap text-md-body">
                {t.content}
              </p>
            );
        }
      })}
      <ScrollBar orientation="horizontal" />
    </ScrollArea>
  );
};

export default Markdown;
