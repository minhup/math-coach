import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MathRenderer } from "./math-renderer";

describe("MathRenderer", () => {
  it("renders valid inline mathematics with accessible KaTeX output", async () => {
    render(<MathRenderer label="Pythagorean identity" latex="a^2+b^2=c^2" mode="inline" />);

    const mathematics = await screen.findByLabelText("Pythagorean identity");

    expect(mathematics).toHaveAttribute("data-math-render-state", "rendered");
    expect(mathematics.querySelector(".katex")).not.toBeNull();
    expect(mathematics.querySelector("math")).not.toBeNull();
  });

  it("replaces malformed mathematics with a source-free correctable placeholder", async () => {
    const untrustedSource = String.raw`\frac{PRIVATE_SOURCE}{`;
    const { container } = render(
      <MathRenderer label="Student expression" latex={untrustedSource} mode="display" />,
    );

    expect(await screen.findByRole("img", { name: "Math needs correction" })).toBeInTheDocument();
    expect(container.innerHTML).not.toContain("PRIVATE_SOURCE");
    expect(container.innerHTML).not.toContain("\\frac");
  });

  it("rejects trusted-command attempts without rendering their source or target", async () => {
    const untrustedSource = String.raw`\href{javascript:PRIVATE_TARGET}{PRIVATE_LINK}`;
    const { container } = render(
      <MathRenderer label="Untrusted expression" latex={untrustedSource} mode="inline" />,
    );

    expect(await screen.findByRole("img", { name: "Math needs correction" })).toBeInTheDocument();
    expect(container.innerHTML).not.toContain("PRIVATE_TARGET");
    expect(container.innerHTML).not.toContain("PRIVATE_LINK");
    expect(container.querySelector("a")).toBeNull();
  });

  it.each([
    String.raw`\url{https://PRIVATE_TARGET}`,
    String.raw`\includegraphics{https://PRIVATE_TARGET/image.png}`,
    String.raw`\htmlClass{PRIVATE_CLASS}{x}`,
    String.raw`\htmlId{PRIVATE_ID}{x}`,
    String.raw`\htmlStyle{color:red}{x}`,
    String.raw`\htmlData{private=value}{x}`,
  ])("rejects every trusted KaTeX command family", async (untrustedSource) => {
    const { container } = render(
      <MathRenderer label="Trusted command attempt" latex={untrustedSource} mode="inline" />,
    );

    expect(await screen.findByRole("img", { name: "Math needs correction" })).toBeInTheDocument();
    expect(container.innerHTML).not.toContain("PRIVATE_");
    expect(container.querySelector("a, img, script, iframe")).toBeNull();
  });

  it("treats empty mathematics as correctable instead of rendering an empty formula", async () => {
    render(<MathRenderer label="Empty expression" latex="   " mode="inline" />);

    expect(await screen.findByRole("img", { name: "Math needs correction" })).toBeInTheDocument();
  });

  it("rejects over-length mathematics before it can expand the document", async () => {
    const untrustedSource = "PRIVATE_LONG_SOURCE".repeat(120);
    const { container } = render(
      <MathRenderer label="Long expression" latex={untrustedSource} mode="display" />,
    );

    expect(await screen.findByRole("img", { name: "Math needs correction" })).toBeInTheDocument();
    expect(container.innerHTML).not.toContain("PRIVATE_LONG_SOURCE");
  });

  it("renders the committed mathematical regression corpus", async () => {
    const expressions = [
      String.raw`\frac{1}{2}`,
      String.raw`\frac{1}{1+\frac{1}{x}}`,
      String.raw`x_1^2+x_2^2`,
      String.raw`\sqrt{x+\sqrt{y}}`,
      String.raw`\begin{cases}x+y=3\\x-y=1\end{cases}`,
      String.raw`f(x)=\begin{cases}x^2&x\geq0\\-x&x<0\end{cases}`,
      String.raw`a<b\leq c`,
      String.raw`a\equiv b\pmod n`,
      String.raw`A\cap B=\varnothing`,
      String.raw`P\land Q\implies P`,
      String.raw`\begin{pmatrix}1&2\\3&4\end{pmatrix}`,
      String.raw`\angle ABC=60^\circ`,
      String.raw`\begin{aligned}x+1&=3\\x&=2\end{aligned}`,
    ];

    render(
      <>
        {expressions.map((latex, index) => (
          <MathRenderer
            key={latex}
            label={`Regression expression ${index + 1}`}
            latex={latex}
            mode="display"
          />
        ))}
      </>,
    );

    await waitFor(() =>
      expect(document.querySelectorAll('[data-math-render-state="rendered"]')).toHaveLength(
        expressions.length,
      ),
    );
    expect(screen.queryByRole("img", { name: "Math needs correction" })).toBeNull();
  });

  it("rejects unsupported commands without exposing the source", async () => {
    const untrustedSource = String.raw`\definitelyunsupported{PRIVATE_UNSUPPORTED}`;
    const { container } = render(
      <MathRenderer label="Unsupported expression" latex={untrustedSource} mode="inline" />,
    );

    expect(await screen.findByRole("img", { name: "Math needs correction" })).toBeInTheDocument();
    expect(container.innerHTML).not.toContain("PRIVATE_UNSUPPORTED");
    expect(container.innerHTML).not.toContain("definitelyunsupported");
  });

  it("bounds macro expansion and removes the attempted source", async () => {
    const untrustedSource = String.raw`\def\loop{\loop}\loop PRIVATE_EXPANSION`;
    const { container } = render(
      <MathRenderer label="Expanding expression" latex={untrustedSource} mode="display" />,
    );

    expect(await screen.findByRole("img", { name: "Math needs correction" })).toBeInTheDocument();
    expect(container.innerHTML).not.toContain("PRIVATE_EXPANSION");
  });

  it("caps explicit element sizes at the controlled renderer limit", async () => {
    render(
      <MathRenderer
        label="Bounded oversized expression"
        latex={String.raw`\rule{500em}{500em}`}
        mode="display"
      />,
    );

    const mathematics = await screen.findByLabelText("Bounded oversized expression");
    await waitFor(() => expect(mathematics).toHaveAttribute("data-math-render-state", "rendered"));

    const visualOutput = mathematics.querySelector(".katex-html");
    expect(visualOutput?.innerHTML).not.toContain("500em");
    expect(visualOutput?.innerHTML).toContain("10em");
  });

  it("recovers when a correctable expression becomes valid", async () => {
    const { rerender } = render(
      <MathRenderer label="Corrected expression" latex={String.raw`\frac{1}{`} mode="display" />,
    );
    expect(await screen.findByRole("img", { name: "Math needs correction" })).toBeInTheDocument();

    rerender(<MathRenderer label="Corrected expression" latex="x^2=4" mode="display" />);

    const mathematics = await screen.findByLabelText("Corrected expression");
    await waitFor(() => expect(mathematics).toHaveAttribute("data-math-render-state", "rendered"));
    expect(screen.queryByRole("img", { name: "Math needs correction" })).toBeNull();
  });
});
