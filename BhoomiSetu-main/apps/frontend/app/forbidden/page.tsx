import Link from "next/link";
import { ShieldX } from "lucide-react";

export default function ForbiddenPage() {
  return <main className="errorPage"><ShieldX /><p className="sectionLabel">403 · Role protected</p><h1>This workspace belongs to a different role.</h1><p>BhoomiSetu keeps citizen, officer and administrative information separated by design.</p><Link className="button primary" href="/login">Return to sign in</Link></main>;
}
