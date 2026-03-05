const noTestidOnSelectRule = {
  meta: {
    type: "problem",
    docs: {
      description:
        "Do not assign data-testid to <Select>. Assign data-testid to <SelectTrigger>, not to <Select>.",
    },
    schema: [],
    messages: {
      noTestidOnSelect:
        "Avoid adding 'data-testid' to <Select>. Please assign it to <SelectTrigger> instead.",
    },
  },
  create(context) {
    return {
      JSXOpeningElement(node) {
        if (node.name?.name === "Select") {
          const hasDataTestId = node.attributes.some(
            (attr) =>
              attr.type === "JSXAttribute" && attr.name?.name === "data-testid"
          );

          if (hasDataTestId) {
            context.report({
              node,
              messageId: "noTestidOnSelect",
            });
          }
        }
      },
    };
  },
};

export default noTestidOnSelectRule;
