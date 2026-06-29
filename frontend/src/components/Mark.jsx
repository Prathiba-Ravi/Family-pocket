// src/components/Mark.jsx
export default function Mark({ size = 32, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" className={className} fill="none">
      <path
        d="M20 3 L35 9 V19 C35 28 29 34 20 37 C11 34 5 28 5 19 V9 Z"
        stroke="currentColor"
        strokeWidth="1.6"
      />
      <path d="M13 20.5 L18 25.5 L27.5 14.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
