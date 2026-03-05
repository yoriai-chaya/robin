import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import readline from "node:readline";
import process from "node:process";
import stripAnsi from "strip-ansi";
import { createRequire } from "node:module";

/**
 * Parse a CLI argument in either from:
 *   --name=value
 */
function getArg(name) {
  const ix = process.argv.findIndex(
    (a) => a === `--${name}` || a.startsWith(`--${name}=`),
  );
  if (ix === -1) return undefined;
  const val = process.argv[ix].split("=")[1] ?? process.argv[ix + 1];
  return val;
}

/**
 * Convert a Date to a compact timestamp string: YYYYMMDD_hhmmss
 */
function formatTimestamp(date) {
  const pad = (n) => n.toString().padStart(2, "0");
  const YYYY = date.getFullYear();
  const MM = pad(date.getMonth() + 1);
  const DD = pad(date.getDate());
  const hh = pad(date.getHours());
  const mm = pad(date.getMinutes());
  const ss = pad(date.getSeconds());
  return `${YYYY}${MM}${DD}_${hh}${mm}${ss}`;
}

// --- Resolve project root and log output directory/file ---
const projectRoot = process.cwd();
const customLogsDir = getArg("logs-dir");
console.log(`customLogsDir: ${customLogsDir}`);

const logsDir = path.resolve(projectRoot, customLogsDir ?? "logs");
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

// --- Optional config file to override the output log filename ---
const customConfigPath = path.join(projectRoot, "build.customconfig.json");
let logFileName = "build.json"; // default filename

if (fs.existsSync(customConfigPath)) {
  try {
    const raw = fs.readFileSync(customConfigPath, "utf8");
    const customConfig = JSON.parse(raw);

    if (typeof customConfig.build_report_file === "string") {
      logFileName = customConfig.build_report_file;
      console.log(`Using custom log file: ${logFileName}`);
    } else {
      console.log(
        "Warning: 'build_report_file' is missing or not a string in build.customconfig.json",
      );
    }
  } catch (err) {
    console.log(
      `Warnig: Failed to read or parse build.customconfig.json: ${err.message}`,
    );
  }
} else {
  console.log("No build.customconfig.json found. Using default build.json");
}

const logPath = path.join(logsDir, logFileName);

// --- Structures to store build output and summary ---
const records = [];
const summary = { errorCount: 0, warnCount: 0, infoCount: 0 };
const startTime = formatTimestamp(new Date());

// --- Path to Next.js CLI entrypoint installed in node_modules
function resolveNextBin(cwd) {
  const requireFromCwd = createRequire(path.join(cwd, "package.json"));
  return requireFromCwd.resolve("next/dist/bin/next");
}
let nextBin;
try {
  nextBin = resolveNextBin(projectRoot);
} catch (e) {
  console.error(`[error] Failed to resolve Next.js CLI. ${e?.message ?? e}`);
  process.exit(1);
}

// --- Run `next build --turbopack` as a child process ---

/**
 * spawn() starts a new process (child process)
 * Here we run: node <nextBin> build --turbopack
 * - stdout/stderr are piped so we can read and process logs line-by-line.
 */
const child = spawn(process.execPath, [nextBin, "build", "--turbopack"], {
  cwd: projectRoot,
  env: { ...process.env },
  stdio: ["ignore", "pipe", "pipe"],
  shell: false,
});

// --- Decide log level from each line ---
// Notes:
//   / ... / : The beginning and end of a regular expression
//   \b      : Word boundary
//   (..| ..): Parentheses ( ) create a group in the regular expression.
//             Inside the group, the vartical bar | acts as an alternation
//             operator, meaning "match any one of these options"
//   i       : Case insensitive. It means that uppercase and lowercase letters
//             are treated as the same.
const LEVEL_PATTERNS = {
  error: [
    /\b(error|errors|fatal|uncaught|unhandled)\b/i,
    /\bfailed\b/i,
    /\bexception\b/i,
  ],
  warn: [/\bwarn(ing)?\b/i, /\bdeprecated\b/i],
};

function inferLevel(message, streamName) {
  const msg = message ?? "";
  // --- If it Looks like an error, treat as error even if from stdout ---
  if (LEVEL_PATTERNS.error.some((re) => re.test(msg))) return "error";
  if (LEVEL_PATTERNS.warn.some((re) => re.test(msg))) return "warn";

  // --- Any stderr output is treated as an error unless it matches a warning ---
  if (streamName === "stderr") return "error";

  // --- Otherwise, treat as info
  return "info";
}

// --- Wire child stdout/stderr into line-based processing ---
/**
 * createInterface() turns a readable stream into a line-based reader.
 * rl.on("line") fires for every newline-terminated line.
 */
const wire = (stream, name) => {
  const rl = readline.createInterface({ input: stream });
  rl.on("line", (line) => {
    // --- Remove ANSI escape codes (colors etc.) for clean JSON Logs
    const clean = stripAnsi(line ?? "");

    // --- Infer Log Level and update counters
    const level = inferLevel(clean, name);
    if (level === "error") summary.errorCount += 1;
    else if (level === "warn") summary.warnCount += 1;
    else summary.infoCount += 1;

    // --- Store the line for the final JSON report
    records.push({ stream: name, message: clean });

    // --- Print to console with a simple prefix for errors/warnings
    const prefix =
      level === "error" ? "[error]" : level === "warn" ? "[warn]" : "";
    process.stdout.write(prefix + clean + "\n");
  });
};

wire(child.stdout, "stdout");
wire(child.stderr, "stderr");

// --- On completion: write JSON report and exit with some status code ---
const t0 = Date.now();

/**
 * child.on("close") fires when the child has exited and stdio streams are closed.
 * We write a JSON report and exit with the child's exit code.
 */
child.on("close", (code) => {
  const endTime = formatTimestamp(new Date());
  const durationMs = Date.now() - t0;
  const result = {
    tool: "next-build",
    args: ["build", "--turbopack"],
    startTime,
    endTime,
    durationMs,
    exitCode: typeof code === "number" ? code : null,
    records,
    summary,
  };
  fs.writeFileSync(logPath, JSON.stringify(result, null, 2), "utf8");
  process.stdout.write(`Saved: ${logPath}\n`);
  process.exit(typeof code === "number" ? code : 1);
});

// --- If spawning fails (e.g., command not found), exit as failure
child.on("error", (err) => {
  console.error(`[error] Failed to spawn next build: ${err?.message ?? err}`);
  process.exit(1);
});
