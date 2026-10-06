import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HomePage from "./page";


describe("HomePage", () => {
  it("introduces the BhoomiSetu role portal", () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", {
        name: "Connecting Land, Records & People.",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Get started" })).toHaveAttribute("href", "/login");
    expect(screen.getByText(/Demonstration cases and ML training histories are synthetic/)).toBeInTheDocument();
  });
});
