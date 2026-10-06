import Link from "next/link";
export function Brand() {
  return (
    <Link className="brand" href="/" aria-label="BhoomiSetu home">
      <span className="brandMark" aria-hidden>
        भू
      </span>
      <span>
        BhoomiSetu<small>भूमि से विश्वास तक</small>
      </span>
    </Link>
  );
}
