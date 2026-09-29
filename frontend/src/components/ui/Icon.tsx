import type { SVGProps } from "react";

export type IconName =
  | "activity"
  | "bell"
  | "calendar"
  | "check"
  | "chevronRight"
  | "clipboard"
  | "clock"
  | "file"
  | "filter"
  | "heartPulse"
  | "home"
  | "log"
  | "menu"
  | "patient"
  | "search"
  | "shield"
  | "sparkles"
  | "users"
  | "x";

const paths: Record<IconName, string[]> = {
  activity: ["M3 12h4l2-7 4 14 2-7h6"],
  bell: ["M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9", "M10 21h4"],
  calendar: ["M7 3v4", "M17 3v4", "M4 9h16", "M5 5h14a1 1 0 0 1 1 1v14H4V6a1 1 0 0 1 1-1Z"],
  check: ["M5 12l4 4L19 6"],
  chevronRight: ["M9 18l6-6-6-6"],
  clipboard: ["M9 5h6", "M8 3h8a1 1 0 0 1 1 1v17H7V4a1 1 0 0 1 1-1Z", "M9 9h6", "M9 13h6", "M9 17h4"],
  clock: ["M12 7v5l3 2", "M20 12a8 8 0 1 1-16 0 8 8 0 0 1 16 0Z"],
  file: ["M6 3h8l4 4v14H6z", "M14 3v5h5", "M9 13h6", "M9 17h6"],
  filter: ["M4 5h16", "M7 12h10", "M10 19h4"],
  heartPulse: ["M3 12h4l2-4 4 8 2-4h6", "M12 21a9.1 9.1 0 0 0 9-9 9.1 9.1 0 0 0-9-9 9.1 9.1 0 0 0-9 9 9.1 9.1 0 0 0 9 9Z"],
  home: ["M3 11l9-7 9 7", "M5 10v10h14V10", "M10 20v-6h4v6"],
  log: ["M5 4h14v16H5z", "M8 8h8", "M8 12h8", "M8 16h5"],
  menu: ["M4 7h16", "M4 12h16", "M4 17h16"],
  patient: ["M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8", "M4 21a8 8 0 0 1 16 0"],
  search: ["M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16Z", "M21 21l-4.35-4.35"],
  shield: ["M12 3l7 3v5c0 4.8-2.9 8.5-7 10-4.1-1.5-7-5.2-7-10V6z", "M9 12l2 2 4-4"],
  sparkles: ["M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5z", "M19 15l.7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7z"],
  users: ["M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2", "M9.5 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8", "M21 21v-2a4 4 0 0 0-3-3.87", "M16 3.13a4 4 0 0 1 0 7.75"],
  x: ["M6 6l12 12", "M18 6L6 18"],
};

export default function Icon({ name, size = 18, strokeWidth = 1.9, ...props }: { name: IconName; size?: number; strokeWidth?: number } & Omit<SVGProps<SVGSVGElement>, "name">) {
  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {paths[name].map((d, index) => (
        <path key={index} d={d} />
      ))}
    </svg>
  );
}
