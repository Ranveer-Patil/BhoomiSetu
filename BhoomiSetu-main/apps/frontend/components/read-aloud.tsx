"use client";
import { useEffect, useState } from "react";
import { Square, Volume2 } from "lucide-react";
import { useLocale, useT } from "@/lib/i18n";

export function ReadAloud({ text }: { text: string }) {
  const locale = useLocale((state) => state.locale);
  return <Reader key={`${locale}:${text}`} text={text} />;
}

function Reader({ text }: { text: string }) {
  const locale = useLocale((state) => state.locale);
  const t = useT();
  const [speaking, setSpeaking] = useState(false);
  const [message, setMessage] = useState("");
  useEffect(
    () => () => {
      window.speechSynthesis?.cancel();
    },
    [text, locale],
  );
  function read() {
    if (!("speechSynthesis" in window)) {
      setMessage(t("voiceUnavailable"));
      return;
    }
    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }
    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find(
      (candidate) => candidate.lang.split("-")[0] === locale,
    );
    if (!voice) {
      setMessage(t("voiceUnavailable"));
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = voice.lang;
    utterance.voice = voice;
    utterance.rate = 0.9;
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => {
      setSpeaking(false);
      setMessage(t("voiceUnavailable"));
    };
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    setSpeaking(true);
    setMessage("");
  }
  return (
    <div className="readAloud">
      <button className="button secondary small" onClick={read}>
        {speaking ? <Square size={15} /> : <Volume2 size={15} />}
        {t(speaking ? "stopReading" : "readAloud")}
      </button>
      <small role="status">{message || t("voiceNote")}</small>
    </div>
  );
}
