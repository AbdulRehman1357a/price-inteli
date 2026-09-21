// A price tag with an upward trend line — pricing + intelligence/analytics.
// Colors are chosen for contrast against the AppBar's primary-blue
// background (theme.js) rather than reusing primary/secondary directly,
// since the tag itself needs to read clearly against that background.
export default function Logo({ size = 32 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Pricing Intelligent Platform logo"
    >
      <path d="M20 3 L37 20 L20 37 L3 20 Z" fill="#ffffff" />
      <circle cx="14" cy="14" r="2.8" fill="#1565c0" />
      <polyline
        points="10,28 16,22 20,25 29,13.5"
        fill="none"
        stroke="#ffb300"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M29,13.5 L22.8,14.8 L26.4,19.7 Z" fill="#ffb300" />
    </svg>
  );
}
