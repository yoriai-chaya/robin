const noImgElementRule = {
  meta: {
    type: "problem",
    docs: {
      description:
        "Do not use <img>. Use Next.js <Image> instead for optimized images.",
    },
    schema: [],
    messages: {
      noImg: "Avoid using <img>. Please use <Image> from 'next/image'.",
    },
  },
  create(context) {
    return {
      JSXOpeningElement(node) {
        if (node.name?.name === "img") {
          context.report({
            node,
            messageId: "noImg",
          });
        }
      },
    };
  },
};

export default noImgElementRule;
