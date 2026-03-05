import * as fs from "fs";
import { parseMarkdown } from "./parseMarkdown";

const args = process.argv.slice(2);
let filePath = "";

const fileIndex = args.indexOf("-f");
if (fileIndex !== -1 && args[fileIndex + 1]) {
  filePath = args[fileIndex + 1];
} else {
  console.error("Usage: node dist/debugMarkdown.js -f <markdown.md>");
  process.exit(1);
}
if (!fs.existsSync(filePath)) {
  console.error(`Error: File not found : ${filePath}`);
  process.exit(1);
}

const markdown = fs.readFileSync(filePath, "utf8");

const tokens = parseMarkdown(markdown);

console.group("Markdown Debug Result");
console.log("tokens:");
console.table(tokens);
console.groupEnd();
