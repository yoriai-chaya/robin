import {
  ResponseInfo,
  EventTypes,
  StreamResponse,
  Emoji,
  ResponseEvent,
  ResponseStatus,
  BuildErrorAnalyzerPayload,
} from "./types";
import { formatDateTime } from "./util";

const confidenceColorMap: Record<
  BuildErrorAnalyzerPayload["confidence"],
  string
> = {
  probable: "text-ctm-blue-500",
  likely: "text-ctm-green-500",
  possible: "text-ctm-yellow-200",
  unclear: "text-ctm-orange-400",
};

interface StreamEventProps {
  status: string;
  responseInfo: ResponseInfo;
}

// Type Guard Function
function isStartedEvent(
  event: StreamResponse,
): event is Extract<StreamResponse, { event: typeof EventTypes.STARTED }> {
  return event.event === EventTypes.STARTED;
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

// StreamEvent Function
const StreamEvent = ({ status, responseInfo }: StreamEventProps) => {
  const events = responseInfo?.r_event ?? [];

  return (
    <div>
      {(status === "Sended" || status === "Done") && (
        <div>
          {events.map((ev: ResponseEvent, idx: number) => {
            const sr = ev.s_res;
            // ----- started event -----
            if (isStartedEvent(sr)) {
              const emoji = Emoji.BLUE_CIRCLE;
              return (
                <div key={`started-${idx}`}>
                  <div className="grid grid-cols-6 items-center">
                    {/* first row*/}
                    <div></div>
                    <div className="col-span-3 text-app-agent">
                      <span className="text-app-emoji pr-2">{emoji}</span>
                      {sr.payload.status}
                    </div>
                    <div className="col-span-2 text-app-time text-muted-foreground">
                      {formatDateTime(ev.r_time)}
                    </div>
                    {/* second row*/}
                    <div></div>
                    <div className="col-span-5 text-app-info ml-5">
                      <span>{sr.payload.step_id}</span>
                    </div>
                  </div>
                </div>
              );
            }

            // ----- agent_update event -----
            if (isUpdateEvent(sr)) {
              const emoji = Emoji.GREEN_CIRCLE;
              const agentName = sr.payload.agent_name;
              return (
                <div key={`agent-${idx}`}>
                  <div className="grid grid-cols-6 items-center">
                    <div></div>
                    <div className="col-span-3 text-app-agent">
                      <span className="text-app-emoji pr-2">{emoji}</span>
                      {agentName}
                    </div>
                    <div className="col-span-2 text-app-time text-muted-foreground">
                      {formatDateTime(ev.r_time)}
                    </div>
                  </div>
                </div>
              );
            }

            // ----- check_result event -----
            if (isCheckResultEvent(sr)) {
              const result = sr.payload.result;
              const resultStr = result ? "OK" : "Error";
              const rule_id = sr.payload.rule_id;
              return (
                <div key={`check-${idx}`}>
                  <div className="grid grid-cols-6 items-center">
                    <div></div>
                    <div className="col-span-3 text-app-info ml-5">
                      <span>
                        {sr.payload.checker} check:{" "}
                        {result ? (
                          <span className="text-ctm-blue-500">{resultStr}</span>
                        ) : (
                          <span className="text-ctm-orange-400">
                            {resultStr}
                          </span>
                        )}
                      </span>
                    </div>
                    <div className="col-span-2 text-app-time text-muted-foreground">
                      {formatDateTime(ev.r_time)}
                    </div>
                  </div>
                  <div className="grid grid-cols-6 items-center">
                    <div></div>
                    <div className="col-span-5 text-app-detail ml-9 text-muted-foreground">
                      {rule_id}
                    </div>
                  </div>
                </div>
              );
            }

            // ----- agent_result event -----
            if (isAgentResultEvent(sr)) {
              const result = sr.payload.result;
              const resultStr = result ? "OK" : "Error";
              return (
                <div key={`agent-result-${idx}`}>
                  <div className="grid grid-cols-6 items-center">
                    <div></div>
                    <div className="col-span-3 text-app-info ml-5">
                      result:{" "}
                      {result ? (
                        <span className="text-ctm-blue-500">{resultStr}</span>
                      ) : (
                        <span className="text-ctm-orange-400">{resultStr}</span>
                      )}
                    </div>
                    <div className="col-span-2 text-app-time text-muted-foreground">
                      {formatDateTime(ev.r_time)}
                    </div>
                  </div>
                </div>
              );
            }

            // ----- test_result event -----
            if (isTestResultEvent(sr)) {
              const payload = sr.payload;
              const { result, total, ok, ng } = payload;
              const resultStr = result ? "OK" : "Error";
              return (
                <div key={`test-result-${idx}`}>
                  <div className="grid grid-cols-6 items-center">
                    <div></div>
                    <div className="col-span-3 text-app-info ml-5">
                      result:{" "}
                      {result ? (
                        <span className="text-ctm-blue-500">{resultStr}</span>
                      ) : (
                        <span className="text-ctm-orange-400">{resultStr}</span>
                      )}
                    </div>
                    <div className="col-span-2 text-app-time text-muted-foreground">
                      {formatDateTime(ev.r_time)}
                    </div>
                  </div>
                  <div className="grid grid-cols-6 items-center">
                    <div></div>
                    <div className="col-span-5 text-app-detail ml-9 text-muted-foreground">
                      <pre>
                        Total: {total} OK: {ok} NG: {ng}
                      </pre>
                    </div>
                  </div>
                </div>
              );
            }

            // ----- test_screenshot event -----
            if (isTestScreenshotEvent(sr)) {
              const { filename, updated } = sr.payload;
              if (!updated) {
                return null;
              }
              return (
                <div key={`screenshot-${idx}`}>
                  <div className="grid grid-cols-6 items-center">
                    <div></div>
                    <div className="col-span-5 text-app-detail ml-9 text-muted-foreground">
                      <pre>{filename} created</pre>
                    </div>
                  </div>
                </div>
              );
            }

            // ----- analyzer_result event -----
            if (isAnalyzerResultEvent(sr)) {
              const { confidence } = sr.payload;
              const colorClass = confidenceColorMap[confidence];
              return (
                <div key={`analyzer-${idx}`}>
                  <div className="grid grid-cols-6 items-center">
                    <div></div>
                    <div className="col-span-5 text-app-detail ml-9 text-muted-foreground">
                      <pre>
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
              let emoji = Emoji.BLUE_CIRCLE;
              if (sr.payload.status === ResponseStatus.FAILED) {
                emoji = Emoji.RED_CIRCLE;
              }
              return (
                <div key={`done-${idx}`}>
                  <div className="grid grid-cols-6 items-center">
                    <div></div>
                    <div className="col-span-3 text-app-agent">
                      <span className="text-app-emoji pr-2">{emoji}</span>
                      {sr.payload.status}
                    </div>
                    <div className="col-span-2 text-app-time text-muted-foreground">
                      {formatDateTime(ev.r_time)}
                    </div>
                  </div>
                </div>
              );
            }
            // ----- system-error event -----
            if (isSystemErrorEvent(sr)) {
              const error = sr.payload.error;
              return (
                <div key={`system-error-${idx}`}>
                  <div className="grid grid-cols-6 items-center">
                    <div></div>
                    <div className="col-span-3 text-app-info ml-5">
                      <span className="text-ctm-orange-400">{error}</span>
                    </div>
                    <div className="col-span-2 text-app-time text-muted-foreground">
                      {formatDateTime(ev.r_time)}
                    </div>
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

export default StreamEvent;
