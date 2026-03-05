import { State, Action, ChatStep } from "./types";
import { initialState } from "./state";

export const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case "RESET":
      return structuredClone(initialState);

    case "LOAD_FILE":
      return {
        steps: state.steps.map((step, i) =>
          i === action.index ? { ...step, status: "Loaded" } : step
        ),
      };

    case "SEND_PROMPT":
      return {
        steps: state.steps.map((step, i) =>
          i === action.index ? { ...step, status: "Sended" } : step
        ),
      };

    case "DONE":
      const updatedSteps = state.steps.map<ChatStep>((step, i) =>
        i === action.index ? { ...step, status: "Done" } : step
      );
      if (action.index === state.steps.length - 1) {
        return {
          steps: [...updatedSteps, { status: "Unloaded" }],
        };
      }
      return { steps: updatedSteps };

    default:
      return state;
  }
};
