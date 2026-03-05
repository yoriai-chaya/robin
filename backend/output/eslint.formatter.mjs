export default function (results, context) {
  return JSON.stringify(
    results.map((result) => ({
      filePath: result.filePath,
      messages: result.messages.map((msg) => ({
        ruleId: msg.ruleId,
        severity: msg.severity,
        message: msg.message,
        messageId: msg.messageId,
        cwd: context.cwd,
        rulesMeta: context.rulesMeta,
      })),
    })),
    null,
    2
  );
}
