"use client";

import type { QuestionItem } from "@/types";

interface QuestionRendererProps {
  question: QuestionItem;
  answer: Record<string, unknown> | undefined;
  onAnswer: (answer: Record<string, unknown>) => void;
  questionNumber: number;
  copyPasteBlocked: boolean;
}

export default function QuestionRenderer({
  question,
  answer,
  onAnswer,
  questionNumber,
  copyPasteBlocked,
}: QuestionRendererProps) {
  const blockHandlers: {
    onCopy?: (e: React.ClipboardEvent) => void;
    onPaste?: (e: React.ClipboardEvent) => void;
    onCut?: (e: React.ClipboardEvent) => void;
  } = copyPasteBlocked
    ? {
        onCopy: (e: React.ClipboardEvent) => e.preventDefault(),
        onPaste: (e: React.ClipboardEvent) => e.preventDefault(),
        onCut: (e: React.ClipboardEvent) => e.preventDefault(),
      }
    : {};

  return (
    <div
      className="rounded-lg border p-6"
      style={{
        backgroundColor: "var(--card)",
        borderColor: "var(--border-light)",
      }}
    >
      <div className="flex items-start gap-3 mb-4">
        <span
          className="inline-flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold flex-shrink-0"
          style={{
            backgroundColor: "var(--accent-light)",
            color: "var(--accent)",
          }}
        >
          {questionNumber}
        </span>
        <p
          className="whitespace-pre-wrap leading-relaxed"
          style={{ color: "var(--text-primary)" }}
          {...blockHandlers}
        >
          {question.stem}
        </p>
      </div>

      <div className="mt-4 ml-10">
        {question.question_type === "mcq" && question.options && (
          <MCQInput
            options={question.options}
            selected={(answer as { key?: string })?.key}
            onSelect={(key) => onAnswer({ key })}
          />
        )}

        {question.question_type === "true_false" && (
          <TrueFalseInput
            selected={(answer as { value?: boolean })?.value}
            onSelect={(value) => onAnswer({ value })}
          />
        )}

        {question.question_type === "numeric" && (
          <NumericInput
            value={(answer as { value?: number })?.value}
            onValue={(value) => onAnswer({ value })}
            blockHandlers={blockHandlers}
          />
        )}

        {question.question_type === "short_answer" && (
          <TextInput
            value={(answer as { text?: string })?.text ?? ""}
            onChange={(text) => onAnswer({ text })}
            rows={3}
            placeholder="Kisa cevabnizi yazin"
            blockHandlers={blockHandlers}
          />
        )}

        {question.question_type === "long_form" && (
          <TextInput
            value={(answer as { text?: string })?.text ?? ""}
            onChange={(text) => onAnswer({ text })}
            rows={10}
            placeholder="Detayli cevabnizi yazin"
            blockHandlers={blockHandlers}
          />
        )}
      </div>
    </div>
  );
}

// --- Sub-components ---

function MCQInput({
  options,
  selected,
  onSelect,
}: {
  options: Array<{ key: string; text: string }>;
  selected: string | undefined;
  onSelect: (key: string) => void;
}) {
  return (
    <div className="space-y-2">
      {options.map((opt) => (
        <button
          key={opt.key}
          onClick={() => onSelect(opt.key)}
          className="w-full text-left rounded-md border px-4 py-3 text-sm transition-colors"
          style={
            selected === opt.key
              ? {
                  borderColor: "var(--accent)",
                  backgroundColor: "var(--accent-light)",
                  color: "var(--accent)",
                }
              : {
                  borderColor: "var(--border-light)",
                  backgroundColor: "var(--card)",
                  color: "var(--text-secondary)",
                }
          }
        >
          <span className="font-medium">{opt.key})</span> {opt.text}
        </button>
      ))}
    </div>
  );
}

function TrueFalseInput({
  selected,
  onSelect,
}: {
  selected: boolean | undefined;
  onSelect: (value: boolean) => void;
}) {
  return (
    <div className="flex gap-4">
      {([true, false] as const).map((val) => (
        <button
          key={String(val)}
          onClick={() => onSelect(val)}
          className="flex-1 rounded-md border px-4 py-3 text-sm font-medium transition-colors"
          style={
            selected === val
              ? {
                  borderColor: "var(--accent)",
                  backgroundColor: "var(--accent-light)",
                  color: "var(--accent)",
                }
              : {
                  borderColor: "var(--border-light)",
                  backgroundColor: "var(--card)",
                  color: "var(--text-secondary)",
                }
          }
        >
          {val ? "Dogru" : "Yanlis"}
        </button>
      ))}
    </div>
  );
}

function NumericInput({
  value,
  onValue,
  blockHandlers,
}: {
  value: number | undefined;
  onValue: (v: number) => void;
  blockHandlers: {
    onCopy?: (e: React.ClipboardEvent) => void;
    onPaste?: (e: React.ClipboardEvent) => void;
    onCut?: (e: React.ClipboardEvent) => void;
  };
}) {
  return (
    <input
      type="number"
      step="any"
      placeholder="Cevabnizi girin"
      defaultValue={value ?? ""}
      onBlur={(e) => {
        const v = parseFloat(e.target.value);
        if (!isNaN(v)) onValue(v);
      }}
      className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-1"
      style={{
        borderColor: "var(--input-border)",
        backgroundColor: "var(--card)",
        color: "var(--text-primary)",
      }}
      onFocus={(e) => {
        e.currentTarget.style.borderColor = "var(--input-focus)";
        e.currentTarget.style.boxShadow =
          "0 0 0 1px var(--input-focus)";
      }}
      onBlur={(e) => {
        e.currentTarget.style.borderColor = "var(--input-border)";
        e.currentTarget.style.boxShadow = "none";
        const v = parseFloat(e.target.value);
        if (!isNaN(v)) onValue(v);
      }}
      {...blockHandlers}
    />
  );
}

function TextInput({
  value,
  onChange,
  rows,
  placeholder,
  blockHandlers,
}: {
  value: string;
  onChange: (text: string) => void;
  rows: number;
  placeholder: string;
  blockHandlers: {
    onCopy?: (e: React.ClipboardEvent) => void;
    onPaste?: (e: React.ClipboardEvent) => void;
    onCut?: (e: React.ClipboardEvent) => void;
  };
}) {
  return (
    <textarea
      rows={rows}
      placeholder={placeholder}
      defaultValue={value}
      onBlur={(e) => onChange(e.target.value)}
      className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-1"
      style={{
        borderColor: "var(--input-border)",
        backgroundColor: "var(--card)",
        color: "var(--text-primary)",
      }}
      onFocus={(e) => {
        e.currentTarget.style.borderColor = "var(--input-focus)";
        e.currentTarget.style.boxShadow =
          "0 0 0 1px var(--input-focus)";
      }}
      {...blockHandlers}
    />
  );
}
