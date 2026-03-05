import { Card } from "@/components/ui/card";
import {
  ResponseEvent,
  ResponseInfo,
  EventTypes,
  StreamResponse,
  BuildErrorAnalyzerPayload,
} from "./types";
import Image from "next/image";
import Markdown from "./Markdown";

const confidenceColorMap: Record<
  BuildErrorAnalyzerPayload["confidence"],
  string
> = {
  probable: "text-ctm-blue-500",
  likely: "text-ctm-green-500",
  possible: "text-ctm-yellow-200",
  unclear: "text-ctm-orange-400",
};

interface StreamDetailProps {
  status: string;
  responseInfo: ResponseInfo;
}

// Type Guard Function
function isCodeEvent(
  event: StreamResponse,
): event is Extract<StreamResponse, { event: typeof EventTypes.CODE }> {
  return event.event === EventTypes.CODE;
}
function isUpdateEvent(
  event: StreamResponse,
): event is Extract<StreamResponse, { event: typeof EventTypes.AGENT_UPDATE }> {
  return event.event === EventTypes.AGENT_UPDATE;
}
function isCheckResultEvent(
  event: StreamResponse,
): event is Extract<StreamResponse, { event: typeof EventTypes.CHECK_RESULT }> {
  return event.event === EventTypes.CHECK_RESULT;
}
function isAgentResultEvent(
  event: StreamResponse,
): event is Extract<StreamResponse, { event: typeof EventTypes.AGENT_RESULT }> {
  return event.event === EventTypes.AGENT_RESULT;
}
function isTestResultEvent(
  event: StreamResponse,
): event is Extract<StreamResponse, { event: typeof EventTypes.TEST_RESULT }> {
  return event.event === EventTypes.TEST_RESULT;
}
function isDoneEvent(
  event: StreamResponse,
): event is Extract<StreamResponse, { event: typeof EventTypes.DONE }> {
  return event.event === EventTypes.DONE;
}
function isSystemErrorEvent(
  event: StreamResponse,
): event is Extract<StreamResponse, { event: typeof EventTypes.SYSTEM_ERROR }> {
  return event.event === EventTypes.SYSTEM_ERROR;
}
function isTestScreenshotEvent(
  event: StreamResponse,
): event is Extract<
  StreamResponse,
  { event: typeof EventTypes.TEST_SCREENSHOT }
> {
  return event.event === EventTypes.TEST_SCREENSHOT;
}
function isAnalyzerResultEvent(
  event: StreamResponse,
): event is Extract<
  StreamResponse,
  { event: typeof EventTypes.ANALYZER_RESULT }
> {
  return event.event === EventTypes.ANALYZER_RESULT;
}

// StreamDetail Function
const StreamDetail = ({ status, responseInfo }: StreamDetailProps) => {
  const events = responseInfo?.r_event ?? [];
  return (
    <div>
      {(status === "Sended" || status === "Done") && (
        <div>
          <p className="text-app-info my-1 font-semibold">Response</p>
          {events.map((ev: ResponseEvent, idx: number) => {
            const sr = ev.s_res;
            // ----- agent_update event -----
            if (isUpdateEvent(sr)) {
              const agentName = sr.payload.agent_name;
              return (
                <div key={`agent_update-${idx}`}>
                  <div className="text-app-detail font-semibold">
                    {agentName}
                  </div>
                </div>
              );
            }

            // ----- code event -----
            if (isCodeEvent(sr)) {
              const code = `\`\`\`${sr.payload.language}\n${sr.payload.code}\n\`\`\``;
              const filePath = sr.payload.file_path;
              return (
                <div key={`code-${idx}`}>
                  <div className="text-app-detail pl-2">
                    Filepath: {filePath}
                  </div>
                  <Card className="my-2 p-1 bg-gray-200 rounded-sm shadow-md">
                    <div className="flex overflow-x-auto">
                      <Markdown markdown={code} />
                    </div>
                  </Card>
                </div>
              );
            }
            // ----- check_result event -----
            if (isCheckResultEvent(sr)) {
              const { checker, result, rule_id, detail } = sr.payload;
              const resultStr = result ? "OK" : "Error";

              return (
                <div key={`check-${idx}`} className="pl-2 text-app-detail">
                  <div>
                    <span className="font-semibold">{checker} check: </span>
                    <span
                      className={`font-semibold ${
                        result ? "text-ctm-blue-500" : "text-ctm-orange-400"
                      }`}
                    >
                      {resultStr}
                    </span>
                  </div>

                  {!result && (
                    <div className="pl-4">
                      <div>
                        <span className="font-semibold">rule: </span>
                        <span className="text-muted-foreground">{rule_id}</span>
                      </div>
                      <div className="break-all">
                        <span className="font-semibold">detail: </span>
                        <span className="text-muted-foreground">{detail}</span>
                      </div>
                    </div>
                  )}
                </div>
              );
            }

            // ----- agent_result event -----
            if (isAgentResultEvent(sr)) {
              const result = sr.payload.result;
              const resultStr = result ? "OK" : "Error";
              const error_detail = sr.payload.error_detail;
              return (
                <div key={`agent-result-${idx}`}>
                  <span className="text-app-detail pl-2">
                    {result ? (
                      <>
                        <span>result: </span>
                        <span className="text-ctm-blue-500">{resultStr}</span>
                      </>
                    ) : (
                      <>
                        <span>result: </span>
                        <span className="text-ctm-orange-400">{resultStr}</span>
                        <div className="text-app-detail pl-4 break-all">
                          detail: {error_detail}
                        </div>
                      </>
                    )}
                  </span>
                </div>
              );
            }

            // ----- test_result event -----
            if (isTestResultEvent(sr)) {
              const payload = sr.payload;
              const { result, detail, name, file, total, ok, ng, specs } =
                payload;
              const resultStr = result ? "OK" : "Error";
              return (
                <div key={`test-result-${idx}`}>
                  <span className="text-app-detail pl-2">
                    check:{" "}
                    {result ? (
                      <>
                        <span className="text-ctm-blue-500">{resultStr}</span>
                      </>
                    ) : (
                      <>
                        <span className="text-ctm-orange-400">{resultStr}</span>
                      </>
                    )}
                    <div className="text-app-detail pl-4">
                      <span>
                        Total:{total}, OK:{ok}, NG:{ng}
                      </span>
                      <div>Name: {name}</div>
                      <div>File: {file}</div>
                      <div className="break-all">Error detail: {detail}</div>
                      {specs && specs.length > 0 && (
                        <div className="mt-1">
                          <div className="font-semibold">Test Specs:</div>
                          <ul className="pl-4 list-disc">
                            {specs.map((spec, sIdx) => (
                              <li
                                key={`spec-${idx}-${sIdx}`}
                                className="text-app-detail"
                              >
                                <div>
                                  <span>Title:</span>
                                  {spec.title}
                                </div>
                                <div>
                                  Result:{" "}
                                  {spec.result ? (
                                    <span className="text-ctm-blue-500">
                                      OK
                                    </span>
                                  ) : (
                                    <span className="text-ctm-orange-400">
                                      NG
                                    </span>
                                  )}
                                </div>
                                {!spec.result && (
                                  <div className="pl-4 text-ctm-orange-400">
                                    {spec.error_summary && (
                                      <div>Summary: {spec.error_summary}</div>
                                    )}
                                    {spec.error_message && (
                                      <div>Message: {spec.error_message}</div>
                                    )}
                                  </div>
                                )}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </span>
                </div>
              );
            }

            // ----- test_screenshot event -----
            if (isTestScreenshotEvent(sr)) {
              const { spec, filename, url, updated } = sr.payload;
              const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;
              const api_url = API_BASE + url;
              console.log(`api_url: ${api_url}`);
              return (
                <div key={`screenshot-${idx}`} className="pl-4 mt-2">
                  <div className="text-app-detail text-muted-foreground">
                    <div>
                      Screenshot: spec={spec}, filename={filename}, updated=
                      {updated ? "true" : "false"}
                    </div>
                  </div>
                  <a
                    href={api_url}
                    target="_blank"
                    className="inline-block mt-1"
                  >
                    <Image
                      src={api_url}
                      alt={filename}
                      width={300}
                      height={300}
                      className="mt-1 border rounded max-w-full"
                    />
                  </a>
                </div>
              );
            }

            // ----- analyzer_result event -----
            if (isAnalyzerResultEvent(sr)) {
              const {
                summary,
                root_cause,
                files_to_fix,
                fix_policy,
                confidence,
              } = sr.payload;
              const colorClass = confidenceColorMap[confidence];
              return (
                <div key={`analyzer-${idx}`}>
                  <div className="pl-4">
                    <div></div>
                    <div className="text-app-detail text-muted-foreground">
                      <div>
                        <span className="font-semibold text-foreground">
                          Summary:
                        </span>{" "}
                        {summary}
                      </div>
                      <div>
                        <span className="font-semibold text-foreground">
                          Root cause:
                        </span>{" "}
                        {root_cause}
                      </div>
                      <div>
                        <span className="font-semibold text-foreground">
                          Files to fix:
                        </span>
                        <ul className="list-disc list-inside ml-2">
                          {files_to_fix.map((f) => (
                            <li key={f}>{f}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <span className="font-semibold text-foreground">
                          Fix policy:
                        </span>
                        <ul className="list-disc list-inside ml-2">
                          {fix_policy.map((p, i) => (
                            <li key={i}>{p}</li>
                          ))}
                        </ul>
                      </div>
                      <pre className="font-semibold text-foreground">
                        confidence:{" "}
                        <span className={colorClass}>{confidence}</span>
                      </pre>
                    </div>
                  </div>
                </div>
              );
            }

            // ----- done event -----
            if (isDoneEvent(sr)) {
              const status = sr.payload.status;
              const message = sr.payload.message;
              return (
                <div key={`done-${idx}`}>
                  <div className="text-app-detail font-semibold">Done</div>
                  <div className="text-app-detail pl-2">
                    <div>
                      <span className="font-semibold text-foreground">
                        status:{" "}
                      </span>
                      <span
                        className={
                          status === "Failed"
                            ? "text-ctm-orange-400"
                            : "text-foreground"
                        }
                      >
                        {status}
                      </span>
                    </div>
                    <div>
                      <span className="font-semibold text-foreground">
                        message:{" "}
                      </span>
                      <span>{message}</span>
                    </div>
                  </div>
                </div>
              );
            }

            // ----- system-error event -----
            if (isSystemErrorEvent(sr)) {
              const error = sr.payload.error;
              const detail = sr.payload.detail;
              return (
                <div key={`system-error-${idx}`}>
                  <div className="text-ctm-orange-400 text-app-detail pl-2 break-all">
                    <div>{error}</div>
                    <div>{detail}</div>
                  </div>
                </div>
              );
            }
          })}
        </div>
      )}
    </div>
  );
};

export default StreamDetail;
