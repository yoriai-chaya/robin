export type ChatStep = { status: "Unloaded" | "Loaded" | "Sended" | "Done" };
export type State = { steps: ChatStep[] };
export type Action =
  | { type: "LOAD_FILE"; index: number }
  | { type: "SEND_PROMPT"; index: number }
  | { type: "DONE"; index: number }
  | { type: "RESET" };
export type FileInfo = {
  filename: string;
  content: string;
  mtime: Date;
};
export type PromptRequest = {
  prompt: string;
};
export type PromptResponse = {
  prompt: string;
};

export type CheckResultPayload = {
  checker: string;
  result: boolean;
  rule_id: string;
  detail: string;
};

export type TestResultSpec = {
  title: string;
  result: boolean;
  error_summary: string | null;
  error_message: string | null;
  error_stack: string | null;
};

export type TestResultPayload = {
  name: string;
  file: string;
  result: boolean;
  detail: string;
  total: number;
  ok: number;
  ng: number;
  specs: TestResultSpec[];
};

export type TestScreenshotPayload = {
  spec: string;
  filename: string;
  url: string;
  updated: boolean;
};

export type BuildErrorAnalyzerPayload = {
  summary: string;
  root_cause: string;
  files_to_fix: string[];
  fix_policy: string[];
  confidence: "probable" | "likely" | "possible" | "unclear";
};

export type StreamResponse =
  | {
      event: "started";
      payload: { status: string; message: string; step_id: string };
    }
  | {
      event: "code";
      payload: { language: string; code: string; file_path: string };
    }
  | { event: "agent_update"; payload: { agent_name: string } }
  | { event: "done"; payload: { status: string; message: string } }
  | { event: "check_result"; payload: CheckResultPayload }
  | { event: "system_error"; payload: { error: string; detail: string } }
  | {
      event: "agent_result";
      payload: { result: boolean; error_detail: string };
    }
  | { event: "test_result"; payload: TestResultPayload }
  | { event: "test_screenshot"; payload: TestScreenshotPayload }
  | {
      event: "analyzer_result";
      payload: BuildErrorAnalyzerPayload;
    };

export type ResponseEvent = {
  s_res: StreamResponse;
  r_time: Date;
};

export type ResponseInfo = {
  r_event: ResponseEvent[];
};

export const EventTypes = {
  STARTED: "started",
  CODE: "code",
  AGENT_UPDATE: "agent_update",
  DONE: "done",
  CHECK_RESULT: "check_result",
  SYSTEM_ERROR: "system_error",
  AGENT_RESULT: "agent_result",
  TEST_RUN: "test_run",
  TEST_RESULT: "test_result",
  TEST_SCREENSHOT: "test_screenshot",
  ANALYZER_RESULT: "analyzer_result",
} as const;

export type CheckResultEvent = {
  event: "check_result";
  payload: CheckResultPayload;
};

export type CheckResultItem = {
  s_res: CheckResultEvent;
  r_time: Date;
};

export type Mode = "Manual" | "Auto";

export type AutoRunFilelist = {
  name: string;
  content: string;
  mtime: string; // ISO8601
};

export type FileNode = {
  type: "file";
  name: string;
  data: AutoRunFilelist;
};
export type DirectoryNode = {
  type: "directory";
  name: string;
  children: TreeNode[];
};
export type TreeNode = FileNode | DirectoryNode;

export type AutoRunFileStatus =
  | "pending"
  | "running"
  | "success"
  | "failed"
  | "skipped";

export type AutoRunFileStatusMap = Record<string, AutoRunFileStatus>;

export type AutoRunState = "idle" | "running" | "pause" | "finished" | "failed";

export enum Emoji {
  WHITE_CIRCLE = "\u26AA", // ⚪
  RED_CIRCLE = "\u{1F534}", // 🔴
  BLUE_CIRCLE = "\u{1F535}", // 🔵
  GREEN_CIRCLE = "\u{1F7E2}", // 🟢
  YELLOW_CIRCLE = "\u{1F7E1}", // 🟡
}

export enum ResponseStatus {
  COMPLETED = "Completed",
  FAILED = "Failed",
}
