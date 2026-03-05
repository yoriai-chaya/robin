export type Token =
  | { type: "heading"; level: number; content: string }
  | { type: "code"; content: string; lang?: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] }
  | { type: "p"; content: string };

export const parseMarkdown = (markdown: string): Token[] => {
  const lines = markdown.split("\n");
  const tokens: Token[] = [];

  let codeMode = false;
  let codeLang = "";
  let codeBuffer: string[] = [];

  let listBuffer: string[] = [];
  let listType: "ul" | "ol" | null = null;

  const flushList = () => {
    if (listType && listBuffer.length > 0) {
      tokens.push({ type: listType, items: listBuffer });
      listBuffer = [];
      listType = null;
    }
  };

  for (let line of lines) {
    line = line.trimEnd();
    console.log(`line: ${line}`);

    // start or end of a code block
    if (line.startsWith("```")) {
      if (!codeMode) {
        codeMode = true;
        codeLang = line.slice(3).trim();
        codeBuffer = [];
      } else {
        codeMode = false;
        tokens.push({
          type: "code",
          content: codeBuffer.join("\n"),
          lang: codeLang,
        });
      }
      continue;
    }

    if (codeMode) {
      codeBuffer.push(line);
      continue;
    }

    // heading(h1-h6) (#, ##, ###, ####, #####, ######)
    const headingMatch = line.match(/^(#{1,6})\s+(.*)/);
    if (headingMatch) {
      flushList();
      const level = headingMatch[1].length;
      const content = headingMatch[2];
      tokens.push({ type: "heading", level, content });
      continue;
    }

    // ol: ordered list (1. item)
    if (/^\d+\.\s+/.test(line)) {
      const item = line.replace(/^\d+\.\s+/, "");
      if (listType === "ol" || listType === null) {
        listType = "ol";
        listBuffer.push(item);
      } else {
        // previous <ui> is not closed
        flushList();
        listType = "ol";
        listBuffer.push(item);
      }
      continue;
    }

    // unordered list (- item / * item)
    if (/^[-*]\s+/.test(line)) {
      const item = line.replace(/^[-*]\s+/, "");
      if (listType === "ul" || listType === null) {
        listType = "ul";
        listBuffer.push(item);
      } else {
        // previous <ol> is not closed
        flushList();
        listType = "ul";
        listBuffer.push(item);
      }
      continue;
    }

    // empty line -> end of list
    if (line.trim() === "" && listType) {
      flushList();
      continue;
    }

    // paragraph
    flushList();
    tokens.push({ type: "p", content: line });
  }

  // remaining lists or codes, add them to the end
  if (listType) tokens.push({ type: listType, items: listBuffer });
  if (codeMode && codeBuffer.length > 0)
    tokens.push({
      type: "code",
      content: codeBuffer.join("\n"),
      lang: codeLang,
    });

  return tokens;
};
