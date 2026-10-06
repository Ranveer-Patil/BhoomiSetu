import {
  ArrowRight,
  CheckCircle2,
  FileSearch,
  GitBranch,
  MapPinned,
  ShieldCheck,
  UploadCloud,
} from "lucide-react";
import Link from "next/link";
import { Brand } from "@/components/brand";
import { LandingPreview } from "@/components/landing-preview";

const journey = [
  "Notification",
  "Verification",
  "Objection",
  "Award",
  "Compensation",
  "Possession",
];
export default function HomePage() {
  return (
    <main className="landing">
      <section className="landingHero" id="top">
        <nav className="landingNav">
          <Brand />
          <div>
            <a href="#platform">The platform</a>
            <a href="#journey">The journey</a>
            <Link className="button light" href="/login">
              Open portal <ArrowRight size={16} />
            </Link>
          </div>
        </nav>
        <div className="heroBody">
          <div className="heroCopy">
            <p className="eyebrow">BhoomiSetu · SIH26016</p>
            <h1>
              Connecting Land,
              <br />
              <em>Records & People.</em>
            </h1>
            <p>
              One shared view of land acquisition—from the first notification to
              compensation and possession.
            </p>
            <div className="heroActions">
              <Link className="button accent" href="/login">
                Get started <ArrowRight size={18} />
              </Link>
              <a href="#platform" className="textLink">
                Explore the platform <ArrowRight size={16} />
              </a>
            </div>
            <div className="heroTrust">
              <span>
                <ShieldCheck size={16} /> Role-specific access
              </span>
              <span>
                <GitBranch size={16} /> Traceable workflow
              </span>
            </div>
          </div>
          <LandingPreview />
        </div>
        <div className="heroBottom">
          <span>भूमि से विश्वास तक</span>
          <span>Land acquisition, made legible.</span>
          <span>01 — A clearer view</span>
        </div>
      </section>
      <section className="landingSection" id="platform">
        <div className="sectionIntro">
          <div>
            <p className="eyebrow">From paper to progress</p>
            <h2>
              A record you can
              <br />
              <em>follow through.</em>
            </h2>
          </div>
          <p>
            Upload a scan. Review the extracted fields. Keep the officer’s
            decision and every stage change attached to the case.
          </p>
        </div>
        <div className="documentShowcase">
          <div className="paperDocument">
            <div className="paperHeader">
              <span>महाराष्ट्र शासन</span>
              <FileSearch size={28} />
            </div>
            <p>ILLUSTRATIVE LAND RECORD</p>
            <h3>Record of Rights</h3>
            <dl>
              <div>
                <dt>Holder</dt>
                <dd>Anita Patil</dd>
              </div>
              <div>
                <dt>Survey</dt>
                <dd>PRR-1001</dd>
              </div>
              <div>
                <dt>District</dt>
                <dd>Pune, Maharashtra</dd>
              </div>
            </dl>
            <div className="paperLines" />
            <small>Synthetic example · no real citizen data</small>
          </div>
          <div className="documentExplanation">
            <p className="eyebrow">Document intelligence</p>
            <h3>
              Read the scan.
              <br />
              Keep the human decision.
            </h3>
            <p>
              OCR extracts fields from PNG, JPEG and TIFF scans. Authorized
              staff review the result before marking a document verified.
            </p>
            <ol>
              {[
                "Upload a document scan",
                "Review extracted information",
                "Confirm or correct the record",
              ].map((item, index) => (
                <li key={item}>
                  <span>0{index + 1}</span>
                  {item}
                  <CheckCircle2 size={18} />
                </li>
              ))}
            </ol>
            <Link href="/login" className="textLink">
              Try the workflow <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>
      <section className="journeySection" id="journey">
        <div className="sectionIntro">
          <div>
            <p className="eyebrow">The acquisition journey</p>
            <h2>
              Six stages.
              <br />
              <em>One responsibility trail.</em>
            </h2>
          </div>
          <p>
            Citizens see the next step. Field officers see their queue.
            Authorities see where a recorded deadline needs attention.
          </p>
        </div>
        <ol className="publicJourney">
          {journey.map((item, index) => (
            <li key={item}>
              <span>0{index + 1}</span>
              <strong>{item}</strong>
            </li>
          ))}
        </ol>
        <p className="helper">
          Workflow support for authorized teams. Statutory decisions remain with
          the responsible authority.
        </p>
      </section>
      <section className="landingSection">
        <div className="sectionIntro">
          <div>
            <p className="eyebrow">Five accountable views</p>
            <h2>
              Different roles.
              <br />
              <em>A connected record.</em>
            </h2>
          </div>
          <p>
            Each workspace puts the relevant cases, tasks and decisions first.
          </p>
        </div>
        <div className="roleEditorial">
          <div>
            <MapPinned size={36} />
            <h3>
              From the family
              <br />
              to the field team.
            </h3>
            <p>
              Case tracking, maps, reporting and a traceable record of action.
            </p>
          </div>
          <ol>
            {[
              [
                "Citizen",
                "Track cases, submit documents and raise grievances.",
              ],
              ["Field Officer", "Review documents and advance assigned cases."],
              [
                "Project Authority",
                "Record compensation, R&R and project deadlines.",
              ],
              [
                "District Administrator",
                "Review progress, exceptions and district reports.",
              ],
              [
                "Senior Administrator",
                "Compare projects and inspect the audit trail.",
              ],
            ].map(([role, task], index) => (
              <li key={role}>
                <span>0{index + 1}</span>
                <strong>{role}</strong>
                <p>{task}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>
      <section className="landingClose">
        <div>
          <p className="eyebrow">A clearer next step</p>
          <h2>
            Make land information
            <br />
            easier to understand.
          </h2>
          <Link href="/login" className="button accent">
            Enter BhoomiSetu <ArrowRight size={18} />
          </Link>
        </div>
        <UploadCloud size={70} strokeWidth={1} />
      </section>
      <footer className="landingFooter">
        <Brand />
        <p>
          SIH prototype. Demonstration cases and ML training histories are
          synthetic. Government adapters return labelled fixtures.
        </p>
        <Link href="/login">Open portal →</Link>
      </footer>
    </main>
  );
}
