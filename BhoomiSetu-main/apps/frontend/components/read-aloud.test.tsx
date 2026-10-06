import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useLocale } from "@/lib/i18n";
import { ReadAloud } from "./read-aloud";

const speech = { cancel: vi.fn(), speak: vi.fn(), getVoices: vi.fn() };

beforeEach(() => {
  useLocale.persist.setOptions({
    storage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
  });
  useLocale.setState({ locale: "en" });
  vi.stubGlobal("speechSynthesis", speech);
  vi.stubGlobal(
    "SpeechSynthesisUtterance",
    class {
      constructor(public text: string) {}
    },
  );
  speech.getVoices.mockReturnValue([{ lang: "en-IN", name: "Test voice" }]);
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

describe("citizen read-aloud", () => {
  it("speaks the actual status and allows stopping", () => {
    render(<ReadAloud text="Case BS-123. Current stage: Verification." />);
    fireEvent.click(screen.getByRole("button", { name: "Read aloud" }));
    expect(speech.speak.mock.calls[0][0]).toMatchObject({
      text: "Case BS-123. Current stage: Verification.",
      lang: "en-IN",
    });
    fireEvent.click(screen.getByRole("button", { name: "Stop reading" }));
    expect(
      screen.getByRole("button", { name: "Read aloud" }),
    ).toBeInTheDocument();
  });
  it("reports missing voices instead of pretending to speak", () => {
    speech.getVoices.mockReturnValue([]);
    render(<ReadAloud text="Current stage: Verification." />);
    fireEvent.click(screen.getByRole("button", { name: "Read aloud" }));
    expect(speech.speak).not.toHaveBeenCalled();
    expect(screen.getByRole("status")).toHaveTextContent(
      /No voice for this language is installed/i,
    );
  });
  it("cancels speech when the selected language changes", () => {
    render(<ReadAloud text="Current stage: Verification." />);
    fireEvent.click(screen.getByRole("button", { name: "Read aloud" }));
    speech.cancel.mockClear();
    act(() => useLocale.setState({ locale: "hi" }));
    expect(speech.cancel).toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "सुनें" })).toBeInTheDocument();
  });
});
